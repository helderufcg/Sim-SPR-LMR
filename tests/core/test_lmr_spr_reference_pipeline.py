from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from sim_spr_lmr.application.parameter_mapper import (
    SimulationParameterInput,
    build_simulation_config,
)
from sim_spr_lmr.core.domain import FiberConfig, FiberCoreConfig, LayerConfig, SimulationConfig
from sim_spr_lmr.core.optics import (
    build_automatic_lmr_spr_result,
    detect_lmr_spr_resonances,
)
from sim_spr_lmr.presentation.plotting import build_simulation_summary
from sim_spr_lmr.core.optics.simulation_engine import (
    _lmr_spr_layer_permittivity,
    _transmitted_power_batch,
    _transmitted_power_batch_tm,
    run_simulation as _run_simulation,
)


def _reference_config() -> SimulationConfig:
    return SimulationConfig(
        simulator="LMR+SPR",
        coupling="Fiber",
        interrogation_mode="WIM",
        polarization="TM",
        layers=[
            LayerConfig("ITO", 24, 10e-9),
            LayerConfig("Silver", 12, 10e-9),
            LayerConfig("ITO", 24, 40e-9),
            LayerConfig("Analyte", -1, 0.0, is_analyte=True),
        ],
        analyte_indices=[1.32 + 0j, 1.33 + 0j],
        scan_start=0.5e-6,
        scan_stop=3.0e-6,
        scan_step=0.5e-9,
        fiber=FiberConfig(
            fiber_type="removed_cladding",
            unclad_length_m=1e-2,
            core_diameter_m=400e-6,
            numerical_aperture=0.22,
            angular_samples=300,
            power_distribution_model="guided",
            core=FiberCoreConfig(material_name="Silica"),
        ),
        response_quantity="transmission",
        resonance_strategy="lmr_spr_auto_multi_dip",
        expected_resonance_labels=(),
        resonance_windows_nm={},
        max_tracked_resonances=0,
    )


def _d_shaped_reference_config() -> SimulationConfig:
    return SimulationConfig(
        simulator="LMR+SPR",
        coupling="Fiber",
        interrogation_mode="WIM",
        polarization="TM",
        layers=[
            LayerConfig("ITO", 24, 80e-9, dispersion_model="drude"),
            LayerConfig("Analyte", -1, 0.0, is_analyte=True),
        ],
        analyte_indices=[1.33 + 0j],
        scan_start=380e-9,
        scan_stop=2500e-9,
        scan_step=0.1e-9,
        fiber=FiberConfig(
            fiber_type="d_shaped",
            unclad_length_m=10e-3,
            core_diameter_m=9e-6,
            numerical_aperture=0.12,
            angular_samples=300,
            power_distribution_model="guided",
            core=FiberCoreConfig(material_name="Silica", material_id=1),
            outer_diameter_m=125e-6,
            residual_cladding_thickness_m=1e-6,
        ),
        response_quantity="transmission",
        resonance_strategy="lmr_spr_auto_multi_dip",
        expected_resonance_labels=(),
        resonance_windows_nm={},
        max_tracked_resonances=0,
    )


