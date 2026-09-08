"""Derive resonance metrics and domain results from optical-response curves.

Single-resonance workflows measure the dominant dip in each curve. LMR+SPR
detects multiple minima, refines their sampled positions, and calculates each
FWHM against an adjacent local baseline before assembling ``SimulationResult``.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.signal import find_peaks

from sim_spr_lmr.core.domain import SimulationConfig, SimulationResult


# Finds the dominant response dip, respecting the critical-angle region for AIM.
def calculate_resonance_point(
    axis_x: Sequence[float],
    reflectance: Sequence[float],
    interrogation_mode: str,
    critical_point: float | None = None,
) -> float:
    """Return the dominant response minimum, excluding pre-critical AIM data."""

    try:
        reflectance_values = list(reflectance)
        minimum_index = reflectance_values.index(min(reflectance_values))

        if interrogation_mode == "AIM" and critical_point is not None:
            axis_values = np.asarray(axis_x)
            critical_index = int(np.abs(axis_values - critical_point).argmin())
            reflectance_right_of_critical = reflectance_values[critical_index:-1]
            minimum_index = reflectance_values.index(min(reflectance_right_of_critical))

        return round(float(axis_x[minimum_index]), 6)
    except ValueError:
        return -1.0


# Measures the width of a resonance dip at its half-depth crossings.
def calculate_fwhm(
    curve: Sequence[float],
    axis_x: Sequence[float],
    interrogation_mode: str,
    critical_point: float | None = None,
) -> float:
    """Calculate the FWHM of a dominant single resonance.

    A half-depth level is calculated independently from each side maximum, and
    the level associated with the higher maximum is selected. The final two
    crossings are linearly interpolated on ``axis_x``, which is expressed in
    degrees for AIM and nanometers for WIM. In AIM, samples before the critical
    point are excluded from the baseline search.

    Multi-resonance processing uses its dedicated local-baseline calculation.
    """

    y_values = list(curve)
    axis_values = list(axis_x)
    if not y_values or not axis_values:
        return 1.0

    if len(y_values) != len(axis_values):
        return 1.0

    try:
        minimum_index = y_values.index(min(y_values))
        values_for_baseline = y_values

        if interrogation_mode == "AIM" and critical_point is not None:
            critical_index = int(np.abs(np.asarray(axis_values) - critical_point).argmin())
            values_for_baseline = y_values[critical_index:-1]
            minimum_index = values_for_baseline.index(min(values_for_baseline))

        values_left = values_for_baseline[: minimum_index + 1]
        values_right = values_for_baseline[minimum_index:]
        maximum_left = max(values_left)
        maximum_right = max(values_right)
        half_level_left = (maximum_left + min(values_left)) / 2.0
        half_level_right = (maximum_right + min(values_right)) / 2.0
        half_level = (
            half_level_left if maximum_left > maximum_right else half_level_right
        )

        signs = np.sign(np.add(y_values, -half_level))
        zero_crossings = signs[:-2] != signs[1:-1]
        zero_crossing_indices = np.where(zero_crossings)[0]
        right_crossing_index = int(zero_crossing_indices[-1])
        left_crossing_index = int(zero_crossing_indices[-2])

        x_right = axis_values[right_crossing_index] + (
            (axis_values[right_crossing_index + 1] - axis_values[right_crossing_index])
            * (
                (half_level - y_values[right_crossing_index])
                / (y_values[right_crossing_index + 1] - y_values[right_crossing_index])
            )
        )
        x_left = axis_values[left_crossing_index] + (
            (axis_values[left_crossing_index + 1] - axis_values[left_crossing_index])
            * (
                (half_level - y_values[left_crossing_index])
                / (y_values[left_crossing_index + 1] - y_values[left_crossing_index])
            )
        )

        return round(abs(float(x_right - x_left)), 6)
    except Exception:
        return 1.0


# Converts resonance displacement into sensitivity per refractive-index unit.
def calculate_sensitivity(resonance_points: Sequence[float], analyte_indices: Sequence[complex]) -> list[float]:
    """Return the sensitivity series derived from resonance point changes."""

    sensitivity: list[float] = []
    for index, resonance_point in enumerate(resonance_points):
        if index == 0:
            sensitivity.append(0.0)
            continue

        delta_x = abs(resonance_points[index - 1] - resonance_point)
        delta_index = abs(analyte_indices[index - 1] - analyte_indices[index])
        sensitivity.append(round((delta_x / delta_index), 6))

        if len(sensitivity) > 1:
            sensitivity[0] = sensitivity[1]

    return sensitivity


# Detects strict and plateau minima in a sampled response curve.
def find_local_minima(axis_x: Sequence[float], curve: Sequence[float]) -> list[int]:
    """Return the indices of local minima in the response curve."""

    _ = axis_x
    minima: list[int] = []
    y_values = list(curve)
    for index in range(1, len(y_values) - 1):
        if y_values[index] <= y_values[index - 1] and y_values[index] <= y_values[index + 1]:
            if y_values[index] < y_values[index - 1] or y_values[index] < y_values[index + 1]:
                minima.append(index)
    return minima


def find_minimum_in_window(
    axis_x: Sequence[float],
    curve: Sequence[float],
    window_start_nm: float,
    window_stop_nm: float,
) -> int | None:
    """Return the minimum index inside a spectral window.

    This mirrors the standalone validation script, which identifies each
    resonance by looking for the minimum transmission inside a predefined
    wavelength band.
    """

    axis_values = np.asarray(axis_x)
    curve_values = np.asarray(curve)
    mask = (axis_values >= window_start_nm) & (axis_values <= window_stop_nm)

    if not np.any(mask):
        return None

    candidate_indices = np.where(mask)[0]
    local_values = curve_values[mask]
    if local_values.size == 0:
        return None

    local_minimum_offset = int(np.argmin(local_values))
    return int(candidate_indices[local_minimum_offset])


# Separates candidate LMR+SPR dips from noise and insignificant extrema.
def classify_lmr_spr_resonances(
    axis_x: Sequence[float],
    curve: Sequence[float],
    candidate_indices: Sequence[int],
    resonance_labels: Sequence[str] = (),
    resonance_windows_nm: dict[str, tuple[float, float]] | None = None,
    sort_mode: str = "axis",
    max_resonances: int = 3,
) -> dict[str, int]:
    """Classify resonance candidates using configurable windows or ordering rules."""

    curve_values = list(curve)
    labels = list(resonance_labels) if resonance_labels else [
        f"R{index}" for index in range(1, max_resonances + 1)
    ]

    if sort_mode == "depth":
        ordered_candidates = sorted(candidate_indices, key=lambda index: curve_values[index])
    else:
        ordered_candidates = sorted(candidate_indices, key=lambda index: axis_x[index])

    if resonance_windows_nm:
        classified: dict[str, int] = {}
        for label in labels:
            if label not in resonance_windows_nm:
                continue
            window_start, window_stop = resonance_windows_nm[label]
            minimum_index = find_minimum_in_window(axis_x, curve, window_start, window_stop)
            if minimum_index is not None:
                classified[label] = minimum_index

        used_indices = set(classified.values())
        fallback_candidates = [index for index in ordered_candidates if index not in used_indices]
        for label in labels:
            if label in classified or not fallback_candidates:
                continue
            classified[label] = fallback_candidates.pop(0)
        return classified

    if not ordered_candidates:
        return {}

    classified = {}
    for label, minimum_index in zip(labels, ordered_candidates[:max_resonances], strict=False):
        classified[label] = minimum_index
    return classified


def calculate_fwhm_at_index(curve: Sequence[float], axis_x: Sequence[float], minimum_index: int) -> float:
    """Calculate FWHM around a specific dip index."""

    if minimum_index < 0 or minimum_index >= len(curve):
        return 1.0

    y_values = list(curve)
    axis_values = list(axis_x)
    if len(y_values) != len(axis_values):
        return 1.0

    try:
        minimum_value = y_values[minimum_index]
        left_baseline = max(y_values[: minimum_index + 1])
        half_level = minimum_value + ((left_baseline - minimum_value) / 2)

        left_crossing_index = None
        for index in range(minimum_index - 1, -1, -1):
            if y_values[index] > half_level and y_values[index + 1] <= half_level:
                left_crossing_index = index
                break

        right_crossing_index = None
        for index in range(minimum_index, len(y_values) - 1):
            if y_values[index] <= half_level and y_values[index + 1] > half_level:
                right_crossing_index = index
                break

        if left_crossing_index is None or right_crossing_index is None:
            return 1.0

        x_left = axis_values[left_crossing_index] + (
            (axis_values[left_crossing_index + 1] - axis_values[left_crossing_index])
            * (
                (half_level - y_values[left_crossing_index])
                / (y_values[left_crossing_index + 1] - y_values[left_crossing_index])
            )
        )
        x_right = axis_values[right_crossing_index] + (
            (axis_values[right_crossing_index + 1] - axis_values[right_crossing_index])
            * (
                (half_level - y_values[right_crossing_index])
                / (y_values[right_crossing_index + 1] - y_values[right_crossing_index])
            )
        )

        return round(abs(float(x_right - x_left)), 6)
    except Exception:
        return 1.0


def calculate_multi_resonance_sensitivity(
    resonance_points: Sequence[float],
    analyte_indices: Sequence[complex],
) -> list[float]:
    """Calculate sensitivity for one named resonance tracked across analytes."""

    cleaned_points = [point for point in resonance_points]
    sensitivity: list[float] = []

    for index, resonance_point in enumerate(cleaned_points):
        if index == 0:
            sensitivity.append(0.0)
            continue

        previous_point = cleaned_points[index - 1]
        if np.isnan(previous_point) or np.isnan(resonance_point):
            sensitivity.append(0.0)
            continue

        # Preserve displacement direction: a blue shift has negative sensitivity.
        delta_x = resonance_point - previous_point
        delta_index = analyte_indices[index].real - analyte_indices[index - 1].real
        if np.isclose(delta_index, 0.0):
            sensitivity.append(0.0)
            continue
        sensitivity.append(round((delta_x / delta_index), 6))

        if len(sensitivity) > 1:
            sensitivity[0] = sensitivity[1]

    return sensitivity


def _refine_minimum_parabolic(
    wavelengths_nm: np.ndarray,
    transmission: np.ndarray,
    minimum_index: int,
) -> tuple[float, float]:
    """Refine a sampled minimum with a three-point parabolic fit."""

    if minimum_index <= 0 or minimum_index >= len(transmission) - 1:
        return float(wavelengths_nm[minimum_index]), float(transmission[minimum_index])

    x_values = wavelengths_nm[minimum_index - 1 : minimum_index + 2]
    y_values = transmission[minimum_index - 1 : minimum_index + 2]
    coefficient_a, coefficient_b, coefficient_c = np.polyfit(x_values, y_values, 2)
    if coefficient_a <= 0:
        return float(wavelengths_nm[minimum_index]), float(transmission[minimum_index])

    refined_wavelength = -coefficient_b / (2 * coefficient_a)
    if not (x_values[0] <= refined_wavelength <= x_values[-1]):
        return float(wavelengths_nm[minimum_index]), float(transmission[minimum_index])
    return float(refined_wavelength), float((coefficient_a * refined_wavelength**2) + (coefficient_b * refined_wavelength) + coefficient_c)


def _interpolate_crossing(x1: float, y1: float, x2: float, y2: float, target: float) -> float:
    if y1 == y2:
        return float("nan")
    return float(x1 + ((target - y1) * (x2 - x1) / (y2 - y1)))


LMR_SPR_MIN_RESONANCE_PROMINENCE = 0.02


# Detects and measures multiple resonances in an LMR+SPR response.
def detect_lmr_spr_resonances(
    axis_x: Sequence[float],
    curve: Sequence[float],
    minimum_prominence: float = LMR_SPR_MIN_RESONANCE_PROMINENCE,
) -> list[int]:
    """Detect every significant spectral dip without fixed wavelength bands.

    The response is inverted and processed as a peak signal. Only a minimal
    three-sample spacing is imposed so nearby resonances are not discarded.
    """

    wavelengths_nm = np.asarray(axis_x, dtype=float)
    response = np.asarray(curve, dtype=float)
    if wavelengths_nm.ndim != 1 or response.ndim != 1:
        return []
    if wavelengths_nm.size != response.size or response.size < 3:
        return []
    if np.any(~np.isfinite(wavelengths_nm)) or np.any(~np.isfinite(response)):
        return []

    inverted_response = float(np.max(response)) - response
    indices, _properties = find_peaks(
        inverted_response,
        prominence=float(minimum_prominence),
        distance=3,
    )
    return sorted((int(index) for index in indices), key=lambda index: wavelengths_nm[index])


def _find_multi_resonance_boundaries(
    response: np.ndarray,
    resonance_indices: Sequence[int],
) -> list[tuple[int, int]]:
    """Return adjacent-maximum limits for each automatically detected dip."""

    if not resonance_indices:
        return []

    boundaries = [int(np.argmax(response[: resonance_indices[0] + 1]))]
    for left_resonance, right_resonance in zip(
        resonance_indices[:-1], resonance_indices[1:], strict=False
    ):
        local_maximum = left_resonance + int(
            np.argmax(response[left_resonance : right_resonance + 1])
        )
        boundaries.append(local_maximum)
    last_resonance = resonance_indices[-1]
    boundaries.append(last_resonance + int(np.argmax(response[last_resonance:])))
    return list(zip(boundaries[:-1], boundaries[1:], strict=False))


def _calculate_multi_resonance_fwhm(
    wavelengths_nm: np.ndarray,
    response: np.ndarray,
    resonance_index: int,
    left_limit: int,
    right_limit: int,
) -> float:
    """Calculate a resonance FWHM using its adjacent local baseline."""

    minimum = float(response[resonance_index])
    left_maximum = float(response[left_limit])
    right_maximum = float(response[right_limit])
    local_baseline = min(
        max(left_maximum, right_maximum),
        (2.0 * min(left_maximum, right_maximum)) - minimum,
    )
    if local_baseline <= minimum or np.isclose(local_baseline, minimum):
        return float("nan")
    half_depth_level = (local_baseline + minimum) / 2.0

    left_crossing = float("nan")
    for index in range(resonance_index - 1, left_limit - 1, -1):
        y0 = float(response[index] - half_depth_level)
        y1 = float(response[index + 1] - half_depth_level)
        if y0 == 0.0 or y0 * y1 <= 0.0:
            left_crossing = _interpolate_crossing(
                float(wavelengths_nm[index]),
                float(response[index]),
                float(wavelengths_nm[index + 1]),
                float(response[index + 1]),
                half_depth_level,
            )
            break

    right_crossing = float("nan")
    for index in range(resonance_index, right_limit):
        y0 = float(response[index] - half_depth_level)
        y1 = float(response[index + 1] - half_depth_level)
        if y0 == 0.0 or y0 * y1 <= 0.0:
            right_crossing = _interpolate_crossing(
                float(wavelengths_nm[index]),
                float(response[index]),
                float(wavelengths_nm[index + 1]),
                float(response[index + 1]),
                half_depth_level,
            )
            break

    width = right_crossing - left_crossing
    if np.isnan(width) or width <= 0.0:
        return float("nan")
    return float(width)


# Builds a domain result from automatically tracked multi-resonance metrics.
def build_automatic_lmr_spr_result(
    config: SimulationConfig,
    axis_x: Sequence[float],
    response_curves: Sequence[Sequence[float]],
    runtime_seconds: float,
) -> SimulationResult:
    """Build generic numbered metrics for every detected LMR+SPR dip."""

    wavelengths_nm = np.asarray(axis_x, dtype=float)
    curves = [np.asarray(curve, dtype=float) for curve in response_curves]
    detections: list[list[tuple[float, float, float]]] = []

    for response in curves:
        resonance_indices = detect_lmr_spr_resonances(wavelengths_nm, response)
        boundaries = _find_multi_resonance_boundaries(response, resonance_indices)
        curve_detections: list[tuple[float, float, float]] = []
        for resonance_index, (left_limit, right_limit) in zip(
            resonance_indices, boundaries, strict=False
        ):
            wavelength, minimum_response = _refine_minimum_parabolic(
                wavelengths_nm,
                response,
                resonance_index,
            )
            fwhm = _calculate_multi_resonance_fwhm(
                wavelengths_nm,
                response,
                resonance_index,
                left_limit,
                right_limit,
            )
            curve_detections.append(
                (
                    round(wavelength, 6),
                    minimum_response,
                    round(fwhm, 6) if np.isfinite(fwhm) else fwhm,
                )
            )
        detections.append(curve_detections)

    resonance_count = max((len(items) for items in detections), default=0)
    resonance_series: dict[str, dict[str, list[float]]] = {}
    for resonance_number in range(1, resonance_count + 1):
        label = f"Resonance {resonance_number}"
        points: list[float] = []
        minimum_response: list[float] = []
        fwhm: list[float] = []
        for curve_detections in detections:
            if resonance_number <= len(curve_detections):
                point, minimum, width = curve_detections[resonance_number - 1]
            else:
                point = minimum = width = float("nan")
            points.append(point)
            minimum_response.append(minimum)
            fwhm.append(width)

        sensitivity = calculate_multi_resonance_sensitivity(points, config.analyte_indices)
        quality_factor = [
            (
                round(abs(sensitivity_value) / width, 6)
                if np.isfinite(sensitivity_value) and np.isfinite(width) and width > 0.0
                else 0.0
            )
            for sensitivity_value, width in zip(sensitivity, fwhm, strict=False)
        ]
        resonance_series[label] = {
            "points": points,
            "minimum_response": minimum_response,
            "fwhm": fwhm,
            "sensitivity": sensitivity,
            "quality_factor": quality_factor,
        }

    if resonance_series:
        primary_metrics = resonance_series["Resonance 1"]
    else:
        empty_metrics = [float("nan")] * len(curves)
        primary_metrics = {
            "points": list(empty_metrics),
            "minimum_response": list(empty_metrics),
            "fwhm": list(empty_metrics),
            "sensitivity": [0.0] * len(curves),
            "quality_factor": [0.0] * len(curves),
        }

    curve_lists = [curve.tolist() for curve in curves]
    return SimulationResult(
        simulator=config.simulator,
        interrogation_mode=config.interrogation_mode,
        polarization=config.polarization,
        response_quantity=config.response_quantity,
        analyte_indices=list(config.analyte_indices),
        axis_x=wavelengths_nm.tolist(),
        axis_label="Wavelength",
        axis_symbol="lambda",
        axis_unit="nm",
        response_curves=curve_lists,
        reflectance_curves=curve_lists,
        resonance_series=resonance_series,
        resonance_points=list(primary_metrics["points"]),
        sensitivity=list(primary_metrics["sensitivity"]),
        critical_points=[],
        minimum_reflectance=list(primary_metrics["minimum_response"]),
        fwhm=list(primary_metrics["fwhm"]),
        quality_factor=list(primary_metrics["quality_factor"]),
        validation_notes=[],
        runtime_seconds=runtime_seconds,
    )


# Assembles the standard SimulationResult for conventional workflows.
def build_simulation_result(
    config: SimulationConfig,
    axis_x: Sequence[float],
    reflectance_curves: Sequence[Sequence[float]],
    runtime_seconds: float,
    critical_points: Sequence[float] | None = None,
) -> SimulationResult:
    """Build a complete simulation result from raw curves and scan metadata."""

    if config.resonance_strategy == "lmr_spr_auto_multi_dip":
        return build_automatic_lmr_spr_result(
            config=config,
            axis_x=axis_x,
            response_curves=reflectance_curves,
            runtime_seconds=runtime_seconds,
        )

    critical_points = list(critical_points or [])
    axis_values = [float(value) for value in axis_x]
    curves = [list(curve) for curve in reflectance_curves]

    if config.interrogation_mode == "AIM":
        axis_label, axis_symbol, axis_unit = "Angle", "theta", "deg"
    else:
        axis_label, axis_symbol, axis_unit = "Wavelength", "lambda", "nm"

    resonance_points = []
    minimum_reflectance = []
    fwhm = []

    # Each raw curve is converted into the scalar metrics consumed later by the
    # plotting and export layers.
    for curve_index, curve in enumerate(curves):
        critical_point = critical_points[curve_index] if curve_index < len(critical_points) else None
        resonance_points.append(
            calculate_resonance_point(
                axis_x=axis_values,
                reflectance=curve,
                interrogation_mode=config.interrogation_mode,
                critical_point=critical_point,
            )
        )
        minimum_reflectance.append(min(curve))
        fwhm.append(
            calculate_fwhm(
                curve=curve,
                axis_x=axis_values,
                interrogation_mode=config.interrogation_mode,
                critical_point=critical_point,
            )
        )

    sensitivity = calculate_sensitivity(resonance_points, config.analyte_indices)
    quality_factor = [
        round(abs(sensitivity[index] / fwhm[index]), 6) if fwhm[index] else 0.0
        for index in range(len(fwhm))
    ]

    primary_label = config.expected_resonance_labels[0]
    resonance_series = {
        primary_label: {
            "points": list(resonance_points),
            "minimum_response": list(minimum_reflectance),
            "fwhm": list(fwhm),
            "sensitivity": list(sensitivity),
            "quality_factor": list(quality_factor),
        }
    }

    return SimulationResult(
        simulator=config.simulator,
        interrogation_mode=config.interrogation_mode,
        polarization=config.polarization,
        response_quantity=config.response_quantity,
        analyte_indices=list(config.analyte_indices),
        axis_x=axis_values,
        axis_label=axis_label,
        axis_symbol=axis_symbol,
        axis_unit=axis_unit,
        response_curves=curves,
        reflectance_curves=curves,
        resonance_series=resonance_series,
        resonance_points=resonance_points,
        sensitivity=sensitivity,
        critical_points=critical_points,
        minimum_reflectance=minimum_reflectance,
        fwhm=fwhm,
        quality_factor=quality_factor,
        validation_notes=[],
        runtime_seconds=runtime_seconds,
    )
