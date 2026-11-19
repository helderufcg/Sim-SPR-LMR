from __future__ import annotations

import unittest

from sim_spr_lmr.core.domain import FiberCoreConfig, SellmeierCoefficients
from sim_spr_lmr.core.materials import dispersion_models as material_models
from sim_spr_lmr.core.materials import (
    calculate_configured_refractive_index,
    calculate_fiber_core_index,
    calculate_refractive_index,
    calculate_sellmeier_refractive_index,
    default_drude_parameters_for_material,
    material_supports_drude_override,
    material_supports_filmetrics_experimental,
    material_uses_builtin_drude,
    material_uses_builtin_drude_lorentz,
    resolve_material_id,
)


class MaterialsTests(unittest.TestCase):
    def test_resolve_material_id_keeps_legacy_catalog_ids(self):
        self.assertEqual(resolve_material_id("BK7"), 0)
        self.assertEqual(resolve_material_id("Silica"), 1)
        self.assertEqual(resolve_material_id("ITO"), 24)
        self.assertEqual(resolve_material_id("Silicon"), 25)
        self.assertEqual(resolve_material_id("Si"), 25)
        self.assertEqual(resolve_material_id("Doped SWCNT"), 26)
        self.assertEqual(resolve_material_id("SWCNT"), 26)
        self.assertEqual(resolve_material_id("Chromium"), 27)
        self.assertEqual(resolve_material_id("FTO"), 28)
        self.assertEqual(resolve_material_id("Nickel"), 29)
        self.assertEqual(resolve_material_id("Ni"), 29)
        self.assertEqual(resolve_material_id("SF11"), 30)
        self.assertEqual(resolve_material_id("Copper"), 13)
        self.assertEqual(resolve_material_id("Aluminum"), 32)
        self.assertEqual(resolve_material_id("Aluminium"), 32)
        self.assertEqual(resolve_material_id("Al"), 32)

    def test_bk7_refractive_index_at_633_nm_is_in_expected_range(self):
        refractive_index = calculate_refractive_index(resolve_material_id("BK7"), 633e-9)

        self.assertAlmostEqual(refractive_index.real, 1.5151, delta=0.002)
        self.assertAlmostEqual(refractive_index.imag, 0.0)

    def test_graphene_uses_bruna_borini_visible_dispersion(self):
        graphene_id = resolve_material_id("Graphene")
        self.assertEqual(graphene_id, 33)
        for wavelength_nm in (400, 633, 700):
            with self.subTest(wavelength_nm=wavelength_nm):
                expected = complex(3.0, (5.446 / 3.0) * wavelength_nm / 1000.0)
                self.assertAlmostEqual(
                    calculate_refractive_index(graphene_id, wavelength_nm * 1e-9).real,
                    expected.real,
                )
                self.assertAlmostEqual(
                    calculate_configured_refractive_index(
                        graphene_id, wavelength_nm * 1e-9, material_name="Graphene"
                    ).imag,
                    expected.imag,
                )

    def test_custom_sellmeier_matches_silica_catalog_near_633_nm(self):
        silica_coefficients = SellmeierCoefficients(
            b1=0.6961663,
            b2=0.4079426,
            b3=0.8974794,
            c1=4.6791e-3,
            c2=1.35121e-2,
            c3=97.934003,
        )

        custom_index = calculate_sellmeier_refractive_index(633e-9, silica_coefficients)
        catalog_index = calculate_refractive_index(resolve_material_id("Silica"), 633e-9)

        self.assertAlmostEqual(custom_index.real, catalog_index.real)
        self.assertAlmostEqual(custom_index.imag, 0.0)

    def test_nickel_matches_kumar_2023_drude_index_at_633_nm(self):
        refractive_index = calculate_refractive_index(
            resolve_material_id("Nickel"),
            633e-9,
        )

        self.assertAlmostEqual(refractive_index.real, 0.0303212665, places=9)
        self.assertAlmostEqual(refractive_index.imag, 2.2842562897, places=9)

    def test_sf11_uses_schott_sellmeier_coefficients_at_633_nm(self):
        refractive_index = calculate_refractive_index(
            resolve_material_id("SF11"),
            633e-9,
        )

        self.assertAlmostEqual(refractive_index.real, 1.7785990448, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.0)

    def test_copper_filmetrics_matches_kla_reference_at_632_8_nm(self):
        refractive_index = calculate_configured_refractive_index(
            resolve_material_id("Copper"),
            632.8e-9,
            material_name="Copper",
            dispersion_model="Experimental (Filmetrics)",
        )

        self.assertAlmostEqual(refractive_index.real, 0.2388327044, places=9)
        self.assertAlmostEqual(refractive_index.imag, 3.4156578616, places=9)

    def test_copper_filmetrics_table_is_embedded_and_complete(self):
        self.assertEqual(len(material_models.COPPER_FILMETRICS_WAVELENGTHS_NM), 121)
        self.assertEqual(len(material_models.COPPER_FILMETRICS_N), 121)
        self.assertEqual(len(material_models.COPPER_FILMETRICS_K), 121)
        self.assertEqual(material_models.COPPER_FILMETRICS_WAVELENGTHS_NM[0], 190.77)
        self.assertEqual(material_models.COPPER_FILMETRICS_WAVELENGTHS_NM[-1], 2480.0)

    def test_copper_offers_johnson_christy_or_filmetrics_experimental_data(self):
        johnson_christy_index = calculate_configured_refractive_index(
            resolve_material_id("Copper"),
            633e-9,
            material_name="Copper",
            dispersion_model="experimental",
        )
        filmetrics_index = calculate_configured_refractive_index(
            resolve_material_id("Copper"),
            633e-9,
            material_name="Copper",
            dispersion_model="experimental-filmetrics",
        )

        self.assertTrue(material_supports_filmetrics_experimental("Copper"))
        self.assertEqual(
            johnson_christy_index,
            calculate_refractive_index(resolve_material_id("Copper"), 633e-9),
        )
        self.assertNotEqual(filmetrics_index, johnson_christy_index)
        self.assertAlmostEqual(filmetrics_index.real, 0.2383144654, places=9)
        self.assertAlmostEqual(filmetrics_index.imag, 3.4184025157, places=9)

    def test_filmetrics_experimental_rejects_unsupported_material(self):
        with self.assertRaisesRegex(ValueError, "only for Copper"):
            calculate_configured_refractive_index(
                resolve_material_id("Gold"),
                633e-9,
                material_name="Gold",
                dispersion_model="Experimental (Filmetrics)",
            )

    def test_drude_override_requires_supported_material(self):
        with self.assertRaisesRegex(ValueError, "Silver, Gold, Copper"):
            calculate_configured_refractive_index(
                resolve_material_id("Chromium"),
                633e-9,
                material_name="Chromium",
                dispersion_model="drude",
                drude_lambda_p_um=0.14541,
                drude_lambda_c_um=17.614,
            )

    def test_article_drude_parameters_are_defaults_for_silver_gold_and_copper(self):
        expected_parameters = {
            "Silver": (0.14541, 17.614),
            "Gold": (0.16826, 8.9342),
            "Copper": (0.13617, 40.852),
        }

        for material_name, expected in expected_parameters.items():
            with self.subTest(material=material_name):
                self.assertTrue(material_supports_drude_override(material_name))
                self.assertEqual(
                    default_drude_parameters_for_material(material_name),
                    expected,
                )

    def test_gold_and_copper_drude_models_match_article_parameters_at_633_nm(self):
        expected_indices = {
            "Gold": (0.1378266808, 3.6195595934),
            "Copper": (0.0368729064, 4.5393462014),
        }

        for material_name, (expected_n, expected_k) in expected_indices.items():
            with self.subTest(material=material_name):
                lambda_p_um, lambda_c_um = default_drude_parameters_for_material(
                    material_name
                )
                refractive_index = calculate_configured_refractive_index(
                    resolve_material_id(material_name),
                    633e-9,
                    material_name=material_name,
                    dispersion_model="drude",
                    drude_lambda_p_um=lambda_p_um,
                    drude_lambda_c_um=lambda_c_um,
                )

                self.assertAlmostEqual(refractive_index.real, expected_n, places=9)
                self.assertAlmostEqual(refractive_index.imag, expected_k, places=9)

    def test_aluminum_uses_article_builtin_drude_model_at_633_nm(self):
        catalog_index = calculate_refractive_index(
            resolve_material_id("Aluminum"),
            633e-9,
        )
        configured_index = calculate_configured_refractive_index(
            resolve_material_id("Aluminum"),
            633e-9,
            material_name="Aluminum",
            dispersion_model="drude",
        )

        self.assertTrue(material_uses_builtin_drude("Aluminum"))
        self.assertIsNone(default_drude_parameters_for_material("Aluminum"))
        self.assertEqual(configured_index, catalog_index)
        self.assertAlmostEqual(catalog_index.real, 0.0777761227, places=9)
        self.assertAlmostEqual(catalog_index.imag, 5.8534826159, places=9)

    def test_ito_drude_lorentz_matches_del_villar_2010_at_633_nm(self):
        refractive_index = calculate_configured_refractive_index(
            resolve_material_id("ITO"),
            633e-9,
            material_name="ITO",
            dispersion_model="drude-lorentz",
        )

        self.assertAlmostEqual(refractive_index.real, 1.9620218647, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.0076554750, places=9)

    def test_ito_builtin_drude_is_the_existing_catalog_model(self):
        catalog_index = calculate_refractive_index(resolve_material_id("ITO"), 633e-9)
        drude_index = calculate_configured_refractive_index(
            resolve_material_id("ITO"),
            633e-9,
            material_name="ITO",
            dispersion_model="drude",
        )

        self.assertEqual(drude_index, catalog_index)

    def test_zno_drude_lorentz_matches_usha_gupta_2017_at_633_nm(self):
        refractive_index = calculate_configured_refractive_index(
            resolve_material_id("ZnO"),
            633e-9,
            material_name="ZnO",
            dispersion_model="Drude–Lorentz",
        )

        self.assertAlmostEqual(refractive_index.real, 1.0674792492, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.1873238986, places=9)

    def test_zno_builtin_drude_is_the_existing_catalog_model(self):
        catalog_index = calculate_refractive_index(resolve_material_id("ZnO"), 633e-9)
        drude_index = calculate_configured_refractive_index(
            resolve_material_id("ZnO"),
            633e-9,
            material_name="ZnO",
            dispersion_model="drude",
        )

        self.assertEqual(drude_index, catalog_index)

    def test_silicon_matches_mishra_2016_at_633_nm(self):
        refractive_index = calculate_refractive_index(
            resolve_material_id("Silicon"),
            633e-9,
        )

        self.assertAlmostEqual(refractive_index.real, 3.8867194819, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.0)

    def test_swcnt_drude_lorentz_matches_mishra_2016_at_633_nm(self):
        catalog_index = calculate_refractive_index(
            resolve_material_id("Doped SWCNT"),
            633e-9,
        )
        configured_index = calculate_configured_refractive_index(
            resolve_material_id("Doped SWCNT"),
            633e-9,
            material_name="Doped SWCNT",
            dispersion_model="drude-lorentz",
        )

        self.assertTrue(material_uses_builtin_drude_lorentz("Doped SWCNT"))
        self.assertEqual(configured_index, catalog_index)
        self.assertAlmostEqual(catalog_index.real, 1.2201927743, places=9)
        self.assertAlmostEqual(catalog_index.imag, 0.2341688554, places=9)

    def test_chromium_matches_legacy_drude_critical_model_at_633_nm(self):
        refractive_index = calculate_refractive_index(
            resolve_material_id("Chromium"),
            633e-9,
        )

        self.assertAlmostEqual(refractive_index.real, 3.4973487210, places=9)
        self.assertAlmostEqual(refractive_index.imag, 4.3027308557, places=9)

    def test_fto_uses_corrected_lorentz_drude_model_at_633_nm(self):
        catalog_index = calculate_refractive_index(
            resolve_material_id("FTO"),
            633e-9,
        )
        configured_index = calculate_configured_refractive_index(
            resolve_material_id("FTO"),
            633e-9,
            material_name="FTO",
            dispersion_model="drude-lorentz",
        )

        self.assertTrue(material_uses_builtin_drude_lorentz("FTO"))
        self.assertEqual(configured_index, catalog_index)
        self.assertAlmostEqual(catalog_index.real, 1.9141566025, places=9)
        self.assertAlmostEqual(catalog_index.imag, 0.0153344689, places=9)

    def test_pmma_remains_available_as_a_predefined_fiber_core(self):
        refractive_index = calculate_fiber_core_index(
            FiberCoreConfig(material_name="PMMA"),
            633e-9,
        )

        self.assertAlmostEqual(refractive_index.real, 1.4887038437, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.0)

    def test_caf2_is_a_catalog_layer_material_with_legacy_name_alias(self):
        material_id = resolve_material_id("CaF₂")
        refractive_index = calculate_refractive_index(material_id, 633e-9)

        self.assertEqual(material_id, resolve_material_id("CaF2"))
        self.assertAlmostEqual(refractive_index.real, 1.4329603699, places=9)
        self.assertAlmostEqual(refractive_index.imag, 0.0)

        with self.assertRaisesRegex(ValueError, "Unsupported predefined fiber-core material"):
            calculate_fiber_core_index(FiberCoreConfig(material_name="CaF₂"), 633e-9)

    def test_drude_lorentz_rejects_unsupported_material(self):
        with self.assertRaisesRegex(ValueError, "ITO, ZnO, Doped SWCNT and FTO"):
            calculate_configured_refractive_index(
                resolve_material_id("Silver"),
                633e-9,
                material_name="Silver",
                dispersion_model="drude-lorentz",
            )


if __name__ == "__main__":
    unittest.main()
