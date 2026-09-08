from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from sim_spr_lmr.application.parameter_mapper import (
    SimulationParameterInput,
    build_simulation_config,
)
from sim_spr_lmr.application.simulation_validation import (
    validate_simulation_parameter_input,
)
from sim_spr_lmr.core.optics import run_simulation
from sim_spr_lmr.presentation.qt.controllers.navigation_controller import (
    NavigationController,
)


class _WidgetRecorder:
    def __init__(self) -> None:
        self.enabled: bool | None = None
        self.text = ""
        self.current_widget = None

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def setText(self, text: str) -> None:
        self.text = text

    def setCurrentWidget(self, widget: object) -> None:
        self.current_widget = widget

    def setChecked(self, checked: bool) -> None:
        self.checked = checked


def _fiber_parameters(simulator: str) -> SimulationParameterInput:
    coating = "Silver" if simulator == "SPR" else "ITO"
    return SimulationParameterInput(
        simulator=simulator,
        coupling_mode=2,
        interrogation_mode=2,
        polarization="TM",
        layer_rows=[
            {"material": coating},
            {"material": "Analyte"},
        ],
        thicknesses_m=[40e-9, 0.0],
        analyte_indices=[1.33 + 0j],
        wim_incidence_angle_deg=0.0,
        wim_scan_start_nm=500.0,
        wim_scan_stop_nm=500.2,
        fiber_type_code=1,
        fiber_length_mm=10.0,
        fiber_core_diameter_um=400.0,
        fiber_numerical_aperture=0.22,
        fiber_core_material_id=1,
        fiber_core_material_name="Silica",
    )


