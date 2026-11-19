from __future__ import annotations

import unittest

from sim_spr_lmr.core.domain import SimulationConfig
from sim_spr_lmr.core.optics import (
    build_simulation_result,
    calculate_fwhm,
    calculate_resonance_point,
    calculate_sensitivity,
    find_local_minima,
)


class PostProcessingTests(unittest.TestCase):
    def test_resonance_point_returns_axis_position_of_dominant_dip(self):
        axis_x = [0.0, 1.0, 2.0, 3.0]
        curve = [0.9, 0.4, 0.1, 0.5]

        self.assertEqual(calculate_resonance_point(axis_x, curve, "WIM"), 2.0)

    def test_fwhm_uses_half_depth_crossings_around_dip(self):
        axis_x = [0.0, 1.0, 2.0, 3.0, 4.0]
        curve = [1.0, 0.5, 0.0, 0.5, 1.0]

        self.assertAlmostEqual(calculate_fwhm(curve, axis_x, "WIM"), 2.0)

    def test_single_dip_fwhm_matches_v1_asymmetric_baseline_selection(self):
        axis_x = [0.0, 1.0, 2.0, 3.0, 4.0]
        curve = [0.8, 0.4, 0.1, 0.6, 1.0]

        self.assertAlmostEqual(calculate_fwhm(curve, axis_x, "WIM"), 2.275)

    def test_single_dip_fwhm_matches_v1_last_two_crossings(self):
        axis_x = list(range(9))
        curve = [1.0, 0.45, 0.05, 0.45, 1.0, 0.7, 0.3, 0.7, 1.0]

        self.assertAlmostEqual(calculate_fwhm(curve, axis_x, "WIM"), 1.125)

    def test_sensitivity_reuses_first_computed_delta_for_initial_sample(self):
        sensitivity = calculate_sensitivity(
            resonance_points=[600.0, 610.0, 625.0],
            analyte_indices=[1.33 + 0j, 1.34 + 0j, 1.35 + 0j],
        )

        self.assertEqual(sensitivity, [1000.0, 1000.0, 1500.0])

    def test_find_local_minima_detects_strict_and_plateau_dips(self):
        minima = find_local_minima([0, 1, 2, 3, 4], [1.0, 0.3, 0.3, 0.8, 0.9])

        self.assertEqual(minima, [1, 2])

    def test_build_simulation_result_populates_primary_metrics(self):
        config = SimulationConfig(
            simulator="SPR",
            coupling="prism",
            interrogation_mode="WIM",
            polarization="TM",
            analyte_indices=[1.33 + 0j, 1.34 + 0j],
        )

        result = build_simulation_result(
            config=config,
            axis_x=[600.0, 610.0, 620.0, 630.0, 640.0],
            reflectance_curves=[
                [1.0, 0.5, 0.1, 0.5, 1.0],
                [1.0, 0.6, 0.2, 0.1, 0.4],
            ],
            runtime_seconds=0.25,
        )

        self.assertEqual(result.axis_label, "Wavelength")
        self.assertEqual(result.axis_unit, "nm")
        self.assertEqual(result.resonance_points, [620.0, 630.0])
        self.assertEqual(result.minimum_reflectance, [0.1, 0.1])
        self.assertAlmostEqual(result.runtime_seconds, 0.25)


if __name__ == "__main__":
    unittest.main()
