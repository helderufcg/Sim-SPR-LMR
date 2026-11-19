"""Plotting adapters for simulation results.

Functions exposed here read only from ``SimulationResult`` and do not depend on
the legacy widget state.
"""

from .result_plotter import build_simulation_summary, render_simulation_result

__all__ = ["build_simulation_summary", "render_simulation_result"]