class FiberCompatibilityTests(unittest.TestCase):
    def test_optical_fiber_always_opens_the_fiber_configuration_page(self) -> None:
        select_fiber_page = object()
        d_shaped_page = object()
        state = SimpleNamespace(fiber_type_code=2)
        window = SimpleNamespace(
            Stacked_windows=_WidgetRecorder(),
            session_state=state,
            select_fiber_window=select_fiber_page,
            d_shaped_characteristics=d_shaped_page,
            cladding_remove_btn=_WidgetRecorder(),
            d_shaped_fiber_btn=_WidgetRecorder(),
            warning_fiber_typ=_WidgetRecorder(),
        )

        NavigationController(window)._next_from_coupling(2, _WidgetRecorder())

        self.assertIs(window.Stacked_windows.current_widget, select_fiber_page)
        self.assertEqual(state.fiber_type_code, 0)

    def test_each_fiber_type_opens_its_own_characteristics_page(self) -> None:
        multimode_page = object()
        d_shaped_page = object()
        window = SimpleNamespace(
            Stacked_windows=_WidgetRecorder(),
            characteristics_fiber=multimode_page,
            d_shaped_characteristics=d_shaped_page,
        )
        controller = NavigationController(window)

        controller._next_from_select_fiber(1, _WidgetRecorder())
        self.assertIs(window.Stacked_windows.current_widget, multimode_page)

        controller._next_from_select_fiber(2, _WidgetRecorder())
        self.assertIs(window.Stacked_windows.current_widget, d_shaped_page)

    def test_d_shaped_characteristics_returns_to_fiber_type_page(self) -> None:
        d_shaped_page = object()
        select_fiber_page = object()
        window = SimpleNamespace(
            Stacked_windows=_WidgetRecorder(),
            Select_simulator=object(),
            home_window=object(),
            coupling_window=object(),
            interrogation_window=object(),
            layers_window=object(),
            d_shaped_characteristics=d_shaped_page,
            select_fiber_window=select_fiber_page,
            interval_setting=object(),
            characteristics_fiber=object(),
        )
        window.Stacked_windows.currentWidget = lambda: d_shaped_page

        NavigationController(window).previous_page()

        self.assertIs(window.Stacked_windows.current_widget, select_fiber_page)

    def test_navigation_enables_multimode_fiber_for_spr_and_lmr(self) -> None:
        simulator_selections = (("spr_selected", "SPR"), ("lmr_selected", "LMR"))
        for selection_method, simulator in simulator_selections:
            with self.subTest(simulator=simulator):
                coupling_page = object()
                footer = _WidgetRecorder()
                window = SimpleNamespace(
                    Stacked_windows=_WidgetRecorder(),
                    coupling_window=coupling_page,
                    session_state=SimpleNamespace(simulator=""),
                    aim_btn=_WidgetRecorder(),
                    wim_btn=_WidgetRecorder(),
                    label_title=_WidgetRecorder(),
                    label_footer=footer,
                )
                controller = NavigationController(window)
                coupling_options: dict[str, bool] = {}
                controller.configure_coupling_options = (
                    lambda **options: coupling_options.update(options)
                )
                controller.configure_wim_controls_for_simulator = lambda: None

                getattr(controller, selection_method)()

                self.assertEqual(window.session_state.simulator, simulator)
                self.assertIs(window.Stacked_windows.current_widget, coupling_page)
                self.assertTrue(coupling_options["allow_prism"])
                self.assertTrue(coupling_options["allow_fiber"])
                self.assertIn("v02.0_a", footer.text)

    def test_mapper_builds_fiber_transmission_for_spr_and_lmr(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                config = build_simulation_config(_fiber_parameters(simulator))

                self.assertEqual(config.simulator, simulator)
                self.assertEqual(config.coupling, "Fiber")
                self.assertEqual(config.interrogation_mode, "WIM")
                self.assertEqual(config.response_quantity, "transmission")
                self.assertEqual(config.resonance_strategy, "single_dip")
                self.assertIsNotNone(config.fiber)
                self.assertEqual(config.fiber.fiber_type, "removed_cladding")

    def test_validation_does_not_require_prism_incidence_angle_for_fiber(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                config = validate_simulation_parameter_input(_fiber_parameters(simulator))
                self.assertIsNone(config.incidence_wavelength_m)
                self.assertEqual(config.response_quantity, "transmission")

    def test_fiber_rejects_angular_interrogation(self) -> None:
        parameters = _fiber_parameters("SPR")
        parameters.interrogation_mode = 1
        parameters.aim_incidence_wavelength_nm = 633.0
        parameters.aim_scan_start_deg = 40.0
        parameters.aim_scan_stop_deg = 80.0

        with self.assertRaisesRegex(
            ValueError,
            "requires wavelength interrogation mode",
        ):
            build_simulation_config(parameters)

    def test_engine_runs_multimode_transmission_for_spr_and_lmr(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                config = validate_simulation_parameter_input(_fiber_parameters(simulator))
                result = run_simulation(config)

                self.assertEqual(result.simulator, simulator)
                self.assertEqual(result.response_quantity, "transmission")
                self.assertEqual(len(result.axis_x), 3)
                self.assertEqual(len(result.reflectance_curves), 1)
                self.assertTrue(np.isfinite(result.reflectance_curves).all())

    def test_unpolarized_fiber_averages_complete_te_and_tm_transmissions(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                parameters = _fiber_parameters(simulator)

                parameters.polarization = "TE"
                te_result = run_simulation(validate_simulation_parameter_input(parameters))

                parameters.polarization = "TM"
                tm_result = run_simulation(validate_simulation_parameter_input(parameters))

                parameters.polarization = "TE+TM"
                unpolarized_config = validate_simulation_parameter_input(parameters)
                unpolarized_result = run_simulation(unpolarized_config)

                expected = (
                    np.asarray(te_result.reflectance_curves, dtype=float)
                    + np.asarray(tm_result.reflectance_curves, dtype=float)
                ) / 2.0
                np.testing.assert_allclose(
                    unpolarized_result.reflectance_curves,
                    expected,
                    rtol=1e-12,
                    atol=1e-12,
                )
                self.assertEqual(unpolarized_config.polarization, "TE+TM")
                self.assertEqual(unpolarized_result.polarization, "TE+TM")

    def test_engine_accepts_pmma_as_a_predefined_fiber_core_material(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                parameters = _fiber_parameters(simulator)
                parameters.fiber_core_material_id = None
                parameters.fiber_core_material_name = "PMMA"

                config = validate_simulation_parameter_input(parameters)
                result = run_simulation(config)

                self.assertEqual(config.fiber.core.material_name, "PMMA")
                self.assertEqual(result.response_quantity, "transmission")
                self.assertTrue(np.isfinite(result.reflectance_curves).all())

    def test_validation_rejects_caf2_as_a_predefined_fiber_core(self) -> None:
        parameters = _fiber_parameters("LMR")
        parameters.fiber_core_material_id = None
        parameters.fiber_core_material_name = "CaF₂"

        with self.assertRaisesRegex(ValueError, "supports Silica and PMMA"):
            validate_simulation_parameter_input(parameters)

    def test_engine_runs_restored_chromium_and_fto_coatings(self) -> None:
        for simulator in ("SPR", "LMR"):
            for coating_material in ("Chromium", "FTO"):
                with self.subTest(simulator=simulator, coating=coating_material):
                    parameters = _fiber_parameters(simulator)
                    parameters.layer_rows[0]["material"] = coating_material

                    config = validate_simulation_parameter_input(parameters)
                    result = run_simulation(config)

                    self.assertEqual(config.layers[0].material_name, coating_material)
                    self.assertEqual(result.response_quantity, "transmission")
                    self.assertTrue(np.isfinite(result.reflectance_curves).all())

    def test_engine_accepts_caf2_as_a_fiber_coating_layer(self) -> None:
        for simulator in ("SPR", "LMR"):
            with self.subTest(simulator=simulator):
                parameters = _fiber_parameters(simulator)
                parameters.layer_rows[0]["material"] = "CaF₂"

                config = validate_simulation_parameter_input(parameters)
                result = run_simulation(config)

                self.assertEqual(config.layers[0].material_name, "CaF₂")
                self.assertEqual(config.layers[0].material_id, 31)
                self.assertEqual(result.response_quantity, "transmission")
                self.assertTrue(np.isfinite(result.reflectance_curves).all())


if __name__ == "__main__":
    unittest.main()
