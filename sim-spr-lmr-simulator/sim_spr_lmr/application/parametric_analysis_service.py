"""Application service for fixed-analyte one-dimensional parameter sweeps."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from math import pi
import time

import numpy as np

from sim_spr_lmr.core.domain import (
    ParametricAnalysisResult,
    ResonanceDetection,
    SimulationConfig,
    SimulationResult,
)
from sim_spr_lmr.core.optics import run_simulation, track_resonances_by_continuity


ProgressCallback = Callable[[int], None]
LogCallback = Callable[[str], None]
MAX_SWEEP_POINTS = 500


@dataclass(slots=True, frozen=True)
# Defines a fixed-analyte sweep request independently from the Qt window.
class ParametricAnalysisInput:
    """Normalized request assembled by the parametric-analysis window."""

    base_config: SimulationConfig
    parameter_kind: str
    parameter_values: Sequence[float]
    fixed_analyte_index: complex
    layer_index: int | None = None
    analyte_step: float | None = None


# Builds stable decimal sweep values while preventing accidental oversized analyses.
def build_inclusive_sweep_values(
    initial: float,
    final: float,
    step: float,
    *,
    max_points: int = MAX_SWEEP_POINTS,
) -> list[float]:
    """Build a stable inclusive decimal sweep and cap accidental huge runs."""

    if step <= 0:
        raise ValueError("Sweep step must be greater than zero.")
    if final <= initial:
        raise ValueError("Final sweep value must be greater than the initial value.")
    start_decimal = Decimal(str(initial))
    final_decimal = Decimal(str(final))
    step_decimal = Decimal(str(step))
    values: list[Decimal] = []
    current = start_decimal
    while current <= final_decimal:
        values.append(current)
        if len(values) > max_points:
            raise ValueError(f"Parameter sweep is limited to {max_points} values.")
        current += step_decimal
    if values[-1] != final_decimal:
        values.append(final_decimal)
    if len(values) > max_points:
        raise ValueError(f"Parameter sweep is limited to {max_points} values.")
    return [float(value) for value in values]


# Runs each sweep point, extracts detections, and assembles tracked resonance metrics.
def run_parametric_analysis(
    request: ParametricAnalysisInput,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> ParametricAnalysisResult:
    """Run one existing optical simulation per external parameter value."""

    parameter_values = [float(value) for value in request.parameter_values]
    _validate_request(request, parameter_values)
    analyte_pair = _sensitivity_analyte_pair(request)
    started_at = time.perf_counter()
    step_results: list[SimulationResult] = []
    detections_by_step: list[list[ResonanceDetection]] = []
    total_steps = len(parameter_values)

    for step_index, parameter_value in enumerate(parameter_values):
        config = _config_for_parameter_value(request, parameter_value, analyte_pair)
        if log_callback is not None:
            log_callback(
                f"Calculating {step_index + 1}/{total_steps}: "
                f"{_parameter_name(request.parameter_kind)} = {parameter_value:g} "
                f"{_parameter_unit(request.parameter_kind)}"
            )

        def report_step_progress(value: int, *, index: int = step_index) -> None:
            if progress_callback is not None:
                completed = index + (max(0, min(value, 100)) / 100.0)
                progress_callback(int(completed * 100 / total_steps))

        simulation_result = run_simulation(
            config,
            progress_callback=report_step_progress,
            log_callback=None,
        )
        step_results.append(simulation_result)
        detections_by_step.append(_extract_resonance_detections(simulation_result))

    if progress_callback is not None:
        progress_callback(100)

    first_result = step_results[0]
    response_axis = list(first_result.axis_x)
    response_span = (
        float(max(response_axis) - min(response_axis)) if len(response_axis) >= 2 else 1.0
    )
    response_resolution = (
        float(np.median(np.abs(np.diff(response_axis)))) if len(response_axis) >= 2 else 1.0
    )
    tracks = track_resonances_by_continuity(
        detections_by_step,
        parameter_values,
        response_axis_span=response_span,
        response_axis_resolution=response_resolution,
        single_resonance=(
            request.base_config.resonance_strategy != "lmr_spr_auto_multi_dip"
        ),
    )
    layer_index = request.layer_index if request.parameter_kind == "thickness" else None
    layer_name = (
        request.base_config.layers[layer_index].material_name
        if layer_index is not None
        else ""
    )
    return ParametricAnalysisResult(
        simulator=request.base_config.simulator,
        coupling=request.base_config.coupling,
        interrogation_mode=request.base_config.interrogation_mode,
        polarization=request.base_config.polarization,
        response_quantity=first_result.response_quantity,
        fixed_analyte_index=complex(request.fixed_analyte_index),
        parameter_kind=request.parameter_kind,
        parameter_name=_parameter_name(request.parameter_kind),
        parameter_unit=_parameter_unit(request.parameter_kind),
        parameter_values=parameter_values,
        varied_layer_index=layer_index,
        varied_layer_name=layer_name,
        response_axis=response_axis,
        response_axis_label=first_result.axis_label,
        response_axis_unit=first_result.axis_unit,
        response_curves=[
            list(result.response_curves or result.reflectance_curves)[0]
            for result in step_results
        ],
        resonance_tracks=tracks,
        runtime_seconds=time.perf_counter() - started_at,
    )


# Checks sweep bounds, layer selection, and the base configuration before execution.
def _validate_request(
    request: ParametricAnalysisInput,
    parameter_values: Sequence[float],
) -> None:
    if request.parameter_kind not in {"thickness", "incidence_angle"}:
        raise ValueError(f"Unsupported parametric-analysis kind: {request.parameter_kind}")
    if len(parameter_values) < 2:
        raise ValueError("Parametric analysis requires at least two parameter values.")
    if len(parameter_values) > MAX_SWEEP_POINTS:
        raise ValueError(f"Parameter sweep is limited to {MAX_SWEEP_POINTS} values.")
    if any(not np.isfinite(value) for value in parameter_values):
        raise ValueError("Sweep values must be finite.")
    if any(
        right <= left
        for left, right in zip(parameter_values[:-1], parameter_values[1:], strict=False)
    ):
        raise ValueError("Sweep values must be strictly increasing.")
    analyte = complex(request.fixed_analyte_index)
    if not np.isfinite(analyte.real) or not np.isfinite(analyte.imag):
        raise ValueError("The fixed analyte refractive index must be finite.")
    _sensitivity_analyte_pair(request)
    if request.parameter_kind == "thickness":
        if request.layer_index is None or not 0 <= request.layer_index < len(request.base_config.layers):
            raise ValueError("Select a valid layer for the thickness sweep.")
        layer = request.base_config.layers[request.layer_index]
        if layer.is_analyte:
            raise ValueError("The analyte thickness cannot be swept.")
        if request.base_config.coupling == "Prism" and request.layer_index == 0:
            raise ValueError("The semi-infinite prism thickness cannot be swept.")
        if any(value < 0.0 for value in parameter_values):
            raise ValueError("Layer thickness cannot be negative.")
    else:
        if request.base_config.coupling != "Prism" or request.base_config.interrogation_mode != "WIM":
            raise ValueError("Incidence-angle sweep is available only for Prism + WIM.")
        if any(value <= 0.0 or value >= 90.0 for value in parameter_values):
            raise ValueError("Incidence angles must be between 0 and 90 degrees.")


# Creates an isolated simulation configuration for one swept parameter value.
def _config_for_parameter_value(
    request: ParametricAnalysisInput,
    parameter_value: float,
    analyte_pair: Sequence[complex],
) -> SimulationConfig:
    config = replace(
        request.base_config,
        analyte_indices=list(analyte_pair),
    )
    if request.parameter_kind == "incidence_angle":
        return replace(config, incidence_angle_rad=parameter_value * (pi / 180.0))

    layers = list(config.layers)
    layer_index = int(request.layer_index)
    layers[layer_index] = replace(
        layers[layer_index],
        thickness_m=parameter_value * 1e-9,
    )
    return replace(config, layers=layers)


# Converts a simulation result into the detections consumed by the continuity tracker.
def _extract_resonance_detections(result: SimulationResult) -> list[ResonanceDetection]:
    detections: list[ResonanceDetection] = []
    if result.resonance_series:
        metric_sources = result.resonance_series.values()
    else:
        metric_sources = (
            {
                "points": result.resonance_points,
                "fwhm": result.fwhm,
                "minimum_response": result.minimum_reflectance,
                "sensitivity": result.sensitivity,
                "quality_factor": result.quality_factor,
            },
        )
    for metrics in metric_sources:
        point = _first_metric(metrics.get("points", []))
        if not np.isfinite(point):
            continue
        fwhm = _first_metric(metrics.get("fwhm", []))
        sensitivity = abs(_first_metric(metrics.get("sensitivity", [])))
        quality_factor = _first_metric(metrics.get("quality_factor", []))
        if (
            not np.isfinite(quality_factor)
            and np.isfinite(sensitivity)
            and fwhm > 0.0
        ):
            quality_factor = sensitivity / fwhm
        detections.append(
            ResonanceDetection(
                position=point,
                fwhm=fwhm,
                minimum_response=_first_metric(metrics.get("minimum_response", [])),
                sensitivity=sensitivity,
                quality_factor=quality_factor,
            )
        )
    return sorted(detections, key=lambda item: item.position)


def _first_metric(values: Sequence[float]) -> float:
    return float(values[0]) if values else float("nan")


def _sensitivity_analyte_pair(request: ParametricAnalysisInput) -> list[complex]:
    fixed_index = complex(request.fixed_analyte_index)
    step = request.analyte_step
    if step is None or not np.isfinite(step) or step <= 0.0:
        configured_indices = request.base_config.analyte_indices
        for left, right in zip(configured_indices[:-1], configured_indices[1:], strict=False):
            candidate = abs(complex(right).real - complex(left).real)
            if np.isfinite(candidate) and candidate > 0.0:
                step = candidate
                break
    if step is None or not np.isfinite(step) or step <= 0.0:
        raise ValueError(
            "A positive conventional analyte step is required to calculate sensitivity."
        )
    return [fixed_index, complex(fixed_index.real + float(step), fixed_index.imag)]


def _parameter_name(parameter_kind: str) -> str:
    return "Layer thickness" if parameter_kind == "thickness" else "Incidence angle"


def _parameter_unit(parameter_kind: str) -> str:
    return "nm" if parameter_kind == "thickness" else "°"
