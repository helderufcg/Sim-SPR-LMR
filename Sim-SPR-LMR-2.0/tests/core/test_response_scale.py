import unittest

from matplotlib.figure import Figure

from sim_spr_lmr.core.domain import SimulationResult
from sim_spr_lmr.core.optics import (
    REFLECTANCE_SCALE_DB,
    REFLECTANCE_SCALE_LINEAR,
    convert_response_curves,
)
from sim_spr_lmr.infrastructure.exporters import build_simulation_export_package
from sim_spr_lmr.presentation.plotting import build_simulation_summary, render_simulation_result


def _prism_result() -> SimulationResult:
    return SimulationResult(
        simulator="LMR+SPR",
        interrogation_mode="WIM",
        polarization="TM",
        response_quantity="reflectance_db",
        analyte_indices=[1.33 + 0j],
        axis_x=[500.0, 600.0],
        axis_label="Wavelength",
        axis_unit="nm",
        response_curves=[[-10.0, 0.0]],
        reflectance_curves=[[-10.0, 0.0]],
        resonance_points=[550.0],
        fwhm=[25.0],
    )


class ResponseScaleTests(unittest.TestCase):
    def test_db_curve_is_converted_to_linear_without_mutating_result(self):
        result = _prism_result()

        converted = convert_response_curves(
            result.response_curves,
            source_quantity=result.response_quantity,
            reflectance_scale=REFLECTANCE_SCALE_LINEAR,
        )

        self.assertEqual(converted, [[0.1, 1.0]])
        self.assertEqual(result.response_curves, [[-10.0, 0.0]])
        self.assertEqual(result.resonance_points, [550.0])
        self.assertEqual(result.fwhm, [25.0])

    def test_plot_uses_selected_scale_and_axis_label(self):
        result = _prism_result()
        figure = Figure()

        render_simulation_result(
            figure,
            "Reflectance",
            result,
            reflectance_scale=REFLECTANCE_SCALE_LINEAR,
        )

        axis = figure.axes[0]
        self.assertEqual(axis.get_ylabel(), "Reflectance (R)")
        self.assertEqual(list(axis.lines[0].get_ydata()), [0.1, 1.0])
        self.assertIn(
            "Response quantity: Reflectance (R)",
            build_simulation_summary(result, REFLECTANCE_SCALE_LINEAR),
        )

        render_simulation_result(
            figure,
            "Reflectance",
            result,
            reflectance_scale=REFLECTANCE_SCALE_DB,
        )
        axis = figure.axes[0]
        self.assertEqual(axis.get_ylabel(), "Reflectance (dB)")
        self.assertEqual(list(axis.lines[0].get_ydata()), [-10.0, 0.0])

    def test_export_uses_selected_linear_scale_in_header_and_filename(self):
        package = build_simulation_export_package(
            _prism_result(),
            "Prism",
            reflectance_scale=REFLECTANCE_SCALE_LINEAR,
        )

        artifact = package.reflectance_artifacts[0]
        self.assertIn("_Reflectance_linear_vs_analyte_", artifact.file_name)
        self.assertEqual(artifact.content.splitlines()[0], "Wavelength,Reflectance_linear")
        self.assertEqual(artifact.content.splitlines()[1:], ["500.000,0.100000", "600.000,1.000000"])
        self.assertIn("Response quantity: Reflectance (R linear)", package.parameters_preview)

    def test_export_uses_selected_db_scale_in_header_and_filename(self):
        package = build_simulation_export_package(
            _prism_result(),
            "Prism",
            reflectance_scale=REFLECTANCE_SCALE_DB,
        )

        artifact = package.reflectance_artifacts[0]
        self.assertIn("_Reflectance_dB_vs_analyte_", artifact.file_name)
        self.assertEqual(artifact.content.splitlines()[0], "Wavelength,Reflectance_dB")
        self.assertEqual(artifact.content.splitlines()[1:], ["500.000,-10.000000", "600.000,0.000000"])
        self.assertIn("Response quantity: Reflectance (dB)", package.parameters_preview)

    def test_conventional_sensitivity_text_is_correct_in_plot_and_export(self):
        result = _prism_result()
        result.simulator = "SPR"
        result.sensitivity = [100.0]
        result.quality_factor = [4.0]
        figure = Figure()

        render_simulation_result(figure, "Sensitivity vs. Analyte", result)

        self.assertTrue(figure.axes[0].get_ylabel().startswith("Sensitivity"))
        summary = build_simulation_summary(result)
        package = build_simulation_export_package(result, "Prism")
        self.assertIn("Sensitivity (nm/RIU)", summary)
        self.assertIn("Sensitivity (nm/RIU)", package.parameters_preview)
        self.assertNotIn("Sensibility", summary)
        self.assertNotIn("Sensibility", package.parameters_preview)


if __name__ == "__main__":
    unittest.main()
