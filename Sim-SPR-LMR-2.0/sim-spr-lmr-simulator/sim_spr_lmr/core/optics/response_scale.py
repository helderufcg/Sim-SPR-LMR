"""Reflectance-scale conversions used by plotting and export adapters."""

from __future__ import annotations

from collections.abc import Sequence
from math import log10


# Response-scale constants define how prism reflectance is presented and exported.
REFLECTANCE_SCALE_LINEAR = "linear"
REFLECTANCE_SCALE_DB = "db"
REFLECTANCE_DB_FLOOR = 1e-12


# Determines the response quantity that should be shown for the selected scale.
def effective_response_quantity(
    source_quantity: str,
    reflectance_scale: str | None = None,
) -> str:
    """Return the response quantity presented for the requested scale."""

    if source_quantity == "transmission":
        return "transmission"
    if reflectance_scale == REFLECTANCE_SCALE_LINEAR:
        return "reflectance"
    if reflectance_scale == REFLECTANCE_SCALE_DB:
        return "reflectance_db"
    return source_quantity


# Converts curves for display without changing the original simulation metrics.
def convert_response_curves(
    curves: Sequence[Sequence[float]],
    *,
    source_quantity: str,
    reflectance_scale: str | None = None,
) -> list[list[float]]:
    """Convert reflectance curves for presentation without mutating metrics."""

    target_quantity = effective_response_quantity(source_quantity, reflectance_scale)
    curve_lists = [[float(value) for value in curve] for curve in curves]

    if source_quantity == "transmission" or source_quantity == target_quantity:
        return curve_lists
    if source_quantity == "reflectance_db" and target_quantity == "reflectance":
        return [
            [float(10.0 ** (value / 10.0)) for value in curve]
            for curve in curve_lists
        ]
    if source_quantity == "reflectance" and target_quantity == "reflectance_db":
        return [
            [float(10.0 * log10(max(value, REFLECTANCE_DB_FLOOR))) for value in curve]
            for curve in curve_lists
        ]
    return curve_lists

