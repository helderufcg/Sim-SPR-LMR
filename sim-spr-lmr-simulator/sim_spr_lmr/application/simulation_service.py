"""High-level application use case for running one simulation request."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sim_spr_lmr.application.parameter_mapper import SimulationParameterInput
from sim_spr_lmr.application.simulation_validation import validate_simulation_parameter_input
from sim_spr_lmr.core.domain import SimulationConfig, SimulationResult
from sim_spr_lmr.core.optics import run_simulation

ProgressCallback = Callable[[int], None]
LogCallback = Callable[[str], None]


@dataclass(slots=True)
# Groups the original parameter snapshot, normalized config, and resulting simulation output.
class SimulationExecution:
    """Complete application-layer simulation payload."""

    parameter_input: SimulationParameterInput
    config: SimulationConfig
    result: SimulationResult


# Validates and maps presentation input before delegating numerical execution to the core.
def run_simulation_from_parameters(
    parameter_input: SimulationParameterInput,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> SimulationExecution:
    """Build the core config from UI parameters and execute the simulation."""

    # The application layer owns the transition from UI snapshot to
    # domain config, then delegates the actual physics to the core.
    config = validate_simulation_parameter_input(parameter_input)
    result = run_simulation(
        config=config,
        progress_callback=progress_callback,
        log_callback=log_callback,
    )
    return SimulationExecution(
        parameter_input=parameter_input,
        config=config,
        result=result,
    )
