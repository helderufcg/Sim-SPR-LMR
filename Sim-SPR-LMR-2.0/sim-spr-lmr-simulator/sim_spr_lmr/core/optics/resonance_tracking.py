"""Associate detected resonances across a changing external parameter."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from collections.abc import Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from sim_spr_lmr.core.domain import ParametricResonanceTrack, ResonanceDetection


@dataclass(slots=True)
# Internal state combines a public resonance track with its recent observations.
class _TrackState:
    output: ParametricResonanceTrack
    observations: list[tuple[int, float, float]] = field(default_factory=list)


# Associates detections across sweep steps using predicted positions and global assignment.
def track_resonances_by_continuity(
    detections_by_step: Sequence[Sequence[ResonanceDetection]],
    parameter_values: Sequence[float],
    *,
    response_axis_span: float,
    response_axis_resolution: float,
    single_resonance: bool = False,
) -> list[ParametricResonanceTrack]:
    """Track resonances using trend prediction and global minimum-cost assignment.

    Missing detections remain NaN. A track with two observations predicts its
    next position by linear extrapolation in the swept parameter, allowing two
    modes to retain identity when their spectral positions cross. In a
    single-resonance workflow, every valid detection is associated with the
    same track regardless of displacement or an intervening absence.
    """

    if len(detections_by_step) != len(parameter_values):
        raise ValueError("Detection and parameter sequences must have the same length.")

    tracks: list[_TrackState] = []
    total_steps = len(parameter_values)
    for step_index, raw_detections in enumerate(detections_by_step):
        detections = sorted(
            (item for item in raw_detections if np.isfinite(item.position)),
            key=lambda item: item.position,
        )
        if single_resonance:
            if not detections:
                continue
            if not tracks:
                tracks.append(_new_track(1, total_steps))
            detection = min(
                detections,
                key=lambda item: abs(
                    item.position
                    - _predict_position(tracks[0], float(parameter_values[step_index]))
                ),
            ) if tracks[0].observations else detections[0]
            _record_detection(
                tracks[0],
                detection,
                step_index,
                float(parameter_values[step_index]),
            )
            continue

        assignments, unmatched = _assign_detections(
            tracks,
            detections,
            step_index,
            parameter_values,
            response_axis_span=response_axis_span,
            response_axis_resolution=response_axis_resolution,
        )
        for track_index, detection_index in assignments:
            _record_detection(
                tracks[track_index],
                detections[detection_index],
                step_index,
                float(parameter_values[step_index]),
            )
        for detection_index in unmatched:
            track = _new_track(len(tracks) + 1, total_steps)
            _record_detection(
                track,
                detections[detection_index],
                step_index,
                float(parameter_values[step_index]),
            )
            tracks.append(track)

    return [track.output for track in tracks]


def _new_track(number: int, total_steps: int) -> _TrackState:
    missing = [float("nan")] * total_steps
    return _TrackState(
        output=ParametricResonanceTrack(
            label=f"Resonance {number}",
            positions=list(missing),
            fwhm=list(missing),
            minimum_response=list(missing),
            sensitivity=list(missing),
            quality_factor=list(missing),
        )
    )


def _record_detection(
    track: _TrackState,
    detection: ResonanceDetection,
    step_index: int,
    parameter_value: float,
) -> None:
    track.output.positions[step_index] = float(detection.position)
    track.output.fwhm[step_index] = float(detection.fwhm)
    track.output.minimum_response[step_index] = float(detection.minimum_response)
    track.output.sensitivity[step_index] = float(detection.sensitivity)
    track.output.quality_factor[step_index] = float(detection.quality_factor)
    track.observations.append((step_index, parameter_value, float(detection.position)))


# Matches current detections to existing tracks while preserving resonance identity.
def _assign_detections(
    tracks: Sequence[_TrackState],
    detections: Sequence[ResonanceDetection],
    step_index: int,
    parameter_values: Sequence[float],
    *,
    response_axis_span: float,
    response_axis_resolution: float,
) -> tuple[list[tuple[int, int]], list[int]]:
    if not tracks or not detections:
        return [], list(range(len(detections)))

    current_parameter = float(parameter_values[step_index])
    costs = np.full((len(tracks), len(detections)), np.inf, dtype=float)
    for track_index, track in enumerate(tracks):
        if not track.observations:
            continue
        prediction = _predict_position(track, current_parameter)
        last_step, _last_parameter, last_position = track.observations[-1]
        gap = max(step_index - last_step, 1)
        displacement = abs(prediction - last_position)
        has_velocity = len(track.observations) >= 2
        base_fraction = 0.03 if has_velocity else 0.12
        base_tolerance = max(
            abs(response_axis_span) * base_fraction,
            abs(response_axis_resolution) * 6.0,
        )
        tolerance = max(base_tolerance, displacement * 2.5) * sqrt(gap)
        for detection_index, detection in enumerate(detections):
            distance = abs(detection.position - prediction)
            if distance <= tolerance:
                costs[track_index, detection_index] = distance

    finite_cost = np.isfinite(costs)
    if not finite_cost.any():
        return [], list(range(len(detections)))
    sentinel = max(abs(response_axis_span), 1.0) * 1e6
    row_indices, column_indices = linear_sum_assignment(
        np.where(finite_cost, costs, sentinel)
    )
    assignments = [
        (int(row), int(column))
        for row, column in zip(row_indices, column_indices, strict=False)
        if finite_cost[row, column]
    ]
    assigned_detections = {column for _row, column in assignments}
    unmatched = [index for index in range(len(detections)) if index not in assigned_detections]
    return assignments, unmatched


# Extrapolates a track position from its previous observations.
def _predict_position(track: _TrackState, parameter_value: float) -> float:
    if len(track.observations) < 2:
        return track.observations[-1][2]
    _step_1, parameter_1, position_1 = track.observations[-2]
    _step_2, parameter_2, position_2 = track.observations[-1]
    parameter_delta = parameter_2 - parameter_1
    if np.isclose(parameter_delta, 0.0):
        return position_2
    slope = (position_2 - position_1) / parameter_delta
    return position_2 + (slope * (parameter_value - parameter_2))
