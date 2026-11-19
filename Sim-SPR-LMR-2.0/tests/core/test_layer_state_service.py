from __future__ import annotations

import unittest

from sim_spr_lmr.application.layer_state_service import (
    LayerFormInput,
    LayerStateSnapshot,
    append_layer,
)


class LayerStateServiceTests(unittest.TestCase):
    def test_graphene_layer_keeps_subnanometer_thickness_without_manual_index(self):
        for mode in ("AIM", "WIM"):
            with self.subTest(mode=mode):
                state = append_layer(
                    LayerStateSnapshot(),
                    LayerFormInput(
                        material_name="Graphene",
                        material_id=33,
                        thickness_text="0.34",
                        description="",
                        interrogation_mode=mode,
                    ),
                )
                self.assertAlmostEqual(state.thicknesses_m[0], 0.34e-9)
                self.assertEqual(state.refractive_indices[0], 0j)

    def test_wim_custom_layer_accepts_n_and_defaults_empty_kappa_to_zero(self):
        state = append_layer(
            LayerStateSnapshot(),
            LayerFormInput(
                material_name="Custom",
                material_id=-1,
                thickness_text="9",
                description="",
                interrogation_mode="WIM",
                real_part_text="1.43",
                imaginary_part_text="",
            ),
        )

        self.assertEqual(state.refractive_indices, [1.43 + 0j])
        self.assertEqual(state.layers[0]["refractiveIndex"].strip(), "1.43+0j")

    def test_wim_custom_layer_preserves_nonzero_kappa(self):
        state = append_layer(
            LayerStateSnapshot(),
            LayerFormInput(
                material_name="Custom",
                material_id=-1,
                thickness_text="1",
                description="",
                interrogation_mode="WIM",
                real_part_text="1.55",
                imaginary_part_text="0.002",
            ),
        )

        self.assertEqual(state.refractive_indices, [1.55 + 0.002j])


if __name__ == "__main__":
    unittest.main()
