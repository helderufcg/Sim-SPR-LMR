from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UI_FILE = PROJECT_ROOT / "ui" / "open_extern_file.ui"
GENERATED_UI_FILE = PROJECT_ROOT / "sim-spr-lmr-simulator" / "open_extern_file.py"
DIALOGS_ROOT = (
    PROJECT_ROOT
    / "sim-spr-lmr-simulator"
    / "sim_spr_lmr"
    / "presentation"
    / "qt"
    / "dialogs"
)


class ExternalFileAnalysisUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ui = ET.parse(UI_FILE).getroot()

    def _widget(self, name: str) -> ET.Element:
        widget = self.ui.find(f".//widget[@name='{name}']")
        self.assertIsNotNone(widget, f"Widget {name!r} is missing from {UI_FILE}")
        return widget  # type: ignore[return-value]

    def _property(self, node: ET.Element, name: str) -> ET.Element:
        prop = node.find(f"./property[@name='{name}']")
        self.assertIsNotNone(prop, f"Property {name!r} is missing")
        return prop  # type: ignore[return-value]

    def test_reference_window_dimensions_are_preserved(self) -> None:
        root_widget = self.ui.find("./widget")
        self.assertIsNotNone(root_widget)

        geometry = self._property(root_widget, "geometry")
        minimum = self._property(root_widget, "minimumSize")

        self.assertEqual(geometry.findtext("./rect/width"), "1280")
        self.assertEqual(geometry.findtext("./rect/height"), "740")
        self.assertEqual(minimum.findtext("./size/width"), "800")
        self.assertEqual(minimum.findtext("./size/height"), "740")

    def test_curve_result_cards_keep_reference_width_hints(self) -> None:
        expected_widths = {
            "label": 120,
            "label_15": 120,
            "label_16": 130,
            "label_4": 120,
            "label_21": 120,
            "label_22": 130,
            "Qline_resonance": 110,
            "Qline_fwhm": 110,
            "Qline_min_ref": 110,
            "Qline_resonance_2": 110,
            "Qline_fwhm_2": 110,
            "Qline_min_ref_2": 110,
        }

        for name, expected_width in expected_widths.items():
            with self.subTest(widget=name):
                maximum = self._property(self._widget(name), "maximumSize")
                self.assertEqual(
                    int(maximum.findtext("./size/width", default="0")),
                    expected_width,
                )

    def test_graph_and_combined_results_match_reference_styling(self) -> None:
        graph_style = self._property(self._widget("frame_graphs"), "styleSheet")
        self.assertNotIn("QFrame{border", graph_style.findtext("./string", default=""))

        results_layout = self.ui.find(".//layout[@name='verticalLayout_4']")
        self.assertIsNotNone(results_layout)
        spacing = self._property(results_layout, "spacing")
        self.assertEqual(spacing.findtext("./number"), "0")

        delta_result = self._property(self._widget("Qline_delta_res"), "text")
        self.assertEqual(delta_result.findtext("./string"), "0")

        delta_index = self._widget("spin_delta_index")
        button_symbols = self._property(delta_index, "buttonSymbols")
        self.assertEqual(
            button_symbols.findtext("./enum"),
            "QAbstractSpinBox::NoButtons",
        )

    def test_generated_python_is_in_sync_with_visual_source(self) -> None:
        generated = GENERATED_UI_FILE.read_text(encoding="utf-8")
        self.assertIn("Widget.resize(1280, 740)", generated)
        self.assertIn(
            "self.spin_delta_index.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)",
            generated,
        )

    def test_external_windows_use_embedded_application_icon(self) -> None:
        expected = 'QtGui.QIcon(":/icons/icons/LOGO.png")'

        for file_name in (
            "instructions_dialog.py",
            "external_file_analysis_window.py",
        ):
            with self.subTest(file=file_name):
                source = (DIALOGS_ROOT / file_name).read_text(encoding="utf-8")
                self.assertIn(expected, source)


if __name__ == "__main__":
    unittest.main()
