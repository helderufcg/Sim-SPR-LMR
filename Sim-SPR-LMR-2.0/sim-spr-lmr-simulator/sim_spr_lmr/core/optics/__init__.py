"""Optical models and transfer-matrix based solvers.

This is the main entry point for the numerical pipeline: raw physics lives in
``transfer_matrix`` and the higher-level execution flow lives in
``simulation_engine``.
"""

from .post_processing import (
    build_automatic_lmr_spr_result,
    build_simulation_result,
    calculate_fwhm,
    calculate_fwhm_at_index,
    calculate_resonance_point,
    calculate_sensitivity,
    classify_lmr_spr_resonances,
    detect_lmr_spr_resonances,
    find_local_minima,
)
from .simulation_engine import run_simulation
from .resonance_tracking import track_resonances_by_continuity
from .transfer_matrix import calculate_reflectance
from .response_scale import (
    REFLECTANCE_SCALE_DB,
    REFLECTANCE_SCALE_LINEAR,
    convert_response_curves,
    effective_response_quantity,
)

__all__ = [
    "build_automatic_lmr_spr_result",
    "build_simulation_result",
    "calculate_fwhm",
    "calculate_fwhm_at_index",
    "calculate_reflectance",
    "REFLECTANCE_SCALE_DB",
    "REFLECTANCE_SCALE_LINEAR",
    "convert_response_curves",
    "effective_response_quantity",
    "calculate_resonance_point",
    "calculate_sensitivity",
    "classify_lmr_spr_resonances",
    "detect_lmr_spr_resonances",
    "find_local_minima",
    "run_simulation",
    "track_resonances_by_continuity",
]
