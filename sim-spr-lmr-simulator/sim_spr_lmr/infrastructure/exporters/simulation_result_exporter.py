"""File export helpers for ``SimulationResult`` artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from sim_spr_lmr.core.domain import SimulationResult
from sim_spr_lmr.core.optics.response_scale import (
    REFLECTANCE_SCALE_DB,
    REFLECTANCE_SCALE_LINEAR,
    convert_response_curves,
    effective_response_quantity,
)


# Artifact models keep export content and file names together so the UI can preview exactly the data that will be written.
@dataclass(slots=True)
class ExportArtifact:
    """Represents one text artifact produced from a simulation result."""

    file_name: str
    content: str


@dataclass(slots=True)
class SimulationExportPackage:
    """Grouped text artifacts and previews used by the export dialog."""

    parameters_preview: str
    reflectance_preview: str
    parameters_artifact: ExportArtifact
    reflectance_artifacts: list[ExportArtifact] = field(default_factory=list)


def build_parameters_preview(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    """Build the textual parameter summary shown in the export dialog."""

    # LMR+SPR may contain several resonance series, while conventional simulations expose one metric set.
    lines = [
        f"Polarization ({simulation_result.polarization})",
        f"Response quantity: {_response_quantity_label(simulation_result, reflectance_scale)}",
        "",
    ]

    if simulation_result.simulator == "LMR+SPR":
        if not simulation_result.resonance_series:
            lines.append("No resonance was detected automatically in the simulated spectral range.")
            return "\n".join(lines).strip()
        for number, metric_series in enumerate(simulation_result.resonance_series.values(), start=1):
            lines.extend(
                [
                    f"Resonance {simulation_result.axis_label} ({simulation_result.axis_unit}) {number}: {metric_series.get('points', [])}",
                    f"FWHM ({simulation_result.axis_unit}) {number}: {metric_series.get('fwhm', [])}",
                    f"Sensitivity ({simulation_result.axis_unit}/RIU) {number}: {metric_series.get('sensitivity', [])}",
                    f"Figure of merit {number}: {metric_series.get('quality_factor', [])}",
                    "",
                ]
            )
        return "\n".join(lines).strip()

    lines.extend(
        [
            f"Resonance {simulation_result.axis_label} ({simulation_result.axis_unit}): {simulation_result.resonance_points}",
            f"FWHM ({simulation_result.axis_unit}): {simulation_result.fwhm}",
            f"Sensitivity ({simulation_result.axis_unit}/RIU): {simulation_result.sensitivity}",
            f"Figure of merit: {simulation_result.quality_factor}",
        ]
    )
    return "\n".join(lines)


def build_reflectance_preview(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    """Build the short response preview shown in the export dialog."""

    return f"{simulation_result.axis_label},{_response_export_label(simulation_result, reflectance_scale)}"


def build_simulation_export_package(
    simulation_result: SimulationResult,
    base_name: str,
    reflectance_scale: str | None = None,
) -> SimulationExportPackage:
    """Build the export package for a simulation result."""

    # The export dialog can preview and persist the same package, which keeps
    # formatting rules in one place.
    # Normalize the base name once so every generated artifact follows the same naming convention.
    normalized_base_name = base_name.strip() or "Simulacao1"
    parameters_preview = build_parameters_preview(simulation_result, reflectance_scale)
    reflectance_preview = build_reflectance_preview(simulation_result, reflectance_scale)

    parameters_artifact = ExportArtifact(
        file_name=f"{normalized_base_name}_Parameters_{simulation_result.polarization}.txt",
        content=parameters_preview,
    )

    reflectance_artifacts: list[ExportArtifact] = []
    response_curve_label = _response_export_label(simulation_result, reflectance_scale)
    # Create one response file for each analyte index and preserve the selected response scale.
    for analyte_index, reflectance_curve in zip(
        simulation_result.analyte_indices,
        _response_curves(simulation_result, reflectance_scale),
        strict=False,
    ):
        analyte_label = str(analyte_index.real).replace(".", "_")
        lines = [reflectance_preview]

        for axis_value, reflectance_value in zip(
            simulation_result.axis_x,
            reflectance_curve,
            strict=False,
        ):
            lines.append(f"{axis_value:.3f},{reflectance_value:.6f}")

        reflectance_artifacts.append(
            ExportArtifact(
                file_name=(
                    f"{normalized_base_name}_{response_curve_label}_vs_analyte_"
                    f"{analyte_label}_{simulation_result.polarization}.txt"
                ),
                content="\n".join(lines),
            )
        )

    return SimulationExportPackage(
        parameters_preview=parameters_preview,
        reflectance_preview=reflectance_preview,
        parameters_artifact=parameters_artifact,
        reflectance_artifacts=reflectance_artifacts,
    )


def write_simulation_export_package(
    export_package: SimulationExportPackage,
    include_reflectance: bool = True,
    include_parameters: bool = True,
) -> list[Path]:
    """Persist the selected export artifacts and return their paths."""

    # File writing is isolated here so presentation code can stay side-effect
    # free and focus only on the dialog behavior.
    written_paths: list[Path] = []

    if include_parameters:
        parameter_path = Path(export_package.parameters_artifact.file_name)
        parameter_path.write_text(export_package.parameters_artifact.content, encoding="utf-8")
        written_paths.append(parameter_path)

    if include_reflectance:
        for reflectance_artifact in export_package.reflectance_artifacts:
            reflectance_path = Path(reflectance_artifact.file_name)
            reflectance_path.write_text(reflectance_artifact.content, encoding="utf-8")
            written_paths.append(reflectance_path)

    return written_paths


def _response_curves(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> list[list[float]]:
    # Prefer normalized response curves while retaining compatibility with legacy reflectance-only results.
    curves = simulation_result.response_curves or simulation_result.reflectance_curves
    return convert_response_curves(
        curves,
        source_quantity=simulation_result.response_quantity,
        reflectance_scale=reflectance_scale,
    )


def _effective_response_quantity(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    return effective_response_quantity(
        simulation_result.response_quantity,
        reflectance_scale,
    )


def _response_quantity_label(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    # Convert the internal response name into text suitable for the preview UI.
    response_quantity = _effective_response_quantity(simulation_result, reflectance_scale)
    if response_quantity == "transmission":
        return "Normalized Transmission"
    if response_quantity == "reflectance_db":
        return "Reflectance (dB)"
    if reflectance_scale is not None:
        return "Reflectance (R linear)"
    return "Reflectance"


def _response_export_label(
    simulation_result: SimulationResult,
    reflectance_scale: str | None = None,
) -> str:
    # Convert the internal response name into text suitable for the preview UI.
    response_quantity = _effective_response_quantity(simulation_result, reflectance_scale)
    if response_quantity == "transmission":
        return "Normalized_Transmission"
    if reflectance_scale == REFLECTANCE_SCALE_DB:
        return "Reflectance_dB"
    if reflectance_scale == REFLECTANCE_SCALE_LINEAR:
        return "Reflectance_linear"
    if response_quantity == "reflectance_db":
        return "Reflectance_(dB)"
    return "Reflectance"
