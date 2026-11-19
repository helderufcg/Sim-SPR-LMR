"""Domain results produced by one-dimensional parameter sweeps."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
# Represents one resonance found at a single sweep step.
class ResonanceDetection:
    """One detected resonance before it is associated with a persistent track."""

    position: float
    fwhm: float = float("nan")
    minimum_response: float = float("nan")
    sensitivity: float = float("nan")
    quality_factor: float = float("nan")


@dataclass(slots=True)
# Keeps one resonance identity and its metrics across all sweep values.
class ParametricResonanceTrack:
    """Metrics for one resonance identity over all parameter values."""

    label: str
    positions: list[float] = field(default_factory=list)
    fwhm: list[float] = field(default_factory=list)
    minimum_response: list[float] = field(default_factory=list)
    sensitivity: list[float] = field(default_factory=list)
    quality_factor: list[float] = field(default_factory=list)


@dataclass(slots=True)
# Groups the complete output of a fixed-analyte parameter sweep.
class ParametricAnalysisResult:
    """Complete output from a fixed-analyte parametric analysis."""

    simulator: str
    coupling: str
    interrogation_mode: str
    polarization: str
    response_quantity: str
    fixed_analyte_index: complex
    parameter_kind: str
    parameter_name: str
    parameter_unit: str
    parameter_values: list[float] = field(default_factory=list)
    varied_layer_index: int | None = None
    varied_layer_name: str = ""
    response_axis: list[float] = field(default_factory=list)
    response_axis_label: str = ""
    response_axis_unit: str = ""
    response_curves: list[list[float]] = field(default_factory=list)
    resonance_tracks: list[ParametricResonanceTrack] = field(default_factory=list)
    runtime_seconds: float = 0.0

    @property
    def parameter_axis_label(self) -> str:
        return f"{self.parameter_name} ({self.parameter_unit})"

    @property
    def sensitivity_unit(self) -> str:
        return f"{self.response_axis_unit}/RIU"

    @property
    def quality_factor_unit(self) -> str:
        return "1/RIU"
