"""Convert presentation snapshots into normalized simulation configuration.

Combo-box indices and values expressed in nanometers or degrees are translated
into domain labels and SI units. Layer rows and fiber fields are also combined
into the coherent contracts consumed by the numerical core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import pi

from sim_spr_lmr.core.domain import (
    FiberConfig,
    FiberCoreConfig,
    LayerConfig,
    SellmeierCoefficients,
    SimulationConfig,
)
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
    resolve_material_id,
)

# UI units are converted here to the SI units expected by the numerical core.
AIM_SCAN_STEP_RAD = 0.001 * (pi / 180)
WIM_SCAN_STEP_M = 0.1 * 1E-9
LMR_SPR_WIM_SCAN_STEP_M = 0.1 * 1E-9

PLASMONIC_MATERIAL_NAMES = {
    "Gold",
    "Silver",
    "Copper",
    "Aluminum",
    "Nickel",
    "Chromium",
}
LMR_SUPPORTING_MATERIAL_NAMES = {
    "ITO",
    "P3HT:PC61BM",
    "PEDOT:PSS",
    "2D HOIP",
    "TiO2",
    "ZnO",
    "Silicon",
    "Doped SWCNT",
    "SWCNT",
    "LiF",
    "Cytop",
    "FTO",
}


@dataclass(slots=True)
# Captures the presentation-layer snapshot before it is mapped to domain objects.
class SimulationParameterInput:
    """Raw parameter snapshot collected from the UI before core conversion."""

    simulator: str
    coupling_mode: int
    interrogation_mode: int
    polarization: str
    layer_rows: list[dict[str, object]] = field(default_factory=list)
    material_ids: list[int] = field(default_factory=list)
    thicknesses_m: list[float] = field(default_factory=list)
    refractive_indices: list[complex | None] = field(default_factory=list)
    analyte_indices: list[complex] = field(default_factory=list)
    aim_incidence_wavelength_nm: float = 0.0
    aim_scan_start_deg: float = 0.0
    aim_scan_stop_deg: float = 0.0
    wim_incidence_angle_deg: float = 0.0
    wim_scan_start_nm: float = 0.0
    wim_scan_stop_nm: float = 0.0
    fiber_type_code: int = 0
    fiber_length_mm: float = 0.0
    fiber_core_diameter_um: float = 0.0
    fiber_numerical_aperture: float = 0.0
    fiber_outer_diameter_um: float = 0.0
    fiber_residual_cladding_um: float = 0.0
    fiber_core_material_id: int | None = None
    fiber_core_material_name: str = ""
    fiber_use_custom_sellmeier: bool = False
    fiber_sellmeier_b1: float | None = None
    fiber_sellmeier_b2: float | None = None
    fiber_sellmeier_b3: float | None = None
    fiber_sellmeier_c1: float | None = None
    fiber_sellmeier_c2: float | None = None
    fiber_sellmeier_c3: float | None = None


# Builds a complete normalized SimulationConfig from UI values and legacy selections.
def build_simulation_config(parameters: SimulationParameterInput) -> SimulationConfig:
    """Map UI-oriented parameters into the normalized core configuration."""

    coupling = _map_coupling_mode(parameters.coupling_mode)
    interrogation_mode = _map_interrogation_mode(parameters.interrogation_mode)
    is_lmr_spr = parameters.simulator == "LMR+SPR"
    is_fiber = coupling == "Fiber"
    is_lmr_spr_prism = is_lmr_spr and coupling == "Prism"

    if is_fiber:
        _validate_multimode_fiber_parameter_set(parameters, interrogation_mode)
    if is_lmr_spr:
        _validate_lmr_spr_parameter_set(parameters, coupling, interrogation_mode)

    if interrogation_mode == "AIM":
        # AIM keeps the wavelength fixed and scans the incidence angle.
        incidence_wavelength_m = parameters.aim_incidence_wavelength_nm * 1E-9
        incidence_angle_rad = None
        scan_start = parameters.aim_scan_start_deg * (pi / 180)
        scan_stop = parameters.aim_scan_stop_deg * (pi / 180)
        scan_step = AIM_SCAN_STEP_RAD
    elif interrogation_mode == "WIM":
        # WIM keeps the angle fixed and scans the wavelength.
        incidence_wavelength_m = None
        incidence_angle_rad = parameters.wim_incidence_angle_deg * (pi / 180)
        scan_start = parameters.wim_scan_start_nm * 1E-9
        scan_stop = parameters.wim_scan_stop_nm * 1E-9
        scan_step = LMR_SPR_WIM_SCAN_STEP_M if is_lmr_spr else WIM_SCAN_STEP_M
    else:
        raise ValueError(f"Unsupported interrogation mode code: {parameters.interrogation_mode}")

    expected_labels = ("resonance",)
    resonance_windows_nm: dict[str, tuple[float, float]] = {}
    resonance_sort_mode = "axis"
    max_tracked_resonances = 1
    resonance_depth_threshold_ratio = 0.85

    if is_lmr_spr:
        # LMR+SPR can produce an unknown number of dips depending on coupling,
        # materials and geometry.  Detection therefore happens over the full
        # simulated spectrum; physical LMR/SPR names are deliberately not
        # inferred from fixed wavelength bands.
        expected_labels = ()
        max_tracked_resonances = 0

    return SimulationConfig(
        simulator=parameters.simulator or "Unknown",
        coupling=coupling,
        interrogation_mode=interrogation_mode,
        polarization=parameters.polarization,
        layers=_build_layer_configs(parameters),
        analyte_indices=list(parameters.analyte_indices),
        incidence_wavelength_m=incidence_wavelength_m,
        incidence_angle_rad=incidence_angle_rad,
        scan_start=scan_start,
        scan_stop=scan_stop,
        scan_step=scan_step,
        fiber=_build_fiber_config(parameters) if is_fiber else None,
        response_quantity=(
            "transmission"
            if is_fiber
            else "reflectance_db"
            if is_lmr_spr_prism
            else "reflectance"
        ),
        resonance_strategy="lmr_spr_auto_multi_dip" if is_lmr_spr else "single_dip",
        expected_resonance_labels=expected_labels,
        resonance_windows_nm=resonance_windows_nm,
        resonance_sort_mode=resonance_sort_mode,
        max_tracked_resonances=max_tracked_resonances,
        resonance_depth_threshold_ratio=resonance_depth_threshold_ratio,
        validation_notes=[],
    )


# Converts editable table rows into typed optical-layer configurations.
def _build_layer_configs(parameters: SimulationParameterInput) -> list[LayerConfig]:
    """Combine row metadata and parallel arrays into one coherent layer list."""

    layers: list[LayerConfig] = []

    for index, layer_data in enumerate(parameters.layer_rows):
        material_name = str(layer_data.get("material", ""))
        material_id = _resolve_layer_material_id(
            material_name=material_name,
            fallback_id=(parameters.material_ids[index] if index < len(parameters.material_ids) else -1),
        )
        dispersion_model = _resolve_layer_dispersion_model(layer_data)
        drude_lambda_p_um = _resolve_optional_layer_float(layer_data.get("drudeLambdaP"), "λp")
        drude_lambda_c_um = _resolve_optional_layer_float(layer_data.get("drudeLambdaC"), "λc")

        if dispersion_model == DRUDE_DISPERSION_MODEL:
            if material_supports_drude_override(material_name):
                if drude_lambda_p_um is None or drude_lambda_c_um is None:
                    raise ValueError(
                        "Drude parameters λp and λc are required when Silver, Gold "
                        "or Copper use the Drude model."
                    )
            elif not material_uses_builtin_drude(material_name):
                raise ValueError(
                    "Drude dispersion is supported only for Silver, Gold, Copper, "
                    "Aluminum, ITO and ZnO."
                )
        elif dispersion_model == DRUDE_LORENTZ_DISPERSION_MODEL:
            if not material_supports_drude_lorentz(material_name):
                raise ValueError(
                    "Drude–Lorentz dispersion is supported only for ITO, ZnO, Doped SWCNT and FTO."
                )
        elif dispersion_model == FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL:
            if not material_supports_filmetrics_experimental(material_name):
                raise ValueError(
                    "Experimental (Filmetrics) dispersion is supported only for Copper."
                )

        layers.append(
            LayerConfig(
                material_name=material_name,
                material_id=material_id,
                thickness_m=parameters.thicknesses_m[index] if index < len(parameters.thicknesses_m) else 0.0,
                refractive_index=(
                    parameters.refractive_indices[index]
                    if index < len(parameters.refractive_indices)
                    else None
                ),
                description=str(layer_data.get("description", "")),
                is_analyte=material_name == "Analyte",
                dispersion_model=dispersion_model,
                drude_lambda_p_um=drude_lambda_p_um,
                drude_lambda_c_um=drude_lambda_c_um,
            )
        )

    return layers


# Maps the selected fiber geometry, core material, and Sellmeier coefficients.
def _build_fiber_config(parameters: SimulationParameterInput) -> FiberConfig:
    """Translate the multimode-fiber inputs shared by all simulators."""

    return FiberConfig(
        fiber_type=_map_fiber_type(parameters.fiber_type_code),
        unclad_length_m=parameters.fiber_length_mm * 1e-3,
        core_diameter_m=parameters.fiber_core_diameter_um * 1e-6,
        numerical_aperture=parameters.fiber_numerical_aperture,
        angular_samples=300,
        power_distribution_model="guided",
        cladding_index=None,
        guiding_margin_rad=1e-5,
        outer_diameter_m=(
            parameters.fiber_outer_diameter_um * 1e-6
            if parameters.fiber_type_code == 2
            else None
        ),
        residual_cladding_thickness_m=(
            parameters.fiber_residual_cladding_um * 1e-6
            if parameters.fiber_type_code == 2
            else None
        ),
        core=FiberCoreConfig(
            material_name=parameters.fiber_core_material_name or "Silic",
            material_id=parameters.fiber_core_material_id,
            use_custom_sellmeier=parameters.fiber_use_custom_sellmeier,
            sellmeier=_build_sellmeier_coefficients(parameters),
        ),
    )


def _build_sellmeier_coefficients(parameters: SimulationParameterInput) -> SellmeierCoefficients | None:
    if not parameters.fiber_use_custom_sellmeier:
        return None

    coefficient_values = (
        parameters.fiber_sellmeier_b1,
        parameters.fiber_sellmeier_b2,
        parameters.fiber_sellmeier_b3,
        parameters.fiber_sellmeier_c1,
        parameters.fiber_sellmeier_c2,
        parameters.fiber_sellmeier_c3,
    )

    if any(value is None for value in coefficient_values):
        raise ValueError("Custom Sellmeier coefficients must be fully defined for the fiber core.")

    return SellmeierCoefficients(
        b1=float(parameters.fiber_sellmeier_b1),
        b2=float(parameters.fiber_sellmeier_b2),
        b3=float(parameters.fiber_sellmeier_b3),
        c1=float(parameters.fiber_sellmeier_c1),
        c2=float(parameters.fiber_sellmeier_c2),
        c3=float(parameters.fiber_sellmeier_c3),
    )


# Validates the parameter combinations required by multimode-fiber coupling.
def _validate_multimode_fiber_parameter_set(
    parameters: SimulationParameterInput,
    interrogation_mode: str,
) -> None:
    """Validate invariants shared by every multimode-fiber simulation."""

    if interrogation_mode != "WIM":
        raise ValueError("Optical-fiber coupling requires wavelength interrogation mode (WIM).")
    if parameters.polarization not in {"TM", "TE", "TE+TM"}:
        raise ValueError("Optical-fiber polarization must be TE, TM or TE+TM.")
    if not parameters.analyte_indices:
        raise ValueError("Optical-fiber coupling requires an analyte refractive-index sweep.")
    if len(parameters.layer_rows) < 2:
        raise ValueError("Optical-fiber coupling requires at least one coating layer plus the analyte.")

    material_names = [str(layer_row.get("material", "")) for layer_row in parameters.layer_rows]
    if material_names.count("Analyte") != 1:
        raise ValueError("Optical-fiber coupling requires exactly one analyte layer.")
    if material_names[-1] != "Analyte":
        raise ValueError("Optical-fiber coupling requires the analyte to be the last layer in the stack.")
    if parameters.fiber_type_code not in {1, 2}:
        raise ValueError("Select a supported fiber configuration.")
    if parameters.fiber_length_mm <= 0 or parameters.fiber_core_diameter_um <= 0:
        raise ValueError("Fiber length and core diameter must be greater than zero.")
    if parameters.fiber_numerical_aperture <= 0:
        raise ValueError("Fiber numerical aperture must be greater than zero.")

    if parameters.fiber_type_code == 2:
        if parameters.fiber_outer_diameter_um <= 0:
            raise ValueError("D-shaped fiber outer diameter must be greater than zero.")
        if parameters.fiber_residual_cladding_um < 0:
            raise ValueError("D-shaped fiber residual cladding cannot be negative.")
        if parameters.fiber_core_diameter_um >= parameters.fiber_outer_diameter_um:
            raise ValueError(
                "D-shaped fiber core diameter must be smaller than its outer diameter."
            )
        if (
            parameters.fiber_residual_cladding_um
            > parameters.fiber_outer_diameter_um / 2.0
        ):
            raise ValueError(
                "D-shaped fiber residual cladding cannot exceed the fiber radius."
            )
        if (
            parameters.fiber_core_diameter_um / 2.0
            + parameters.fiber_residual_cladding_um
            >= parameters.fiber_outer_diameter_um / 2.0
        ):
            raise ValueError(
                "D-shaped geometry requires core radius plus residual cladding "
                "to be smaller than the fiber outer radius."
            )


# Validates the additional restrictions of the combined LMR+SPR simulator.
def _validate_lmr_spr_parameter_set(
    parameters: SimulationParameterInput,
    coupling: str,
    interrogation_mode: str,
) -> None:
    if coupling not in {"Fiber", "Prism"}:
        raise ValueError("LMR+SPR requires Prism or optical-fiber coupling.")
    if interrogation_mode != "WIM":
        raise ValueError("LMR+SPR currently supports only wavelength interrogation mode (WIM).")
    if parameters.polarization not in {"TM", "TE", "TE+TM"}:
        raise ValueError("LMR+SPR polarization must be TE, TM or TE+TM.")
    if not parameters.analyte_indices:
        raise ValueError("LMR+SPR requires an analyte refractive-index sweep.")
    minimum_layers = 2 if coupling == "Fiber" else 3
    if len(parameters.layer_rows) < minimum_layers:
        if coupling == "Prism":
            raise ValueError("Prism-coupled LMR+SPR requires a prism, at least one coating layer and the analyte.")
        raise ValueError("LMR+SPR requires at least one coating layer plus the analyte.")
    material_names = [str(layer_row.get("material", "")) for layer_row in parameters.layer_rows]
    if "Analyte" not in material_names:
        raise ValueError("LMR+SPR requires an explicit analyte layer in the stack.")
    if coupling == "Fiber":
        if parameters.fiber_length_mm <= 0 or parameters.fiber_core_diameter_um <= 0:
            raise ValueError("Fiber length and core diameter must be greater than zero.")
        if parameters.fiber_numerical_aperture <= 0:
            raise ValueError("Fiber numerical aperture must be greater than zero.")
        if parameters.fiber_type_code == 2:
            if parameters.fiber_outer_diameter_um <= 0:
                raise ValueError("D-shaped fiber outer diameter must be greater than zero.")
            if parameters.fiber_residual_cladding_um < 0:
                raise ValueError("D-shaped fiber residual cladding cannot be negative.")
            if parameters.fiber_core_diameter_um >= parameters.fiber_outer_diameter_um:
                raise ValueError(
                    "D-shaped fiber core diameter must be smaller than its outer diameter."
                )
            if (
                parameters.fiber_residual_cladding_um
                > parameters.fiber_outer_diameter_um / 2.0
            ):
                raise ValueError(
                    "D-shaped fiber residual cladding cannot exceed the fiber radius."
                )
            if (
                parameters.fiber_core_diameter_um / 2.0
                + parameters.fiber_residual_cladding_um
                >= parameters.fiber_outer_diameter_um / 2.0
            ):
                raise ValueError(
                    "D-shaped geometry requires core radius plus residual cladding "
                    "to be smaller than the fiber outer radius."
                )

    analyte_index = material_names.index("Analyte")
    if coupling == "Fiber" and analyte_index != len(material_names) - 1:
        raise ValueError("LMR+SPR currently requires the analyte to be the last layer in the stack.")

    coating_material_names = (
        material_names[:analyte_index]
        if coupling == "Fiber"
        else [
            material_name
            for material_name in material_names[1:]
            if material_name != "Analyte"
        ]
    )
    if len(coating_material_names) < 1:
        raise ValueError("LMR+SPR requires at least one coating layer in addition to the analyte.")

    supported_resonant_material_names = (
        PLASMONIC_MATERIAL_NAMES | LMR_SUPPORTING_MATERIAL_NAMES
    )
    if not any(
        material_name in supported_resonant_material_names
        for material_name in coating_material_names
    ):
        raise ValueError(
            "LMR+SPR requires at least one supported resonant coating layer "
            "(for example Gold, Silver, Copper, Aluminum, Nickel, ITO, "
            "TiO2, ZnO, PEDOT:PSS, P3HT:PC61BM, 2D HOIP, Silicon, Doped SWCNT, "
            "Chromium, FTO, LiF or Cytop)."
        )


def _resolve_layer_material_id(material_name: str, fallback_id: int) -> int:
    try:
        return resolve_material_id(material_name)
    except ValueError:
        return fallback_id


def _resolve_layer_dispersion_model(layer_data: dict[str, object]) -> str:
    raw_model = layer_data.get("dispersionModel", EXPERIMENTAL_DISPERSION_MODEL)
    return normalize_dispersion_model_name(str(raw_model))


def _resolve_optional_layer_float(raw_value: object, field_label: str) -> float | None:
    normalized_value = str(raw_value or "").strip()
    if normalized_value == "":
        return None
    try:
        return float(normalized_value)
    except ValueError as error:
        raise ValueError(f"The Drude parameter {field_label} must be a valid number.") from error


def _map_fiber_type(fiber_type_code: int) -> str:
    if fiber_type_code == 1:
        return "removed_cladding"
    if fiber_type_code == 2:
        return "d_shaped"
    return "unknown"


def _map_coupling_mode(coupling_mode: int) -> str:
    return "Prism" if coupling_mode == 1 else "Fiber" if coupling_mode == 2 else "Unknown"


def _map_interrogation_mode(interrogation_mode: int) -> str:
    return "AIM" if interrogation_mode == 1 else "WIM" if interrogation_mode == 2 else "Unknown"
