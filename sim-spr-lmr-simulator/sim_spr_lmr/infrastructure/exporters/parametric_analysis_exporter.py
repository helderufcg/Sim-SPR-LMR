"""CSV export helpers for parametric-analysis metrics and spectra."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from sim_spr_lmr.core.domain import ParametricAnalysisResult


# Metrics use a long-form layout: each row identifies a parameter value and a resonance track.
def build_parametric_metrics_csv(result: ParametricAnalysisResult) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output)
    """Build long-form resonance metrics, retaining missing values as NaN."""

# Spectra use a wide layout so each swept parameter can be compared on the same response-axis rows.
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            result.parameter_axis_label,
            "Resonance",
            f"Resonance position ({result.response_axis_unit})",
            f"FWHM ({result.response_axis_unit})",
            f"Sensitivity ({result.sensitivity_unit})",
            f"Figure of merit ({result.quality_factor_unit})",
            "Minimum response",
        ]
    )
    for track in result.resonance_tracks:
        for index, parameter_value in enumerate(result.parameter_values):
            writer.writerow(
                [
                    _format_number(parameter_value),
                    track.label,
                    _format_number(track.positions[index]),
                    _format_number(track.fwhm[index]),
                    _format_number(track.sensitivity[index]),
                    _format_number(track.quality_factor[index]),
                    _format_number(track.minimum_response[index]),
                ]
            )
    return output.getvalue()


def build_parametric_spectra_csv(result: ParametricAnalysisResult) -> str:
    """Build one response column per swept parameter value."""

# Spectra use a wide layout so each swept parameter can be compared on the same response-axis rows.
    output = StringIO(newline="")
    writer = csv.writer(output)
    response_label = _response_label(result.response_quantity)
    writer.writerow(
        [f"{result.response_axis_label} ({result.response_axis_unit})"]
        + [
            f"{response_label} at {value:g} {result.parameter_unit}"
            for value in result.parameter_values
        ]
    )
    for axis_index, axis_value in enumerate(result.response_axis):
        writer.writerow(
            [_format_number(axis_value)]
            + [
                _format_number(curve[axis_index])
                for curve in result.response_curves
            ]
        )
    return output.getvalue()


def write_parametric_analysis_exports(
    result: ParametricAnalysisResult,
    metrics_path: str | Path,
) -> list[Path]:
    """Write the selected metrics CSV plus a sibling spectra CSV."""

    # Always produce a pair of related files with a predictable sibling name.
    resolved_metrics_path = Path(metrics_path)
    if resolved_metrics_path.suffix.lower() != ".csv":
        resolved_metrics_path = resolved_metrics_path.with_suffix(".csv")
    spectra_path = resolved_metrics_path.with_name(
        f"{resolved_metrics_path.stem}_spectra.csv"
    )
    resolved_metrics_path.write_text(
        build_parametric_metrics_csv(result),
        encoding="utf-8-sig",
    )
    spectra_path.write_text(
        build_parametric_spectra_csv(result),
        encoding="utf-8-sig",
    )
    return [resolved_metrics_path, spectra_path]


def _format_number(value: float) -> str:
    # Preserve missing measurements explicitly instead of writing an empty CSV field.
    return "NaN" if value != value else f"{value:.10g}"


def _response_label(response_quantity: str) -> str:
    # Converts the domain response identifier into a human-readable CSV header.
    if response_quantity == "transmission":
        return "Normalized Transmission"
    if response_quantity == "reflectance_db":
        return "Reflectance (dB)"
    return "Reflectance"
