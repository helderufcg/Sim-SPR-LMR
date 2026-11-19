"""
python tests/previews/parametric_analysis_preview.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
from PyQt5 import QtCore, QtWidgets


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "sim-spr-lmr-simulator"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from sim_spr_lmr.core.domain import (  # noqa: E402
    LayerConfig,
    ParametricAnalysisResult,
    ParametricResonanceTrack,
    SimulationConfig,
)
from sim_spr_lmr.presentation.qt.dialogs import ParametricAnalysisWindow  # noqa: E402


LAYERS = [
    {"material": "ITO", "description": "Coating"},
    {"material": "Analyte", "description": "Analyte"},
]
THICKNESSES_M = [50e-9, 0.0]
ANALYTE_INDICES = [1.33 + 0j]
ANALYTE_STEP = 0.01


def build_preview_window() -> ParametricAnalysisWindow:
    """Build the real dialog and populate it with deterministic fake results."""

    config = SimulationConfig(
        simulator="LMR+SPR",
        coupling="Fiber",
        interrogation_mode="WIM",
        polarization="TM",
        layers=[
            LayerConfig("ITO", 5, 50e-9, 1.9 + 0.02j),
            LayerConfig("Analyte", -1, 0.0, 1.33 + 0j, is_analyte=True),
        ],
        analyte_indices=list(ANALYTE_INDICES),
        scan_start=400e-9,
        scan_stop=1_200e-9,
        scan_step=1e-9,
        response_quantity="transmission",
        resonance_strategy="lmr_spr_auto_multi_dip",
    )
    window = ParametricAnalysisWindow(
        layers=LAYERS,
        thicknesses_m=THICKNESSES_M,
        analyte_indices=ANALYTE_INDICES,
        analyte_step=ANALYTE_STEP,
        coupling="Fiber",
        interrogation_mode="WIM",
        incidence_angle_deg=None,
        simulation_config=config,
    )
    window._handle_analysis_completed(_synthetic_result())
    return window


def _synthetic_result() -> ParametricAnalysisResult:
    parameter_values = [10.0, 20.0, 30.0]
    wavelength = np.linspace(400.0, 1_200.0, 401)
    resonance_positions = [930.0, 850.0, 780.0]
    spectra = [
        _synthetic_spectrum(wavelength, resonance_position, width)
        for resonance_position, width in zip(
            resonance_positions,
            [95.0, 85.0, 75.0],
            strict=False,
        )
    ]
    tracks = [
        ParametricResonanceTrack(
            label="Resonance 1",
            positions=[505.0, 508.0, 511.0],
            fwhm=[24.0, 23.0, 22.0],
            minimum_response=[0.32, 0.30, 0.28],
            sensitivity=[120.0, 125.0, 130.0],
            quality_factor=[5.0, 5.43, 5.91],
        ),
        ParametricResonanceTrack(
            label="Resonance 2",
            positions=[670.0, 700.0, 735.0],
            fwhm=[58.0, 55.0, 52.0],
            minimum_response=[0.20, 0.18, 0.16],
            sensitivity=[310.0, 325.0, 340.0],
            quality_factor=[5.34, 5.91, 6.54],
        ),
        ParametricResonanceTrack(
            label="Resonance 3",
            positions=[930.0, 850.0, 780.0],
            fwhm=[95.0, 85.0, 75.0],
            minimum_response=[0.12, 0.10, 0.08],
            sensitivity=[460.0, 475.0, 490.0],
            quality_factor=[4.84, 5.59, 6.53],
        ),
    ]
    return ParametricAnalysisResult(
        simulator="LMR+SPR",
        coupling="Fiber",
        interrogation_mode="WIM",
        polarization="TM",
        response_quantity="transmission",
        fixed_analyte_index=1.33 + 0j,
        parameter_kind="thickness",
        parameter_name="Layer thickness",
        parameter_unit="nm",
        parameter_values=parameter_values,
        varied_layer_index=0,
        varied_layer_name="ITO",
        response_axis=wavelength.tolist(),
        response_axis_label="Wavelength",
        response_axis_unit="nm",
        response_curves=[curve.tolist() for curve in spectra],
        resonance_tracks=tracks,
        runtime_seconds=0.42,
    )


def _synthetic_spectrum(
    wavelength: np.ndarray,
    resonance_position: float,
    width: float,
) -> np.ndarray:
    broad_dip = 0.78 * np.exp(-0.5 * ((wavelength - resonance_position) / width) ** 2)
    secondary_dip = 0.30 * np.exp(-0.5 * ((wavelength - 610.0) / 38.0) ** 2)
    return np.clip(0.96 - broad_dip - secondary_dip, 0.0, 1.0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Render the window briefly and exit without user interaction.",
    )
    arguments = parser.parse_args()

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = build_preview_window()
    window.show()
    if arguments.smoke_test:
        QtCore.QTimer.singleShot(150, application.quit)
    return int(application.exec_())


if __name__ == "__main__":
    raise SystemExit(main())
