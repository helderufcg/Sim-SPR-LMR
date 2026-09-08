"""Validate simulation input at navigation and execution boundaries.

Stage validation maps invalid combinations back to presentation fields so the
wizard can provide immediate feedback. Full validation also builds the domain
configuration, ensuring the numerical engine receives a coherent request.
"""

from __future__ import annotations

from sim_spr_lmr.application.parameter_mapper import SimulationParameterInput, build_simulation_config
from sim_spr_lmr.core.domain import SimulationConfig


# Carries both user-facing messages and the logical fields that should be highlighted.
class SimulationValidationError(ValueError):
    """Validation error with explicit UI field mapping."""

    def __init__(self, field_names: list[str], messages: list[str]) -> None:
        self.field_names = field_names
        self.messages = messages
        super().__init__("\n".join(messages))


# Applies only the validation rules needed to advance from the current wizard stage.
def validate_simulation_parameter_input_stage(
    parameter_input: SimulationParameterInput,
    stage: str,
) -> None:
    """Validate only the rules relevant to one navigation stage."""

    field_names: list[str] = []
    messages: list[str] = []

    if stage == "fiber":
        _validate_fiber_inputs(parameter_input, field_names, messages)
    elif stage == "layers":
        _validate_common_inputs(parameter_input, field_names, messages)
        _validate_layer_stack(parameter_input, field_names, messages)
        _validate_fiber_inputs(parameter_input, field_names, messages)
        _validate_buildable_stack(parameter_input, field_names, messages)
    elif stage == "run":
        _validate_common_inputs(parameter_input, field_names, messages)
        _validate_scan_inputs(parameter_input, field_names, messages)
        _validate_layer_stack(parameter_input, field_names, messages)
        _validate_fiber_inputs(parameter_input, field_names, messages)
        _validate_buildable_stack(parameter_input, field_names, messages)
    else:
        raise ValueError(f"Unsupported validation stage: {stage}")

    if messages:
        raise SimulationValidationError(
            field_names=_unique(field_names),
            messages=_unique(messages),
        )


# Performs full validation and returns the normalized domain configuration.
def validate_simulation_parameter_input(parameter_input: SimulationParameterInput) -> SimulationConfig:
    """Validate raw simulation inputs and return the normalized config."""

    validate_simulation_parameter_input_stage(parameter_input, stage="run")

    try:
        return build_simulation_config(parameter_input)
    except ValueError as error:
        mapped_fields = _map_build_error_to_fields(str(error))
        raise SimulationValidationError(
            field_names=mapped_fields,
            messages=[str(error)],
        ) from error


# Checks simulator, coupling, interrogation mode, and polarization choices shared by all paths.
def _validate_common_inputs(
    parameter_input: SimulationParameterInput,
    field_names: list[str],
    messages: list[str],
) -> None:
    if parameter_input.coupling_mode == 0:
        field_names.append("coupling_mode")
        messages.append("Select a coupling mode before running the simulation.")

    if parameter_input.interrogation_mode == 0:
        field_names.append("interrogation_mode")
        messages.append("Select an interrogation mode before running the simulation.")

    if not parameter_input.layer_rows:
        field_names.append("layer_stack")
        messages.append("Add the optical stack before running the simulation.")


# Validates scan ranges, incidence values, and analyte sampling parameters.
def _validate_scan_inputs(
    parameter_input: SimulationParameterInput,
    field_names: list[str],
    messages: list[str],
) -> None:
    if parameter_input.interrogation_mode == 1:
        if parameter_input.aim_incidence_wavelength_nm <= 0:
            field_names.append("aim_incidence_wavelength_nm")
            messages.append("The AIM incidence wavelength must be greater than zero.")
        if parameter_input.aim_scan_stop_deg <= parameter_input.aim_scan_start_deg:
            field_names.extend(["aim_scan_start_deg", "aim_scan_stop_deg"])
            messages.append("The AIM angular range must end after it starts.")
        return

    if parameter_input.interrogation_mode == 2:
        if parameter_input.wim_scan_stop_nm <= parameter_input.wim_scan_start_nm:
            field_names.extend(["wim_scan_start_nm", "wim_scan_stop_nm"])
            messages.append("The WIM spectral range must end after it starts.")

        if parameter_input.coupling_mode != 2:
            if not (0 < parameter_input.wim_incidence_angle_deg < 90):
                field_names.append("wim_incidence_angle_deg")
                messages.append("The WIM incidence angle must be between 0 and 90 degrees.")