class LmrSprReferencePipelineTests(unittest.TestCase):
    def test_parameter_mapper_builds_d_shaped_maurya_geometry(self):
        parameters = SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=2,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "ITO", "dispersionModel": "drude"},
                    {"material": "Analyte"},
                ],
                thicknesses_m=[80e-9, 0.0],
                analyte_indices=[1.33 + 0j],
                wim_scan_start_nm=380.0,
                wim_scan_stop_nm=2500.0,
                fiber_type_code=2,
                fiber_length_mm=10.0,
                fiber_core_diameter_um=9.0,
                fiber_outer_diameter_um=125.0,
                fiber_residual_cladding_um=1.0,
                fiber_numerical_aperture=0.12,
                fiber_core_material_id=1,
                fiber_core_material_name="Silica",
            )
        config = build_simulation_config(parameters)

        self.assertEqual(config.fiber.fiber_type, "d_shaped")
        self.assertAlmostEqual(config.fiber.outer_diameter_m, 125e-6)
        self.assertAlmostEqual(config.fiber.residual_cladding_thickness_m, 1e-6)
        self.assertEqual(config.resonance_strategy, "lmr_spr_auto_multi_dip")
        self.assertEqual(config.expected_resonance_labels, ())
        self.assertEqual(config.resonance_windows_nm, {})

        with self.assertRaisesRegex(ValueError, "core diameter"):
            build_simulation_config(
                replace(parameters, fiber_core_diameter_um=125.0)
            )

        with self.assertRaisesRegex(ValueError, "cannot exceed the fiber radius"):
            build_simulation_config(
                replace(parameters, fiber_residual_cladding_um=63.0)
            )

    def test_d_shaped_maurya_transmission_matches_reference_samples(self):
        wavelengths_nm = np.array(
            [400.0, 450.0, 500.0, 550.0, 633.0, 1600.0, 1800.0, 2000.0, 2500.0]
        )
        response = _transmitted_power_batch(
            _d_shaped_reference_config(),
            wavelengths_nm * 1e-9,
            1.33 + 0j,
        )

        np.testing.assert_allclose(
            response,
            [
                0.995479781982,
                0.950123502905,
                0.473423671297,
                0.931929844422,
                0.969957197949,
                0.564131623458,
                0.191615709206,
                0.624270983266,
                0.793475763075,
            ],
            rtol=0,
            atol=2e-10,
        )

    def test_parameter_mapper_accepts_prism_stack_for_lmr_spr(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=1,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "Silica"},
                    {"material": "ITO", "dispersionModel": "drude-lorentz"},
                    {"material": "Analyte"},
                ],
                material_ids=[1, 24, -1],
                thicknesses_m=[1e-6, 100e-9, 1e-6],
                analyte_indices=[1.321 + 0j],
                wim_incidence_angle_deg=80.0,
                wim_scan_start_nm=400.0,
                wim_scan_stop_nm=4000.0,
            )
        )

        self.assertEqual(config.coupling, "Prism")
        self.assertEqual(config.response_quantity, "reflectance_db")
        self.assertEqual(config.resonance_strategy, "lmr_spr_auto_multi_dip")
        self.assertIsNone(config.fiber)

    def test_parameter_mapper_accepts_internal_analyte_in_prism_stack(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=1,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "SF11"},
                    {"material": "Silica"},
                    {"material": "Analyte"},
                    {"material": "Custom"},
                    {"material": "Copper", "dispersionModel": "Experimental (Filmetrics)"},
                ],
                thicknesses_m=[0.0, 300e-9, 9e-9, 1e-9, 0.0],
                refractive_indices=[0j, 0j, 0j, 1.55 + 0j, 0j],
                analyte_indices=[1.43 + 0j],
                wim_incidence_angle_deg=80.0,
                wim_scan_start_nm=500.0,
                wim_scan_stop_nm=500.2,
            )
        )

        self.assertTrue(config.layers[2].is_analyte)
        self.assertEqual(config.layers[3].refractive_index, 1.55 + 0j)
        self.assertEqual(config.layers[-1].material_name, "Copper")
        result = _run_simulation(config)
        self.assertTrue(np.all(np.isfinite(result.response_curves[0])))

    def test_automatic_detection_numbers_every_significant_dip_and_uses_local_fwhm(self):
        axis_nm = list(range(12))
        curve = [1.0, 1.0, 0.8, 0.4, 0.0, 0.4, 0.8, 1.0, 0.8, 0.2, 0.8, 1.0]
        config = replace(
            _reference_config(),
            analyte_indices=[1.33 + 0j],
            resonance_strategy="lmr_spr_auto_multi_dip",
            expected_resonance_labels=(),
            resonance_windows_nm={},
        )

        self.assertEqual(detect_lmr_spr_resonances(axis_nm, curve), [4, 9])
        result = build_automatic_lmr_spr_result(config, axis_nm, [curve], 0.0)

        self.assertEqual(list(result.resonance_series), ["Resonance 1", "Resonance 2"])
        self.assertAlmostEqual(result.resonance_series["Resonance 1"]["points"][0], 4.0)
        self.assertAlmostEqual(result.resonance_series["Resonance 2"]["points"][0], 9.0)
        self.assertAlmostEqual(result.resonance_series["Resonance 1"]["fwhm"][0], 2.5)
        self.assertAlmostEqual(
            result.resonance_series["Resonance 2"]["fwhm"][0],
            4.0 / 3.0,
            places=6,
        )

        summary = build_simulation_summary(result)
        self.assertIn("Resonance Wavelength (nm) 1: [4.0]", summary)
        self.assertIn("Resonance Wavelength (nm) 2: [9.0]", summary)
        self.assertIn("FWHM (nm) 1: [2.5]", summary)

    def test_automatic_detection_reports_no_resonance_for_a_monotonic_curve(self):
        config = replace(
            _reference_config(),
            analyte_indices=[1.33 + 0j],
            resonance_strategy="lmr_spr_auto_multi_dip",
        )
        result = build_automatic_lmr_spr_result(
            config,
            [500.0, 600.0, 700.0, 800.0],
            [[1.0, 0.9, 0.8, 0.7]],
            0.0,
        )

        self.assertEqual(result.resonance_series, {})
        self.assertIn("No resonance was detected automatically", build_simulation_summary(result))

    def test_prism_lmr_spr_matches_del_villar_db_at_633_nm(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=1,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "Silica"},
                    {"material": "ITO", "dispersionModel": "drude-lorentz"},
                    {"material": "Analyte"},
                ],
                material_ids=[1, 24, -1],
                thicknesses_m=[123e-9, 100e-9, 456e-9],
                analyte_indices=[1.321 + 0j],
                wim_incidence_angle_deg=80.0,
                wim_scan_start_nm=632.9,
                wim_scan_stop_nm=633.2,
            )
        )

        result = _run_simulation(config)

        self.assertEqual(result.response_quantity, "reflectance_db")
        self.assertAlmostEqual(result.axis_x[1], 633.0, places=6)
        self.assertAlmostEqual(result.response_curves[0][1], -0.1811114025, places=6)

    def test_parameter_mapper_preserves_ito_drude_lorentz_selection(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=2,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "ITO", "dispersionModel": "drude-lorentz"},
                    {"material": "Analyte"},
                ],
                thicknesses_m=[100e-9, 0.0],
                analyte_indices=[1.321 + 0j],
                wim_scan_start_nm=500.0,
                wim_scan_stop_nm=3000.0,
                fiber_type_code=1,
                fiber_length_mm=10.0,
                fiber_core_diameter_um=400.0,
                fiber_numerical_aperture=0.22,
                fiber_core_material_name="Silica",
            )
        )

        self.assertEqual(config.layers[0].dispersion_model, "drude-lorentz")

    def test_parameter_mapper_accepts_swcnt_drude_lorentz_layer(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=2,
                interrogation_mode=2,
                polarization="TM",
                layer_rows=[
                    {"material": "SWCNT", "dispersionModel": "drude-lorentz"},
                    {"material": "Analyte"},
                ],
                thicknesses_m=[4e-9, 0.0],
                analyte_indices=[1.33 + 0j],
                wim_scan_start_nm=500.0,
                wim_scan_stop_nm=3500.0,
                fiber_type_code=1,
                fiber_length_mm=10.0,
                fiber_core_diameter_um=400.0,
                fiber_numerical_aperture=0.22,
                fiber_core_material_name="Silica",
            )
        )

        self.assertEqual(config.layers[0].material_id, 26)
        self.assertEqual(config.layers[0].dispersion_model, "drude-lorentz")

    def test_lmr_spr_engine_uses_selected_ito_drude_lorentz_model(self):
        wavelengths = np.array([633e-9])
        standard = _lmr_spr_layer_permittivity(
            LayerConfig("ITO", 24, 100e-9),
            wavelengths,
        )
        drude_lorentz = _lmr_spr_layer_permittivity(
            LayerConfig("ITO", 24, 100e-9, dispersion_model="drude-lorentz"),
            wavelengths,
        )

        self.assertFalse(np.allclose(standard, drude_lorentz))
        np.testing.assert_allclose(
            np.sqrt(drude_lorentz),
            [1.9620218647 + 0.0076554750j],
            rtol=0,
            atol=1e-9,
        )

    def test_lmr_spr_engine_uses_mishra_swcnt_drude_lorentz_model(self):
        permittivity = _lmr_spr_layer_permittivity(
            LayerConfig("SWCNT", 26, 4e-9, dispersion_model="drude-lorentz"),
            np.array([633e-9]),
        )

        np.testing.assert_allclose(
            np.sqrt(permittivity),
            [1.2201927743 + 0.2341688554j],
            rtol=0,
            atol=1e-9,
        )

    def test_parameter_mapper_accepts_two_layer_te_stack_for_lmr_spr(self):
        config = build_simulation_config(
            SimulationParameterInput(
                simulator="LMR+SPR",
                coupling_mode=2,
                interrogation_mode=2,
                polarization="TE",
                layer_rows=[
                    {"material": "Silver"},
                    {"material": "Analyte"},
                ],
                thicknesses_m=[10e-9, 0.0],
                analyte_indices=[1.32 + 0j],
                wim_scan_start_nm=500.0,
                wim_scan_stop_nm=3000.0,
                fiber_type_code=1,
                fiber_length_mm=10.0,
                fiber_core_diameter_um=400.0,
                fiber_numerical_aperture=0.22,
                fiber_core_material_name="Silica",
            )
        )

        self.assertEqual(config.polarization, "TE")
        self.assertEqual(len(config.layers), 2)
        self.assertEqual(config.resonance_strategy, "lmr_spr_auto_multi_dip")
        self.assertEqual(config.expected_resonance_labels, ())

    def test_vectorized_ito_ag_ito_transmission_matches_reference_samples(self):
        response = _transmitted_power_batch_tm(
            _reference_config(),
            np.array([0.5e-6, 0.9e-6, 1.3e-6, 1.8e-6, 3.0e-6]),
            1.32 + 0j,
        )

        np.testing.assert_allclose(
            response,
            [0.62655797, 0.65588656, 0.43821840, 0.33453201, 0.35977431],
            rtol=0,
            atol=1e-8,
        )

    def test_vectorized_ito_ag_ito_supports_te_polarization(self):
        config = _reference_config()
        config.polarization = "TE"

        response = _transmitted_power_batch(
            config,
            np.array([0.5e-6, 0.9e-6, 1.3e-6, 1.8e-6, 3.0e-6]),
            1.32 + 0j,
        )

        np.testing.assert_allclose(
            response,
            [0.95876257, 0.97227868, 0.97373388, 0.97389579, 0.97315855],
            rtol=0,
            atol=1e-8,
        )

if __name__ == "__main__":
    unittest.main()
