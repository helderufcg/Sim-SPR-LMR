from __future__ import annotations

from pathlib import Path
import re
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = PROJECT_ROOT / "sim-spr-lmr-simulator"


def _combo_items(source: str, combo_name: str) -> list[str]:
    block_match = re.search(
        rf"self\.{combo_name} = QtWidgets\.QComboBox.*?"
        rf"self\.{combo_name}\.setObjectName",
        source,
        flags=re.DOTALL,
    )
    if block_match is None:
        raise AssertionError(f"Combo box {combo_name!r} was not found")
    return re.findall(
        rf'self\.{combo_name}\.addItem\("([^"]+)"',
        block_match.group(0),
    )


class MaterialCatalogUiTests(unittest.TestCase):
    def test_layer_selectors_expose_chromium_and_fto(self) -> None:
        source = (APP_ROOT / "Sim_LMR_interface.py").read_text(encoding="utf-8")

        for combo_name in ("cbox_material", "cbox_material_2"):
            with self.subTest(combo=combo_name):
                items = _combo_items(source, combo_name)
                self.assertIn("Chromium", items)
                self.assertIn("FTO", items)
                self.assertIn("Doped SWCNT", items)
                self.assertIn("Nickel", items)
                self.assertIn("SF11", items)
                self.assertIn("Aluminum", items)
                self.assertIn("Graphene", items)
                self.assertIn("Custom", items)
                self.assertEqual(items.count("Copper"), 1)
                self.assertNotIn("Copper (Filmetrics)", items)
                self.assertNotIn("Al", items)
                self.assertNotIn("SWCNT", items)

    def test_caf2_is_exposed_as_a_layer_but_not_as_a_fiber_core(self) -> None:
        main_source = (APP_ROOT / "Sim_LMR_interface.py").read_text(encoding="utf-8")

        for combo_name in ("cbox_material", "cbox_material_2"):
            with self.subTest(combo=combo_name):
                items = _combo_items(main_source, combo_name)
                self.assertIn("CaF₂", items)
                self.assertNotIn("CaF2", items)

        standard_core_items = _combo_items(main_source, "cbox_core_material")
        self.assertIn("PMMA", standard_core_items)
        self.assertNotIn("CaF₂", standard_core_items)
        self.assertNotIn("CaF2", standard_core_items)

        d_shaped_source = (
            APP_ROOT
            / "sim_spr_lmr"
            / "presentation"
            / "qt"
            / "d_shaped_fiber_page.py"
        ).read_text(encoding="utf-8")
        self.assertIn('d_shape_core_material.addItem("PMMA")', d_shaped_source)
        self.assertNotIn('d_shape_core_material.addItem("CaF₂")', d_shaped_source)
        self.assertNotIn('d_shape_core_material.addItem("CaF2")', d_shaped_source)

    def test_results_page_exposes_unpolarized_te_tm_option(self) -> None:
        source = (APP_ROOT / "Sim_LMR_interface.py").read_text(encoding="utf-8")

        self.assertIn(
            'self.TE_TM_polarization = QtWidgets.QRadioButton(self.grafico1_4)',
            source,
        )
        self.assertIn('u"Unpolarized (TE + TM)"', source)


if __name__ == "__main__":
    unittest.main()
