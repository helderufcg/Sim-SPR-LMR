"""Matplotlib adapters for displaying a normalized ``SimulationResult``."""

from __future__ import annotations

import numpy as np
from matplotlib import rc
from matplotlib.figure import Figure

from sim_spr_lmr.core.domain import SimulationResult
from sim_spr_lmr.core.optics.response_scale import (
    convert_response_curves,
    effective_response_quantity,
)

# Plot defaults shared by all simulation-result graphs.
DEFAULT_FONT = {"size": 5, "family": "Sans-Serif"}
DEFAULT_REFLECTANCE_TICKS = np.arange(0, 1.20, 0.20)


# Selects the requested graph and delegates drawing to the appropriate helper.
def render_simulation_result(
    figure: Figure,
    graph_name: str,
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> None:
    """Render a simulation graph into a Matplotlib figure."""

    # Graph selection is handled here so the Qt window only needs to provide
    # the selected label, not plotting rules.
    rc("font", **DEFAULT_FONT)
    figure.clear()

    match graph_name:
        case "Reflectance":
            _apply_default_layout(figure)
            _plot_response_curve(figure, simulation_result, reflectance_scale)
        case "Transmission":
            _apply_default_layout(figure)
            _plot_response_curve(figure, simulation_result)
        case "FWHM vs. Analyte":
            _apply_analyte_layout(figure)
            _plot_metric_graph(
                figure=figure,
                analyte_values=_real_analyte_values(simulation_result),
                simulation_result=simulation_result,
                metric_key="fwhm",
                y_label=f"FWHM ({simulation_result.axis_unit})",
            )
        case "Reflectance vs. Analyte":
            _apply_default_layout(figure)
            _plot_response_vs_analyte(figure, simulation_result, reflectance_scale)
        case "Transmission vs. Analyte":
            _apply_default_layout(figure)
            _plot_response_vs_analyte(figure, simulation_result)
        case "Resonance point vs. Analyte":
            _apply_analyte_layout(figure)
            _plot_metric_graph(
                figure=figure,
                analyte_values=_real_analyte_values(simulation_result),
                simulation_result=simulation_result,
                metric_key="points",
                y_label=f"Resonance {simulation_result.axis_label} ({simulation_result.axis_unit})",
            )
        case "Sensitivity vs. Analyte" | "Sensibility vs. Analyte":
            _apply_analyte_layout(figure)
            _plot_metric_graph(
                figure=figure,
                analyte_values=_real_analyte_values(simulation_result),
                simulation_result=simulation_result,
                metric_key="sensitivity",
                y_label=f"Sensitivity ({simulation_result.axis_unit} RI$U^-$$^1$)",
            )
        case "Figure of merit vs. Analyte":
            _apply_analyte_layout(figure)
            _plot_metric_graph(
                figure=figure,
                analyte_values=_real_analyte_values(simulation_result),
                simulation_result=simulation_result,
                metric_key="quality_factor",
                y_label="Figure of merit (RI$U^-$$^1$)",
            )
        case _:
            raise ValueError(f"Unsupported graph selection: {graph_name}")


# Builds the textual summary displayed alongside the rendered result.
def build_simulation_summary(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    """Return the textual summary associated with a simulation result."""

    lines = [
        f"Runtime: {simulation_result.runtime_seconds:.6f} s",
        f"Polarization ({simulation_result.polarization})",
        f"Response quantity: {_response_quantity_label(simulation_result, reflectance_scale)}",
        "",
    ]

    if simulation_result.simulator == "LMR+SPR":
        if not simulation_result.resonance_series:
            lines.append("No resonance was detected automatically in the simulated spectral range.")
            return "\n".join(lines).strip()
        for number, metric_series in enumerate(simulation_result.resonance_series.values(), start=1):
            lines.extend(
                [
                    f"Resonance {simulation_result.axis_label} ({simulation_result.axis_unit}) {number}: {metric_series.get('points', [])}",
                    f"FWHM ({simulation_result.axis_unit}) {number}: {metric_series.get('fwhm', [])}",
                    f"Sensitivity ({simulation_result.axis_unit}/RIU) {number}: {metric_series.get('sensitivity', [])}",
                    f"Figure of merit {number}: {metric_series.get('quality_factor', [])}",
                    "",
                ]
            )
        return "\n".join(lines).strip()

    return "\n".join(
        lines
        + [
            f"Resonance {simulation_result.axis_label} ({simulation_result.axis_unit}): {simulation_result.resonance_points}",
            f"FWHM ({simulation_result.axis_unit}): {simulation_result.fwhm}",
            f"Sensitivity ({simulation_result.axis_unit}/RIU): {simulation_result.sensitivity}",
            f"Figure of merit: {simulation_result.quality_factor}",
        ]
    )


# These helpers keep axis setup and curve-specific plotting separate.
def _plot_response_curve(
    figure: Figure,
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> None:
    """Plot the first response curve and annotate AIM critical point if available."""

    ax = figure.add_subplot()
    curve = _response_curves(simulation_result, reflectance_scale)[0]
    ax.plot(simulation_result.axis_x, curve)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(
        f"Incidence {simulation_result.axis_label} ({simulation_result.axis_unit})",
        fontdict=DEFAULT_FONT,
    )
    ax.set_ylabel(
        _response_quantity_label(simulation_result, reflectance_scale),
        fontdict=DEFAULT_FONT,
    )

    if _effective_response_quantity(simulation_result, reflectance_scale) == "reflectance":
        ax.set_yticks(DEFAULT_REFLECTANCE_TICKS)

    if (
        simulation_result.interrogation_mode == "AIM"
        and _effective_response_quantity(simulation_result, reflectance_scale) == "reflectance"
    ):
        _annotate_critical_point(ax, simulation_result)


def _plot_response_vs_analyte(
    figure: Figure,
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> None:
    """Plot one response curve per analyte value in the sweep."""

    ax = figure.add_subplot()
    legend: list[str] = []

    for analyte_index, response_curve in zip(
        simulation_result.analyte_indices,
        _response_curves(simulation_result, reflectance_scale),
        strict=False,
    ):
        ax.plot(simulation_result.axis_x, response_curve)
        legend.append(fr"{analyte_index.real:.3f}")

    ax.grid(True, alpha=0.3)
    ax.legend(legend, fontsize=6)
    ax.set_xlabel(
        f"Incidence {simulation_result.axis_label} ({simulation_result.axis_unit})",
        fontdict=DEFAULT_FONT,
    )
    ax.set_ylabel(
        _response_quantity_label(simulation_result, reflectance_scale),
        fontdict=DEFAULT_FONT,
    )
    if _effective_response_quantity(simulation_result, reflectance_scale) == "reflectance":
        ax.set_yticks(DEFAULT_REFLECTANCE_TICKS)


def _plot_metric_vs_analyte(
    figure: Figure,
    analyte_values: list[float],
    metric_values: list[float],
    y_label: str,
    legend_label: str | None = None,
) -> None:
    """Plot a scalar metric against analyte refractive index."""

    ax = figure.add_subplot()
    ax.tick_params(labelsize=5, labelrotation=45)
    ax.plot(analyte_values, metric_values, "-o", markersize=3, label=legend_label)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Analyte (RIU)", fontdict=DEFAULT_FONT)
    ax.set_ylabel(y_label, fontdict=DEFAULT_FONT)
    filtered_metric_values = [value for value in metric_values if value >= 0]
    if filtered_metric_values:
        ax.set_yticks(filtered_metric_values)
    ax.set_xticks(analyte_values)
    if legend_label is not None:
        ax.legend(fontsize=6)


def _plot_metric_graph(
    figure: Figure,
    analyte_values: list[float],
    simulation_result: SimulationResult,
    metric_key: str,
    y_label: str,
) -> None:
    if len(simulation_result.resonance_series) <= 1 and simulation_result.simulator != "LMR+SPR":
        metric_values = _legacy_metric_values(simulation_result, metric_key)
        _plot_metric_vs_analyte(
            figure=figure,
            analyte_values=analyte_values,
            metric_values=metric_values,
            y_label=y_label,
        )
        return

    ax = figure.add_subplot()
    ax.tick_params(labelsize=5, labelrotation=45)

    for label, metric_series in simulation_result.resonance_series.items():
        metric_values = list(metric_series.get(metric_key, []))
        ax.plot(analyte_values, metric_values, "-o", markersize=3, label=label)

    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Analyte (RIU)", fontdict=DEFAULT_FONT)
    ax.set_ylabel(y_label, fontdict=DEFAULT_FONT)
    ax.set_xticks(analyte_values)
    ax.legend(fontsize=6)


def _annotate_critical_point(ax, simulation_result: SimulationResult) -> None:
    curves = _response_curves(simulation_result)
    if not simulation_result.critical_points or not curves:
        return
    if len(simulation_result.axis_x) != len(curves[0]):
        return

    critical_point = simulation_result.critical_points[0]
    critical_reflectance = float(
        np.interp(critical_point, simulation_result.axis_x, curves[0])
    )
    annotation_text = (
        f"{simulation_result.axis_symbol}$_C$ = "
        f"{critical_point:.4f} {simulation_result.axis_unit}"
    )

    ax.annotate(
        text=annotation_text,
        xy=(critical_point, critical_reflectance),
        xytext=(simulation_result.axis_x[0], 0.6),
        bbox=dict(boxstyle="round4", fc="w"),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3, rad=-0.2"),
    )


def _apply_default_layout(figure: Figure) -> None:
    figure.subplots_adjust(
        left=0.160,
        bottom=0.195,
        right=0.930,
        top=0.950,
        wspace=0.1,
        hspace=0.2,
    )


def _apply_analyte_layout(figure: Figure) -> None:
    figure.subplots_adjust(
        left=0.210,
        bottom=0.285,
        right=0.900,
        top=0.960,
        wspace=0.1,
        hspace=0.2,
    )


def _real_analyte_values(simulation_result: SimulationResult) -> list[float]:
    return [float(analyte_index.real) for analyte_index in simulation_result.analyte_indices]


def _response_curves(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> list[list[float]]:
    curves = simulation_result.response_curves or simulation_result.reflectance_curves
    return convert_response_curves(
        curves,
        source_quantity=simulation_result.response_quantity,
        reflectance_scale=reflectance_scale,
    )


def _effective_response_quantity(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    return effective_response_quantity(
        simulation_result.response_quantity,
        reflectance_scale,
    )


def _response_quantity_label(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    response_quantity = _effective_response_quantity(simulation_result, reflectance_scale)
    if response_quantity == "transmission":
        return "Normalized Transmission"
    if response_quantity == "reflectance_db":
        return "Reflectance (dB)"
    if reflectance_scale is not None:
        return "Reflectance (R)"
    return "Reflectance"


def _legacy_metric_values(simulation_result: SimulationResult, metric_key: str) -> list[float]:
    if metric_key == "points":
        return simulation_result.resonance_points
    if metric_key == "fwhm":
        return simulation_result.fwhm
    if metric_key == "sensitivity":
        return simulation_result.sensitivity
    if metric_key == "quality_factor":
        return simulation_result.quality_factor
    raise ValueError(f"Unsupported legacy metric key: {metric_key}")