# Verifies that the optical layer rows form a valid stack for the selected workflow.
def _validate_layer_stack(
    parameter_input: SimulationParameterInput,
    field_names: list[str],
    messages: list[str],
) -> None:
    material_names = [str(layer_row.get("material", "")) for layer_row in parameter_input.layer_rows]
    analyte_count = material_names.count("Analyte")

    if analyte_count == 0:
        field_names.append("layer_stack")
        messages.append("Add exactly one analyte layer before running the simulation.")
    elif analyte_count > 1:
        field_names.append("layer_stack")
        messages.append("Only one analyte layer is supported in the current simulation flow.")

def _validate_buildable_stack(
    parameter_input: SimulationParameterInput,
    field_names: list[str],
    messages: list[str],
) -> None:
    try:
        build_simulation_config(parameter_input)
    except ValueError as error:
        field_names.extend(_map_build_error_to_fields(str(error)))
        messages.append(str(error))


# Checks the fiber type, geometry, core material, and Sellmeier data when applicable.
def _validate_fiber_inputs(
    parameter_input: SimulationParameterInput,
    field_names: list[str],
    messages: list[str],
) -> None:
    requires_fiber = parameter_input.coupling_mode == 2
    if not requires_fiber:
        return

    if parameter_input.fiber_type_code == 0:
        field_names.append("fiber_type_code")
        messages.append("Select the fiber configuration before running the simulation.")

    if parameter_input.fiber_length_mm <= 0:
        field_names.append("fiber_length_mm")
        messages.append("Fiber sensing length must be greater than zero.")

    if parameter_input.fiber_core_diameter_um <= 0:
        field_names.append("fiber_core_diameter_um")
        messages.append("Fiber core diameter must be greater than zero.")

    if parameter_input.fiber_numerical_aperture <= 0:
        field_names.append("fiber_numerical_aperture")
        messages.append("Fiber numerical aperture must be greater than zero.")

    if parameter_input.fiber_type_code == 2:
        if parameter_input.fiber_outer_diameter_um <= 0:
            field_names.append("fiber_outer_diameter_um")
            messages.append("D-shaped fiber outer diameter must be greater than zero.")

        if parameter_input.fiber_residual_cladding_um < 0:
            field_names.append("fiber_residual_cladding_um")
            messages.append("Residual cladding thickness cannot be negative.")

        polishing_depth_um = (
            parameter_input.fiber_core_diameter_um / 2.0
            + parameter_input.fiber_residual_cladding_um
        )
        outer_radius_um = parameter_input.fiber_outer_diameter_um / 2.0
        if (
            parameter_input.fiber_outer_diameter_um > 0
            and parameter_input.fiber_core_diameter_um
            >= parameter_input.fiber_outer_diameter_um
        ):
            field_names.extend(["fiber_core_diameter_um", "fiber_outer_diameter_um"])
            messages.append(
                "D-shaped fiber core diameter must be smaller than its outer diameter."
            )

        if (
            outer_radius_um > 0
            and parameter_input.fiber_residual_cladding_um > outer_radius_um
        ):
            field_names.extend(["fiber_residual_cladding_um", "fiber_outer_diameter_um"])
            messages.append(
                "D-shaped fiber residual cladding cannot exceed the fiber radius."
            )
        elif (
            outer_radius_um > 0
            and parameter_input.fiber_core_diameter_um
            < parameter_input.fiber_outer_diameter_um
            and polishing_depth_um >= outer_radius_um
        ):
            field_names.extend(
                [
                    "fiber_outer_diameter_um",
                    "fiber_core_diameter_um",
                    "fiber_residual_cladding_um",
                ]
            )
            messages.append(
                "D-shaped geometry requires core radius plus residual cladding "
                "to be smaller than the fiber outer radius."
            )

    if parameter_input.fiber_use_custom_sellmeier:
        coefficient_map = {
            "fiber_sellmeier_b1": parameter_input.fiber_sellmeier_b1,
            "fiber_sellmeier_b2": parameter_input.fiber_sellmeier_b2,
            "fiber_sellmeier_b3": parameter_input.fiber_sellmeier_b3,
            "fiber_sellmeier_c1": parameter_input.fiber_sellmeier_c1,
            "fiber_sellmeier_c2": parameter_input.fiber_sellmeier_c2,
            "fiber_sellmeier_c3": parameter_input.fiber_sellmeier_c3,
        }
        missing_coefficients = [
            field_name for field_name, value in coefficient_map.items() if value is None
        ]
        if missing_coefficients:
            field_names.extend(missing_coefficients)
            messages.append("Fill in all custom Sellmeier coefficients for the fiber core.")
        return

    if parameter_input.fiber_core_material_name.strip().lower() not in {
        "silic",
        "silica",
        "pmma",
    }:
        field_names.append("fiber_core_material_name")
        messages.append(
            "The predefined fiber-core model supports Silica and PMMA. "
            "Select one of them or enable Custom Sellmeier coefficients."
        )


