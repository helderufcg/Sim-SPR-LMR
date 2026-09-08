"""Pure output models produced by the simulation core."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
# Holds simulation output independently from Qt widgets, plotting, and file export.
class SimulationResult:
    """Simulation output independent from plotting and export concerns.

    Presentation and export code should read from this structure instead of
    reaching back into the original widgets or legacy parallel lists.
    """

    simulator: str
    interrogation_mode: str
    polarization: str
    response_quantity: str = "reflectance"
    analyte_indices: list[complex] = field(default_factory=list)
    axis_x: list[float] = field(default_factory=list)
    axis_label: str = ""
    axis_symbol: str = ""
    axis_unit: str = ""
    response_curves: list[list[float]] = field(default_factory=list)
    reflectance_curves: list[list[float]] = field(default_factory=list)
    resonance_series: dict[str, dict[str, list[float]]] = field(default_factory=dict)
    resonance_points: list[float] = field(default_factory=list)
    sensitivity: list[float] = field(default_factory=list)
    critical_points: list[float] = field(default_factory=list)
    minimum_reflectance: list[float] = field(default_factory=list)
    fwhm: list[float] = field(default_factory=list)
    quality_factor: list[float] = field(default_factory=list)
    validation_notes: list[str] = field(default_factory=list)
    runtime_seconds: float = 0.0
