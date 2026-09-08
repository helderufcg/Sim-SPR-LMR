from __future__ import annotations

import unittest

import numpy as np

from sim_spr_lmr.core.optics import calculate_reflectance
from sim_spr_lmr.core.optics.simulation_engine import (
    _calculate_selected_polarization_reflectance,
)


class TransferMatrixTests(unittest.TestCase):
    def test_normal_incidence_interface_reflectance_matches_fresnel_limit(self):
        reflectance = calculate_reflectance(
            layer_indices=[1.0 + 0j, 1.5 + 0j],
            layer_thicknesses_m=[0.0, 0.0],
            incidence_angle_rad=0.0,
            wavelength_m=633e-9,
            polarization="TE",
        )

        self.assertAlmostEqual(reflectance, 0.04)

    def test_calculate_reflectance_rejects_invalid_layer_shapes(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            calculate_reflectance(
                layer_indices=[1.0 + 0j, 1.5 + 0j],
                layer_thicknesses_m=[0.0],
                incidence_angle_rad=0.0,
                wavelength_m=633e-9,
                polarization="TE",
            )

    def test_calculate_reflectance_rejects_unknown_polarization(self):
        with self.assertRaisesRegex(ValueError, "Polarization"):
            calculate_reflectance(
                layer_indices=[1.0 + 0j, 1.5 + 0j],
                layer_thicknesses_m=[0.0, 0.0],
                incidence_angle_rad=0.0,
                wavelength_m=633e-9,
                polarization="BAD",
            )

    def test_unpolarized_reflectance_is_equal_power_te_tm_average(self):
        optical_stack = {
            "layer_indices": [1.515 + 0j, 0.18 + 3.42j, 1.33 + 0j],
            "layer_thicknesses_m": [0.0, 50e-9, 0.0],
            "incidence_angle_rad": np.deg2rad(68.0),
            "wavelength_m": 633e-9,
        }
        reflectance_te = _calculate_selected_polarization_reflectance(
            **optical_stack,
            polarization="TE",
        )
        reflectance_tm = _calculate_selected_polarization_reflectance(
            **optical_stack,
            polarization="TM",
        )
        reflectance_unpolarized = _calculate_selected_polarization_reflectance(
            **optical_stack,
            polarization="TE+TM",
        )

        self.assertAlmostEqual(
            reflectance_unpolarized,
            (reflectance_te + reflectance_tm) / 2.0,
            places=14,
        )


if __name__ == "__main__":
    unittest.main()
