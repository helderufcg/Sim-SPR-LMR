"""Apply validated transformations to the layer/analyte table state.

The table stores row metadata, material settings, thicknesses, and refractive
indices in index-aligned collections. This module centralizes add, replace, and
remove operations so every collection represents the same optical-stack order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sim_spr_lmr.core.materials import (
    DRUDE_DISPERSION_MODEL,
    DRUDE_LORENTZ_DISPERSION_MODEL,
    EXPERIMENTAL_DISPERSION_MODEL,
    FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL,
    material_supports_drude_override,
    material_supports_drude_lorentz,
    material_supports_filmetrics_experimental,
    material_uses_builtin_drude,
    normalize_dispersion_model_name,
)


@dataclass(slots=True)
# Keeps all editable layer and analyte collections aligned by row index.
class LayerStateSnapshot:
    """Index-aligned collections that represent the editable optical stack."""

    layers: list[dict[str, str]] = field(default_factory=list)
    material_names: list[str] = field(default_factory=list)
    material_ids: list[int] = field(default_factory=list)
    thicknesses_m: list[float] = field(default_factory=list)
    refractive_indices: list[complex] = field(default_factory=list)
    analyte_indices: list[complex] = field(default_factory=list)


@dataclass(slots=True)
# Represents raw values from the layer-editing form before parsing and validation.
class LayerFormInput:
    """Raw input for creating or editing one optical layer."""

    material_name: str
    material_id: int
    thickness_text: str
    description: str
    interrogation_mode: str
    real_part_text: str = ""
    imaginary_part_text: str = ""
    dispersion_model: str = EXPERIMENTAL_DISPERSION_MODEL
    drude_lambda_p_text: str = ""
    drude_lambda_c_text: str = ""


@dataclass(slots=True)
# Represents raw values from the analyte form before conversion to complex indices.
class AnalyteFormInput:
    """Raw input for creating or editing the analyte layer."""

    thickness_text: str
    description: str
    initial_index: float
    sample_count: int
    step: float


class LayerValidationError(ValueError):
    """Validation error that keeps track of the affected UI fields."""

    def __init__(self, field_names: list[str], message: str = "* Fill in all required fields *") -> None:
        super().__init__(message)
        self.field_names = field_names
        self.message = message


# Validates a layer form and returns a new state with the layer appended.
def append_layer(state: LayerStateSnapshot, form_input: LayerFormInput) -> LayerStateSnapshot:
    """Return a new snapshot with one optical layer appended."""

    layer_payload = _build_layer_payload(form_input)
    return LayerStateSnapshot(
        layers=[*state.layers, layer_payload.table_row],
        material_names=[*state.material_names, layer_payload.material_name],
        material_ids=[*state.material_ids, layer_payload.material_id],
        thicknesses_m=[*state.thicknesses_m, layer_payload.thickness_m],
        refractive_indices=[*state.refractive_indices, layer_payload.refractive_index],
        analyte_indices=list(state.analyte_indices),
    )


# Validates an analyte form and appends its index to the state.
def append_analyte(state: LayerStateSnapshot, form_input: AnalyteFormInput) -> LayerStateSnapshot:
    """Return a new snapshot with the analyte row appended."""

    analyte_payload = _build_analyte_payload(form_input)
    return LayerStateSnapshot(
        layers=[*state.layers, analyte_payload.table_row],
        material_names=[*state.material_names, "Analyte"],
        material_ids=[*state.material_ids, 19],
        thicknesses_m=[*state.thicknesses_m, analyte_payload.thickness_m],
        refractive_indices=[*state.refractive_indices, complex(form_input.initial_index, 0)],
        analyte_indices=analyte_payload.analyte_indices,
    )


# Replaces one existing layer while preserving the stack order.
def replace_layer(
    state: LayerStateSnapshot,
    index: int,
    form_input: LayerFormInput,
) -> LayerStateSnapshot:
    """Replace one non-analyte layer while preserving the rest of the snapshot."""

    _validate_index(state, index)
    layer_payload = _build_layer_payload(form_input)
    updated = clone_state(state)
    updated.layers[index] = layer_payload.table_row
    updated.material_names[index] = layer_payload.material_name
    updated.material_ids[index] = layer_payload.material_id
    updated.thicknesses_m[index] = layer_payload.thickness_m
    updated.refractive_indices[index] = layer_payload.refractive_index
    return updated


# Replaces the analyte entry and its associated refractive-index sweep.
def replace_analyte(
    state: LayerStateSnapshot,
    index: int,
    form_input: AnalyteFormInput,
) -> LayerStateSnapshot:
    """Replace the analyte row and regenerate its refractive-index sweep."""

    _validate_index(state, index)
    analyte_payload = _build_analyte_payload(form_input)
    updated = clone_state(state)
    updated.layers[index] = analyte_payload.table_row
    updated.material_names[index] = "Analyte"
    updated.material_ids[index] = 19
    updated.thicknesses_m[index] = analyte_payload.thickness_m
    updated.refractive_indices[index] = complex(form_input.initial_index, 0)
    updated.analyte_indices = analyte_payload.analyte_indices
    return updated


# Removes one layer and updates every index-aligned collection.
def remove_layer(state: LayerStateSnapshot, index: int) -> LayerStateSnapshot:
    """Remove one row and clear analyte data if the removed row is the analyte."""

    _validate_index(state, index)
    updated = clone_state(state)
    removed_material = updated.material_names[index]
    del updated.layers[index]
    del updated.material_names[index]
    del updated.material_ids[index]
    del updated.thicknesses_m[index]
    del updated.refractive_indices[index]
    if removed_material == "Analyte":
        updated.analyte_indices = []
    return updated


def clone_state(state: LayerStateSnapshot) -> LayerStateSnapshot:
    return LayerStateSnapshot(
        layers=[dict(layer_row) for layer_row in state.layers],
        material_names=list(state.material_names),
        material_ids=list(state.material_ids),
        thicknesses_m=list(state.thicknesses_m),
        refractive_indices=list(state.refractive_indices),
        analyte_indices=list(state.analyte_indices),
    )


@dataclass(slots=True)
class _LayerPayload:
    material_name: str
    material_id: int
    thickness_m: float
    refractive_index: complex
    table_row: dict[str, str]


@dataclass(slots=True)
class _AnalytePayload:
    thickness_m: float
    analyte_indices: list[complex]
    table_row: dict[str, str]


# Parses numeric fields and prepares the normalized layer payload.
def _build_layer_payload(form_input: LayerFormInput) -> _LayerPayload:
    thickness_m = _parse_thickness_m(form_input.thickness_text, ["thickness"])
    dispersion_model = normalize_dispersion_model_name(form_input.dispersion_model)
    drude_lambda_p = ""
    drude_lambda_c = ""

    if dispersion_model == DRUDE_DISPERSION_MODEL:
        if material_supports_drude_override(form_input.material_name):
            drude_lambda_p = _normalize_text_number(form_input.drude_lambda_p_text)
            drude_lambda_c = _normalize_text_number(form_input.drude_lambda_c_text)
            _parse_float(drude_lambda_p, ["drude_lambda_p"])
            _parse_float(drude_lambda_c, ["drude_lambda_c"])
        elif not material_uses_builtin_drude(form_input.material_name):
            raise LayerValidationError(
                ["dispersion_model"],
                "The Drude model is available only for Silver, Gold, Copper, "
                "Aluminum, ITO and ZnO.",
            )
    elif dispersion_model == DRUDE_LORENTZ_DISPERSION_MODEL:
        if not material_supports_drude_lorentz(form_input.material_name):
            raise LayerValidationError(
                ["dispersion_model"],
                "The Drude–Lorentz model is currently available only for ITO and ZnO.",
            )
    elif dispersion_model == FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL:
        if not material_supports_filmetrics_experimental(form_input.material_name):
            raise LayerValidationError(
                ["dispersion_model"],
                "Experimental (Filmetrics) is available only for Copper.",
            )

    if form_input.interrogation_mode == "AIM":
        real_part = _parse_float(form_input.real_part_text, ["real_part_index"])
        imaginary_part = _parse_float(form_input.imaginary_part_text, ["imaginary_part_index"])
        refractive_index = complex(real_part, imaginary_part)
        refractive_index_label = str(refractive_index).replace("(", " ").replace(")", " ")
    elif form_input.material_name == "Custom":
        real_part = _parse_float(form_input.real_part_text, ["real_part_index"])
        imaginary_part = (
            0.0
            if form_input.interrogation_mode == "WIM"
            and not str(form_input.imaginary_part_text).strip()
            else _parse_float(form_input.imaginary_part_text, ["imaginary_part_index"])
        )
        refractive_index = complex(real_part, imaginary_part)
        refractive_index_label = str(refractive_index).replace("(", " ").replace(")", " ")
    else:
        refractive_index = complex(0, 0)
        refractive_index_label = "-"

    return _LayerPayload(
        material_name=form_input.material_name,
        material_id=form_input.material_id,
        thickness_m=thickness_m,
        refractive_index=refractive_index,
        table_row={
            "material": form_input.material_name,
            "thickness": _normalize_text_number(form_input.thickness_text),
            "refractiveIndex": refractive_index_label,
            "description": form_input.description,
            "dispersionModel": dispersion_model,
            "drudeLambdaP": drude_lambda_p,
            "drudeLambdaC": drude_lambda_c,
        },
    )


# Parses analyte thickness and refractive-index values for state updates.
def _build_analyte_payload(form_input: AnalyteFormInput) -> _AnalytePayload:
    thickness_m = _parse_thickness_m(form_input.thickness_text, ["analyte_thickness"])

    if form_input.sample_count < 1:
        raise LayerValidationError(["analyte_sample_count"])

    analyte_indices = [
        complex(round(form_input.initial_index + (sample_index * form_input.step), 4))
        for sample_index in range(int(form_input.sample_count))
    ]

    refractive_index_label = (
        f"{round(form_input.initial_index, 4)} - {round(analyte_indices[-1].real, 4)}"
    )

    return _AnalytePayload(
        thickness_m=thickness_m,
        analyte_indices=analyte_indices,
        table_row={
            "material": "Analyte",
            "thickness": _normalize_text_number(form_input.thickness_text),
            "refractiveIndex": refractive_index_label,
            "description": form_input.description,
        },
    )


def _parse_thickness_m(thickness_text: str, field_names: list[str]) -> float:
    return _parse_float(thickness_text, field_names) * 1e-9


def _parse_float(raw_value: str | float, field_names: list[str]) -> float:
    try:
        value = float(str(raw_value).replace(",", "."))
    except (TypeError, ValueError) as error:
        raise LayerValidationError(field_names) from error
    return value


def _normalize_text_number(raw_value: str) -> str:
    return str(raw_value).replace(",", ".")


# Prevents edit and removal operations from addressing an invalid row.
def _validate_index(state: LayerStateSnapshot, index: int) -> None:
    if index < 0 or index >= len(state.layers):
        raise IndexError("Layer index out of range.")
