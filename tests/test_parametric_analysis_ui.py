from __future__ import annotations

import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore, QtWidgets

from sim_spr_lmr.core.domain import (
    LayerConfig,
    ParametricAnalysisResult,
    ParametricResonanceTrack,
    SimulationConfig,
)
from sim_spr_lmr.presentation.qt.dialogs import ParametricAnalysisWindow


LAYERS = [
    {"material": "BK7", "description": "Prism"},
    {"material": "Gold", "description": "Coating"},
    {"material": "Analyte", "description": "Analyte"},
]
THICKNESSES = [0.0, 50e-9, 0.0]


class ParametricAnalysisUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def make_window(self, *, coupling: str = "Prism", mode: str = "WIM"):
        window = ParametricAnalysisWindow(
            layers=LAYERS,
            thicknesses_m=THICKNESSES,
            analyte_indices=[1.33 + 0j, 1.34 + 0j],
            coupling=coupling,
            interrogation_mode=mode,
            incidence_angle_deg=62.5,
        )
        self.addCleanup(window.close)
        return window

    @staticmethod
    def simulation_config() -> SimulationConfig:
        return SimulationConfig(
            simulator="LMR+SPR",
            coupling="Prism",
            interrogation_mode="WIM",
            polarization="TM",
            layers=[
                LayerConfig("BK7", 1, 0.0, 1.5 + 0j),
                LayerConfig("Gold", 4, 50e-9, 0.2 + 3j),
                LayerConfig("Analyte", -1, 0.0, 1.33 + 0j, is_analyte=True),
            ],
            analyte_indices=[1.33 + 0j],
        )

    @staticmethod
    def analysis_result() -> ParametricAnalysisResult:
        track = ParametricResonanceTrack(
            label="Resonance 1",
            positions=[500.0, 510.0],
            fwhm=[10.0, 11.0],
            minimum_response=[0.1, 0.2],
            sensitivity=[1.0, 1.0],
            quality_factor=[0.1, 1.0 / 11.0],
        )
        return ParametricAnalysisResult(
            simulator="LMR+SPR",
            coupling="Prism",
            interrogation_mode="WIM",
            polarization="TM",
            response_quantity="reflectance",
            fixed_analyte_index=1.33 + 0j,
            parameter_kind="thickness",
            parameter_name="Layer thickness",
            parameter_unit="nm",
            parameter_values=[50.0, 60.0],
            response_axis=[400.0, 500.0, 600.0],
            response_axis_label="Wavelength",
            response_axis_unit="nm",
            response_curves=[[0.8, 0.1, 0.9], [0.9, 0.2, 0.8]],
            resonance_tracks=[track],
        )

    def test_window_exposes_requested_controls_and_output_areas(self) -> None:
        window = self.make_window()

        self.assertEqual(window.parameter_selector.count(), 2)
        self.assertEqual(window.parameter_selector.itemText(0), "Layer thickness")
        self.assertEqual(window.parameter_selector.itemText(1), "Incidence angle")
        self.assertEqual(window.output_tabs.count(), 3)
        self.assertEqual(window.output_tabs.tabText(0), "Spectra")
        self.assertIn("FWHM", window.output_tabs.tabText(1))
        self.assertEqual(window.output_tabs.tabText(2), "Sensitivity and FOM")
        self.assertEqual(window.output_tabs.tabBar().elideMode(), QtCore.Qt.ElideNone)
        self.assertFalse(window.output_tabs.tabBar().usesScrollButtons())
        self.assertEqual(window.spectra_tab.layout().contentsMargins().left(), 18)
        self.assertEqual(window.metrics_tab.layout().contentsMargins().left(), 18)
        self.assertEqual(window.sensitivity_tab.layout().contentsMargins().left(), 18)
        window.show()
        self.app.processEvents()
        tab_bar = window.output_tabs.tabBar()
        for index in range(tab_bar.count()):
            with self.subTest(tab=index):
                text_width = tab_bar.fontMetrics().horizontalAdvance(tab_bar.tabText(index))
                self.assertGreaterEqual(tab_bar.tabRect(index).width(), text_width + 36)
        self.assertFalse(window.run_button.isEnabled())
        self.assertIn("conventional simulation", window.run_button.toolTip())
        self.assertIn("reuses its optical configuration", window.run_button.toolTip())
        self.assertFalse(window.export_button.isEnabled())

    def test_thickness_selector_excludes_prism_and_analyte(self) -> None:
        window = self.make_window()

        self.assertEqual(window.layer_selector.count(), 1)
        self.assertIn("Gold", window.layer_selector.currentText())
        self.assertAlmostEqual(window.initial_value.value(), 50.0)
        self.assertAlmostEqual(window.final_value.value(), 60.0)
        self.assertEqual(window.initial_value.suffix(), " nm")
        self.assertEqual(window.initial_value.decimals(), 2)
        self.assertEqual(window.final_value.decimals(), 2)
        self.assertEqual(window.step_value.decimals(), 2)

    def test_angle_is_available_only_for_prism_wim(self) -> None:
        prism_wim = self.make_window()
        self.assertTrue(prism_wim.parameter_selector.model().item(1).isEnabled())
        prism_wim.parameter_selector.setCurrentIndex(1)
        self.assertEqual(prism_wim.initial_value.suffix(), " °")
        self.assertAlmostEqual(prism_wim.initial_value.value(), 62.5)
        self.assertTrue(prism_wim.layer_selector.isHidden())
        self.assertEqual(
            [axes.get_xlabel() for axes in prism_wim.metrics_figure.axes],
            ["Incidence angle (°)", "Incidence angle (°)"],
        )
        self.assertEqual(
            [axes.get_title() for axes in prism_wim.metrics_figure.axes],
            ["Resonance position vs. Incidence angle", "FWHM vs. Incidence angle"],
        )
        self.assertEqual(
            [axes.get_xlabel() for axes in prism_wim.sensitivity_figure.axes],
            ["Incidence angle (°)", "Incidence angle (°)"],
        )
        self.assertEqual(
            [axes.get_title() for axes in prism_wim.sensitivity_figure.axes],
            ["Sensitivity vs. Incidence angle", "Figure of merit vs. Incidence angle"],
        )

        fiber_wim = self.make_window(coupling="Fiber")
        self.assertFalse(fiber_wim.parameter_selector.model().item(1).isEnabled())
        self.assertEqual(fiber_wim.parameter_selector.currentData(), fiber_wim.THICKNESS)

        prism_aim = self.make_window(mode="AIM")
        self.assertFalse(prism_aim.parameter_selector.model().item(1).isEnabled())
        self.assertEqual(prism_aim.spectra_figure.axes[0].get_xlabel(), "Incidence angle (°)")

    def test_analyte_values_are_presented_as_fixed_choices(self) -> None:
        window = self.make_window()

        self.assertEqual(window.analyte_selector.count(), 2)
        self.assertEqual(window.analyte_selector.itemText(0), "1.33 RIU")
        self.assertEqual(window.analyte_selector.itemText(1), "1.34 RIU")

    def test_valid_base_config_enables_run_and_result_renders_all_tabs(self) -> None:
        window = self.make_window()
        window.refresh_context(
            layers=LAYERS,
            thicknesses_m=THICKNESSES,
            analyte_indices=[1.33 + 0j],
            analyte_step=0.01,
            coupling="Prism",
            interrogation_mode="WIM",
            incidence_angle_deg=62.5,
            simulation_config=self.simulation_config(),
        )
        self.assertTrue(window.run_button.isEnabled())
        self.assertIn("next conventional analyte step", window.run_button.toolTip())

        result = self.analysis_result()
        window._handle_analysis_completed(result)

        self.assertEqual(len(window.spectra_figure.axes[0].lines), 2)
        self.assertEqual(len(window.spectra_figure.axes), 2)
        self.assertEqual(
            window.spectra_figure.axes[1].get_ylabel(),
            "Layer thickness (nm)",
        )
        self.assertGreaterEqual(window.spectra_figure.axes[0].title.get_fontsize(), 13)
        self.assertGreaterEqual(
            window.spectra_figure.axes[0].xaxis.label.get_fontsize(),
            11,
        )
        self.assertGreaterEqual(
            window.spectra_figure.axes[0].get_xticklabels()[0].get_fontsize(),
            10,
        )
        self.assertEqual(len(window.metrics_figure.axes[0].lines), 1)
        self.assertEqual(len(window.sensitivity_figure.axes[1].lines), 1)
        self.assertEqual(
            window.sensitivity_figure.axes[0].get_ylabel(),
            "Sensitivity (nm/RIU)",
        )
        self.assertTrue(window.export_button.isEnabled())

    def test_run_button_executes_worker_and_publishes_result(self) -> None:
        window = self.make_window()
        window.refresh_context(
            layers=LAYERS,
            thicknesses_m=THICKNESSES,
            analyte_indices=[1.33 + 0j],
            analyte_step=0.01,
            coupling="Prism",
            interrogation_mode="WIM",
            incidence_angle_deg=62.5,
            simulation_config=self.simulation_config(),
        )
        expected_result = self.analysis_result()
        with patch(
            "sim_spr_lmr.presentation.qt.dialogs.parametric_analysis_window.run_parametric_analysis",
            return_value=expected_result,
        ):
            window.run_button.click()
            deadline = time.monotonic() + 3.0
            while window._worker_thread is not None and time.monotonic() < deadline:
                self.app.processEvents()

        self.assertIsNone(window._worker_thread)
        self.assertIs(window._analysis_result, expected_result)
        self.assertTrue(window.export_button.isEnabled())
        self.assertEqual(window.progress_bar.value(), 100)


if __name__ == "__main__":
    unittest.main()
