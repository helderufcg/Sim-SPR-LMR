"""Domain objects exchanged between the UI and the simulation core.

These dataclasses define the stable contract between layers during simulation.
"""

from .simulation_config import (
    FiberConfig,
    FiberCoreConfig,
    LayerConfig,
    SellmeierCoefficients,
    SimulationConfig,
)
from .simulation_result import SimulationResult
from .parametric_analysis_result import (
    ParametricAnalysisResult,
    ParametricResonanceTrack,
    ResonanceDetection,
)

__all__ = [
    "FiberConfig",
    "FiberCoreConfig",
    "LayerConfig",
    "ParametricAnalysisResult",
    "ParametricResonanceTrack",
    "ResonanceDetection",
    "SellmeierCoefficients",
    "SimulationConfig",
    "SimulationResult",
]