def _map_build_error_to_fields(error_message: str) -> list[str]:
    field_names: list[str] = []
    lowered_message = error_message.lower()

    if "optical-fiber coupling" in lowered_message:
        field_names.append("coupling_mode")
    if "wavelength interrogation mode" in lowered_message:
        field_names.append("interrogation_mode")
    if "polarization" in lowered_message:
        field_names.append("polarization")
    if "analyte refractive-index sweep" in lowered_message:
        field_names.append("layer_stack")
    if "analyte to be the last layer" in lowered_message:
        field_names.append("layer_stack")
    if "coating layer" in lowered_message or "coating stack" in lowered_message:
        field_names.append("layer_stack")
    if "plasmonic metal layer" in lowered_message:
        field_names.append("layer_stack")
    if "lmr-supporting coating layer" in lowered_message:
        field_names.append("layer_stack")
    if "fiber length" in lowered_message:
        field_names.append("fiber_length_mm")
    if "core diameter" in lowered_message:
        field_names.append("fiber_core_diameter_um")
    if "numerical aperture" in lowered_message:
        field_names.append("fiber_numerical_aperture")
    if "outer diameter" in lowered_message:
        field_names.append("fiber_outer_diameter_um")
    if "residual cladding" in lowered_message:
        field_names.append("fiber_residual_cladding_um")
    if "sellmeier coefficients" in lowered_message:
        field_names.extend(
            [
                "fiber_sellmeier_b1",
                "fiber_sellmeier_b2",
                "fiber_sellmeier_b3",
                "fiber_sellmeier_c1",
                "fiber_sellmeier_c2",
                "fiber_sellmeier_c3",
            ]
        )
    if "drude override" in lowered_message:
        field_names.append("dispersion_model")
    if "drude parameters" in lowered_message:
        field_names.extend(["drude_lambda_p", "drude_lambda_c"])
    if "drude parameter λp" in lowered_message:
        field_names.append("drude_lambda_p")
    if "drude parameter λc" in lowered_message:
        field_names.append("drude_lambda_c")

    return _unique(field_names) or ["layer_stack"]


def _unique(values: list[str]) -> list[str]:
    ordered_values: list[str] = []
    for value in values:
        if value not in ordered_values:
            ordered_values.append(value)
    return ordered_values
