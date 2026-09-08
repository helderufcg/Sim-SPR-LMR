from __future__ import annotations

from math import pi
import unittest
from unittest.mock import patch

from sim_spr_lmr.application import (
    ParametricAnalysisInput,
    build_inclusive_sweep_values,
    run_parametric_analysis,
)
from sim_spr_lmr.core.domain import LayerConfig, SimulationConfig, SimulationResult


def base_config() -> SimulationConfig:
    return SimulationConfig(
        simulator="LMR+SPR",
        coupling="Prism",
        interrogation_mode="WIM",
        polarization="TM",
        layers=[
            LayerConfig("BK7", 1, 0.0, 1.5 + 0j),
            LayerConfig("Gold", 4, 50e-9, 0.2 + 3j),
            LayerConfig("Analyte", -1, 0.0, 1.33 + 0j, is_analyte=True),
        ],
        analyte_indices=[1.33 + 0j, 1.34 + 0j],
        incidence_angle_rad=60 * pi / 180,
        scan_start=400e-9,
        scan_stop=800e-9,
        scan_step=1e-9,
        resonance_strategy="lmr_spr_auto_multi_dip",
    )


def fake_result(position: float, sensitivity: float = -100.0) -> SimulationResult:
    return SimulationResult(
        simulator="LMR+SPR",
        interrogation_mode="WIM",
        polarization="TM",
        response_quantity="reflectance",
        analyte_indices=[1.33 + 0j, 1.34 + 0j],
        axis_x=[400.0, 500.0, 600.0],
        axis_label="Wavelength",
        axis_unit="nm",
        response_curves=[[0.8, 0.1, 0.9], [0.82, 0.12, 0.88]],
        resonance_series={
            "Resonance 1": {
                "points": [position, position - 1.0],
                "fwhm": [10.0, 10.0],
                "minimum_response": [0.1, 0.12],
                "sensitivity": [sensitivity, sensitivity],
                "quality_factor": [abs(sensitivity) / 10.0] * 2,
            }
        },
    )


class ParametricAnalysisServiceTests(unittest.TestCase):
    def test_inclusive_sweep_keeps_final_value(self) -> None:
        self.assertEqual(build_inclusive_sweep_values(50, 51, 0.4), [50.0, 50.4, 50.8, 51.0])

    def test_thickness_sweep_clones_config_and_calculates_metrics(self) -> None:
        config = base_config()
        observed_configs: list[SimulationConfig] = []

        def run_stub(step_config, progress_callback=None, log_callback=None):
            observed_configs.append(step_config)
            thickness_nm = step_config.layers[1].thickness_m * 1e9
            if progress_callback:
                progress_callback(100)
            return fake_result(400.0 + (2.0 * thickness_nm))

        with patch(
            "sim_spr_lmr.application.parametric_analysis_service.run_simulation",
            side_effect=run_stub,
        ):
            result = run_parametric_analysis(
                ParametricAnalysisInput(
                    base_config=config,
                    parameter_kind="thickness",
                    parameter_values=[50.0, 60.0],
                    fixed_analyte_index=1.33 + 0j,
                    layer_index=1,
                )
            )

        self.assertAlmostEqual(config.layers[1].thickness_m, 50e-9)
        for actual, expected in zip(
            [item.layers[1].thickness_m for item in observed_configs],
            [50e-9, 60e-9],
            strict=False,
        ):
            self.assertAlmostEqual(actual, expected)
        self.assertTrue(
            all(
                item.analyte_indices == [1.33 + 0j, 1.34 + 0j]
                for item in observed_configs
            )
        )
        self.assertEqual(result.resonance_tracks[0].positions, [500.0, 520.0])
        self.assertEqual(result.resonance_tracks[0].sensitivity, [100.0, 100.0])
        self.assertEqual(result.resonance_tracks[0].quality_factor, [10.0, 10.0])
        self.assertEqual(result.sensitivity_unit, "nm/RIU")
        self.assertEqual(result.quality_factor_unit, "1/RIU")

    def test_angle_sweep_updates_only_fixed_wim_angle(self) -> None:
        observed_angles: list[float] = []

        def run_stub(step_config, progress_callback=None, log_callback=None):
            observed_angles.append(step_config.incidence_angle_rad)
            return fake_result(500.0)

        with patch(
            "sim_spr_lmr.application.parametric_analysis_service.run_simulation",
            side_effect=run_stub,
        ):
            run_parametric_analysis(
                ParametricAnalysisInput(
                    base_config=base_config(),
                    parameter_kind="incidence_angle",
                    parameter_values=[60.0, 61.0],
                    fixed_analyte_index=1.33 + 0j,
                )
            )

        self.assertAlmostEqual(observed_angles[0], 60 * pi / 180)
        self.assertAlmostEqual(observed_angles[1], 61 * pi / 180)

    def test_single_dip_sweep_keeps_one_track_across_large_displacements(self) -> None:
        config = base_config()
        config.simulator = "SPR"
        config.resonance_strategy = "single_dip"

        with patch(
            "sim_spr_lmr.application.parametric_analysis_service.run_simulation",
            side_effect=[fake_result(400.0), fake_result(940.0), fake_result(770.0)],
        ):
            result = run_parametric_analysis(
                ParametricAnalysisInput(
                    base_config=config,
                    parameter_kind="incidence_angle",
                    parameter_values=[60.0, 61.0, 62.0],
                    fixed_analyte_index=1.33 + 0j,
                )
            )

        self.assertEqual(len(result.resonance_tracks), 1)
        self.assertEqual(result.resonance_tracks[0].positions, [400.0, 940.0, 770.0])

    def test_explicit_conventional_step_builds_pair_from_single_fixed_index(self) -> None:
        config = base_config()
        config.analyte_indices = [1.33 + 0j]
        observed_pairs: list[list[complex]] = []

        def run_stub(step_config, progress_callback=None, log_callback=None):
            observed_pairs.append(step_config.analyte_indices)
            return fake_result(500.0)

        with patch(
            "sim_spr_lmr.application.parametric_analysis_service.run_simulation",
            side_effect=run_stub,
        ):
            run_parametric_analysis(
                ParametricAnalysisInput(
                    base_config=config,
                    parameter_kind="incidence_angle",
                    parameter_values=[60.0, 61.0],
                    fixed_analyte_index=1.33 + 0j,
                    analyte_step=0.01,
                )
            )

        self.assertEqual(
            observed_pairs,
            [[1.33 + 0j, 1.34 + 0j], [1.33 + 0j, 1.34 + 0j]],
        )


if __name__ == "__main__":
    unittest.main()
