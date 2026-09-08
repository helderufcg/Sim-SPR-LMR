"""Normalize presentation input and orchestrate simulation use cases.

The application layer converts UI-facing values into domain contracts,
validates workflow stages, and applies state transformations before delegating
numerical work to the core. It may understand presentation formats, but it does
not manipulate widgets or implement optical models.
"""

from .layer_state_service import (
    AnalyteFormInput,
    LayerFormInput,
    LayerStateSnapshot,
    LayerValidationError,
    append_analyte,
    append_layer,
    remove_layer,
    replace_analyte,
    replace_layer,
)
from .parameter_mapper import SimulationParameterInput, build_simulation_config
from .parametric_analysis_service import (
    ParametricAnalysisInput,
    build_inclusive_sweep_values,
    run_parametric_analysis,
)
from .simulation_service import SimulationExecution, run_simulation_from_parameters
from .simulation_validation import (
    SimulationValidationError,
    validate_simulation_parameter_input,
    validate_simulation_parameter_input_stage,
)

__all__ = [
    "AnalyteFormInput",
    "LayerFormInput",
    "LayerStateSnapshot",
    "LayerValidationError",
    "ParametricAnalysisInput",
    "SimulationExecution",
    "SimulationParameterInput",
    "SimulationValidationError",
    "append_analyte",
    "append_layer",
    "build_simulation_config",
    "build_inclusive_sweep_values",
    "remove_layer",
    "replace_analyte",
    "replace_layer",
    "run_simulation_from_parameters",
    "run_parametric_analysis",
    "validate_simulation_parameter_input",
    "validate_simulation_parameter_input_stage",
]
