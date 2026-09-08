from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sim_spr_lmr.core.domain import ParametricAnalysisResult, ParametricResonanceTrack
from sim_spr_lmr.infrastructure.exporters import (
    build_parametric_metrics_csv,
    build_parametric_spectra_csv,
    write_parametric_analysis_exports,
)


def result_fixture() -> ParametricAnalysisResult:
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
        response_axis=[400.0, 500.0],
        response_axis_label="Wavelength",
        response_axis_unit="nm",
        response_curves=[[0.8, 0.1], [0.7, 0.2]],
        resonance_tracks=[
            ParametricResonanceTrack(
                label="Resonance 1",
                positions=[500.0, float("nan")],
                fwhm=[10.0, float("nan")],
                minimum_response=[0.1, float("nan")],
                sensitivity=[1.0, float("nan")],
                quality_factor=[0.1, float("nan")],
            )
        ],
    )


class ParametricAnalysisExporterTests(unittest.TestCase):
    def test_csv_builders_include_metrics_spectra_and_missing_values(self) -> None:
        metrics = build_parametric_metrics_csv(result_fixture())
        spectra = build_parametric_spectra_csv(result_fixture())

        self.assertIn("Resonance position (nm)", metrics)
        self.assertIn("Sensitivity (nm/RIU)", metrics)
        self.assertIn("Figure of merit (1/RIU)", metrics)
        self.assertIn("NaN", metrics)
        self.assertIn("Reflectance at 60 nm", spectra)

    def test_writer_creates_metrics_and_sibling_spectra_files(self) -> None:
        with TemporaryDirectory() as directory:
            selected_path = Path(directory) / "analysis.csv"
            written = write_parametric_analysis_exports(result_fixture(), selected_path)

            self.assertEqual(written, [selected_path, Path(directory) / "analysis_spectra.csv"])
            self.assertTrue(all(path.exists() for path in written))


if __name__ == "__main__":
    unittest.main()
