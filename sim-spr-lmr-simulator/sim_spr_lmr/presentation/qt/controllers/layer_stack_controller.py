"""Controller for the layer/analyte table workflow in the Qt window."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt5 import QtGui, QtWidgets

from sim_spr_lmr.application import (
    AnalyteFormInput,
    LayerFormInput,
    LayerStateSnapshot,
    LayerValidationError,
    append_analyte,
    append_layer,
    remove_layer,
    replace_analyte,
    replace_layer,
)
from sim_spr_lmr.core.materials import resolve_material_id
from sim_spr_lmr.presentation.qt.layer_editor_presenter import (
    populate_analyte_edit_form,
    populate_layer_edit_form,
    restore_manual_layer_refractive_index,
)

# These constants define the table schema and preset storage location.
LAYER_TABLE_COLUMNS = ("material", "thickness", "refractiveIndex", "description")
LAYER_PRESETS_PATH = Path(__file__).resolve().parents[4] / "layer_presets.json"


# Coordinates layer/analyte form values, table rows, and saved presets.
class LayerStackController:
    """Coordinate layer table state while the legacy window keeps Qt slots."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def capture_layer_state_snapshot(self) -> LayerStateSnapshot:
        return LayerStateSnapshot(
            layers=[dict(layer_row) for layer_row in self.window.layers],
            material_names=list(self.window.material),
            material_ids=list(self.window.material_id),
            thicknesses_m=list(self.window.d),
            refractive_indices=list(self.window.indexRef),
            analyte_indices=list(self.window.index_ref_analyte),
        )

    def apply_layer_state_snapshot(self, snapshot: LayerStateSnapshot) -> None:
        self.window.layers = [dict(layer_row) for layer_row in snapshot.layers]
        self.window.material = list(snapshot.material_names)
        self.window.material_id = list(snapshot.material_ids)
        self.window.d = list(snapshot.thicknesses_m)
        self.window.indexRef = list(snapshot.refractive_indices)
        self.window.index_ref_analyte = list(snapshot.analyte_indices)
        self.window.nLayers = len(self.window.layers)

    def reset_layer_stack(self) -> None:
        """Clear every in-memory and visible value from the current optical stack."""
        self.apply_layer_state_snapshot(
            LayerStateSnapshot(
                layers=[],
                material_names=[],
                material_ids=[],
                thicknesses_m=[],
                refractive_indices=[],
                analyte_indices=[],
            )
        )
        self.show_layers()
        self.window.tableWidget_layers.clearSelection()
        self.window.clear_layer_form_inputs()
        self.window.clear_analyte_form_inputs()
        self.sync_layer_management_buttons()
        self.window.warning.setHidden(True)

    def collect_layer_form_input(self) -> LayerFormInput:
        if self.window.session_state.interrogation_mode == 1:
            return LayerFormInput(
                material_name=self.window.cbox_material.currentText(),
                material_id=resolve_material_id(self.window.cbox_material.currentText()),
                thickness_text=self.window.thickness.text(),
                description=self.window.description.text(),
                interrogation_mode="AIM",
                real_part_text=self.window.real_part_index.text(),
                imaginary_part_text=self.window.imaginary_part_index.text(),
                dispersion_model=self.window._selected_layer_dispersion_model("AIM"),
                drude_lambda_p_text=self.window.aim_drude_lambda_p.text(),
                drude_lambda_c_text=self.window.aim_drude_lambda_c.text(),
            )

        return LayerFormInput(
            material_name=self.window.cbox_material_2.currentText(),
            material_id=resolve_material_id(self.window.cbox_material_2.currentText()),
            thickness_text=self.window.thickness_2.text(),
            description=self.window.description_2.text(),
            interrogation_mode="WIM",
            real_part_text=self.window.wim_real_part_index.text(),
            imaginary_part_text=self.window.wim_imaginary_part_index.text(),
            dispersion_model=self.window._selected_layer_dispersion_model("WIM"),
            drude_lambda_p_text=self.window.wim_drude_lambda_p.text(),
            drude_lambda_c_text=self.window.wim_drude_lambda_c.text(),
        )

    def collect_analyte_form_input(self) -> AnalyteFormInput:
        if self.window.session_state.interrogation_mode == 1:
            return AnalyteFormInput(
                thickness_text=self.window.thickness_4.text(),
                description=self.window.description_3.text(),
                initial_index=self.window.Analyte_refractive_index.value(),
                sample_count=int(self.window.n_sample_analyte.value()),
                step=round(self.window.step_analyte.value(), 5),
            )

        return AnalyteFormInput(
            thickness_text=self.window.thickness_3.text(),
            description=self.window.description_4.text(),
            initial_index=self.window.Analyte_refractive_index_wim.value(),
            sample_count=int(self.window.n_sample_analyte_wim.value()),
            step=round(self.window.step_analyte_wim.value(), 5),
        )

# Validates and appends a new optical layer to the current stack.
    def add_layers(self) -> None:
        try:
            snapshot = append_layer(
                state=self.capture_layer_state_snapshot(),
                form_input=self.collect_layer_form_input(),
            )
        except LayerValidationError as error:
            self.window.show_layer_validation_error(error)
            return

        self.window.warning.setHidden(True)
        self.apply_layer_state_snapshot(snapshot)
        self.show_layers()
        self.window.clear_layer_form_inputs()
        self.sync_layer_management_buttons()

    def add_analyte(self) -> None:
        try:
            snapshot = append_analyte(
                state=self.capture_layer_state_snapshot(),
                form_input=self.collect_analyte_form_input(),
            )
        except LayerValidationError as error:
            self.window.show_layer_validation_error(error)
            return

        self.window.warning.setHidden(True)
        self.apply_layer_state_snapshot(snapshot)
        self.show_layers()
        self.window.clear_analyte_form_inputs()
        self.sync_layer_management_buttons()

# Removes the selected layer and keeps UI collections synchronized.
    def remove_layers(self) -> None:
        index_remove = self.window.tableWidget_layers.currentRow()
        if index_remove >= 0:
            snapshot = remove_layer(self.capture_layer_state_snapshot(), index_remove)
            self.apply_layer_state_snapshot(snapshot)
            self.show_layers()
            self.sync_layer_management_buttons()
            return

        self._show_layer_selection_warning("Select the layer to be deleted!")

    def select_edit_layer(self) -> None:
        index_select = self.window.tableWidget_layers.currentRow()
        if index_select < 0:
            self._show_layer_selection_warning("Select the layer to be edited!")
            return

        layer_edit = self.window.layers[index_select]
        if self.window.material[index_select] == "Analyte":
            populate_analyte_edit_form(
                self.window,
                layer_edit=layer_edit,
                analyte_indices=self.window.index_ref_analyte,
                interrogation_mode=self.window.session_state.interrogation_mode,
            )
            return

        populate_layer_edit_form(
            self.window,
            layer_edit=layer_edit,
            refractive_index=(
                self.window.indexRef[index_select]
                if index_select < len(self.window.indexRef)
                else None
            ),
            interrogation_mode=self.window.session_state.interrogation_mode,
        )
        self.window._populate_layer_dispersion_form(
            layer_edit,
            self.window.session_state.interrogation_mode,
        )
        restore_manual_layer_refractive_index(
            self.window,
            material_name=str(layer_edit.get("material", "")),
            refractive_index=(
                self.window.indexRef[index_select]
                if index_select < len(self.window.indexRef)
                else layer_edit.get("refractiveIndex", 0j)
            ),
            interrogation_mode=self.window.session_state.interrogation_mode,
        )

    def edit_layer(self) -> None:
        index_select = self.window.tableWidget_layers.currentRow()
        try:
            snapshot = replace_layer(
                state=self.capture_layer_state_snapshot(),
                index=index_select,
                form_input=self.collect_layer_form_input(),
            )
        except LayerValidationError as error:
            self.window.show_layer_validation_error(error)
            return

        self.window.warning.setHidden(True)
        self.apply_layer_state_snapshot(snapshot)
        self.show_layers()
        self.window.clear_layer_form_inputs()

    def edit_analyte(self) -> None:
        index_select = self.window.tableWidget_layers.currentRow()
        try:
            snapshot = replace_analyte(
                state=self.capture_layer_state_snapshot(),
                index=index_select,
                form_input=self.collect_analyte_form_input(),
            )
        except LayerValidationError as error:
            self.window.show_layer_validation_error(error)
            return

        self.window.warning.setHidden(True)
        self.apply_layer_state_snapshot(snapshot)
        self.show_layers()
        self.window.clear_analyte_form_inputs()

    def show_layers(self) -> None:
        self.window.tableWidget_layers.setRowCount(len(self.window.layers))
        for row, text in enumerate(self.window.layers):
            for column, field_name in enumerate(LAYER_TABLE_COLUMNS):
                self.window.tableWidget_layers.setItem(
                    row,
                    column,
                    QtWidgets.QTableWidgetItem(str(text.get(field_name, ""))),
                )

    def sync_layer_management_buttons(self) -> None:
        has_presets = self.has_saved_layer_presets()
        if self.window.nLayers > 0:
            self.window.btn_remove_layers.setEnabled(True)
            self.window.btn_remove_layers.setStyleSheet(self._enabled_management_button_style())
            self.window.btn_edit_layers.setEnabled(True)
            self.window.btn_edit_layers.setStyleSheet(self._enabled_management_button_style())
            self.window.btn_save_preset.setEnabled(True)
            self.window.btn_save_preset.setStyleSheet(self.window.btn_edit_layers.styleSheet())
            self._sync_preset_read_buttons(has_presets)
            return

        self.window.btn_remove_layers.setEnabled(False)
        self.window.btn_remove_layers.setStyleSheet(self._disabled_management_button_style())
        self.window.btn_edit_layers.setEnabled(False)
        self.window.btn_edit_layers.setStyleSheet(self._disabled_management_button_style())
        self.window.btn_save_preset.setEnabled(False)
        self.window.btn_save_preset.setStyleSheet(self.window.btn_edit_layers.styleSheet())
        self._sync_preset_read_buttons(has_presets)

    def has_saved_layer_presets(self) -> bool:
        return bool(self.read_layer_presets(silent=True))

    def read_layer_presets(self, *, silent: bool = False) -> dict[str, object]:
        if not LAYER_PRESETS_PATH.exists():
            return {}

        try:
            with LAYER_PRESETS_PATH.open("r", encoding="utf-8") as preset_file:
                data = json.load(preset_file)
        except (OSError, json.JSONDecodeError) as error:
            if not silent:
                self._show_message_box(
                    title="Layer presets",
                    text=f"Could not read saved layer presets.\n{error}",
                    icon=QtWidgets.QMessageBox.Warning,
                )
            return {}

        if isinstance(data, dict):
            return data
        return {}

    def write_layer_presets(self, presets: dict[str, object]) -> None:
        with LAYER_PRESETS_PATH.open("w", encoding="utf-8") as preset_file:
            json.dump(presets, preset_file, indent=2, ensure_ascii=True)

    def serialize_current_layer_preset(self) -> dict[str, object]:
        snapshot = self.capture_layer_state_snapshot()
        return {
            "simulator": self.window.session_state.simulator or "Unknown",
            "coupling": self.window.session_state.coupling_mode_name,
            "interrogation_mode": self.window.session_state.interrogation_mode_name,
            "layers": [dict(layer_row) for layer_row in snapshot.layers],
            "material_names": list(snapshot.material_names),
            "material_ids": list(snapshot.material_ids),
            "thicknesses_m": [float(value) for value in snapshot.thicknesses_m],
            "refractive_indices": [
                self._complex_to_payload(value) for value in snapshot.refractive_indices
            ],
            "analyte_indices": [
                self._complex_to_payload(value) for value in snapshot.analyte_indices
            ],
        }

    def deserialize_layer_preset(self, payload: dict[str, object]) -> LayerStateSnapshot:
        return LayerStateSnapshot(
            layers=[dict(layer_row) for layer_row in payload.get("layers", [])],
            material_names=[str(value) for value in payload.get("material_names", [])],
            material_ids=[int(value) for value in payload.get("material_ids", [])],
            thicknesses_m=[float(value) for value in payload.get("thicknesses_m", [])],
            refractive_indices=[
                self._complex_from_payload(value) for value in payload.get("refractive_indices", [])
            ],
            analyte_indices=[
                self._complex_from_payload(value) for value in payload.get("analyte_indices", [])
            ],
        )

# Serializes the current stack and stores it under a user-selected name.
    def save_layer_preset(self) -> None:
        if self.window.nLayers <= 0:
            self._show_message_box(
                title="Save preset",
                text="Add at least one layer before saving a preset.",
                icon=QtWidgets.QMessageBox.Warning,
            )
            return

        default_name = (
            f"{self.window.session_state.simulator or 'Simulation'}_"
            f"{self.window.session_state.interrogation_mode_name}"
        )
        preset_name, accepted = QtWidgets.QInputDialog.getText(
            self.window,
            "Save layer preset",
            "Preset name:",
            text=default_name,
        )
        preset_name = preset_name.strip()
        if not accepted or preset_name == "":
            return

        presets = self.read_layer_presets()
        if preset_name in presets:
            overwrite = QtWidgets.QMessageBox.question(
                self.window,
                "Save layer preset",
                f"The preset '{preset_name}' already exists. Do you want to overwrite it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if overwrite != QtWidgets.QMessageBox.Yes:
                return

        presets[preset_name] = self.serialize_current_layer_preset()
        self.write_layer_presets(presets)
        self.sync_layer_management_buttons()
        self._show_message_box(
            title="Save preset",
            text=f"Preset '{preset_name}' saved successfully.",
        )

# Reconstructs a saved preset and applies it to the current window.
    def load_layer_preset(self) -> None:
        presets = self.read_layer_presets()
        if not presets:
            self._show_message_box(
                title="Load preset",
                text="No saved layer presets were found yet.",
                icon=QtWidgets.QMessageBox.Warning,
            )
            return

        preset_labels, preset_map = self._build_preset_selection_labels(presets)

        selected_label, accepted = QtWidgets.QInputDialog.getItem(
            self.window,
            "Load layer preset",
            "Saved presets:",
            preset_labels,
            0,
            False,
        )
        if not accepted or selected_label == "":
            return

        preset_name = preset_map[selected_label]
        preset_payload = presets[preset_name]
        snapshot = self.deserialize_layer_preset(preset_payload)
        self.apply_layer_state_snapshot(snapshot)
        self.show_layers()
        self.window.clear_layer_form_inputs()
        self.window.clear_analyte_form_inputs()
        self.sync_layer_management_buttons()
        self.window.warning.setHidden(True)

        preset_mode = preset_payload.get("interrogation_mode", "Unknown")
        if preset_mode != self.window.session_state.interrogation_mode_name:
            self._show_message_box(
                title="Load preset",
                text=(
                    f"Preset '{preset_name}' loaded successfully.\n"
                    f"It was created in {preset_mode}, so review the current "
                    "mode-specific fields before running."
                ),
            )
            return

        self._show_message_box(
            title="Load preset",
            text=f"Preset '{preset_name}' loaded successfully.",
        )

    def delete_layer_preset(self) -> None:
        presets = self.read_layer_presets()
        if not presets:
            self._show_message_box(
                title="Delete preset",
                text="No saved layer presets were found yet.",
                icon=QtWidgets.QMessageBox.Warning,
            )
            return

        preset_labels, preset_map = self._build_preset_selection_labels(presets)
        selected_label, accepted = QtWidgets.QInputDialog.getItem(
            self.window,
            "Delete layer preset",
            "Saved presets:",
            preset_labels,
            0,
            False,
        )
        if not accepted or selected_label == "":
            return

        preset_name = preset_map[selected_label]
        confirm_delete = QtWidgets.QMessageBox.question(
            self.window,
            "Delete layer preset",
            f"Delete preset '{preset_name}'? This cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if confirm_delete != QtWidgets.QMessageBox.Yes:
            return

        del presets[preset_name]
        self.write_layer_presets(presets)
        self.sync_layer_management_buttons()
        self._show_message_box(
            title="Delete preset",
            text=f"Preset '{preset_name}' deleted successfully.",
        )

    def _build_preset_selection_labels(
        self, presets: dict[str, object]
    ) -> tuple[list[str], dict[str, str]]:
        preset_labels = []
        preset_map = {}
        for preset_name in sorted(presets):
            preset_payload = presets[preset_name]
            label = (
                f"{preset_name} "
                f"[{preset_payload.get('simulator', 'Unknown')} / "
                f"{preset_payload.get('interrogation_mode', 'Unknown')}]"
            )
            preset_labels.append(label)
            preset_map[label] = preset_name
        return preset_labels, preset_map

    def _sync_preset_read_buttons(self, has_presets: bool) -> None:
        style = (
            self.window.btn_save_table.styleSheet()
            if has_presets
            else self._disabled_management_button_style()
        )
        self.window.btn_load_preset.setEnabled(has_presets)
        self.window.btn_load_preset.setStyleSheet(style)
        self.window.btn_delete_preset.setEnabled(has_presets)
        self.window.btn_delete_preset.setStyleSheet(style)

    def _show_layer_selection_warning(self, text: str) -> None:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText(text)
        msg.setWindowTitle("Warning")
        msg.setWindowIcon(QtGui.QIcon("icons/LOGO.png"))
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def _show_message_box(
        self,
        *,
        title: str,
        text: str,
        icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Information,
    ) -> None:
        message_box = QtWidgets.QMessageBox(self.window)
        message_box.setIcon(icon)
        message_box.setWindowTitle(title)
        message_box.setText(text)
        message_box.exec_()

    def _complex_to_payload(self, value: object) -> dict[str, float] | None:
        if value is None:
            return None
        complex_value = complex(value)
        return {
            "real": float(complex_value.real),
            "imag": float(complex_value.imag),
        }

    def _complex_from_payload(self, payload: object) -> complex | None:
        if payload is None:
            return None
        return complex(float(payload.get("real", 0.0)), float(payload.get("imag", 0.0)))

    def _enabled_management_button_style(self) -> str:
        return (
            "QPushButton{\n"
            '    font: 400 11pt "Ubuntu";\n'
            "    color: rgb(255, 255,255);\n"
            "    background-color: rgb(0, 130, 180);\n"
            "    border-color: rgb(0, 100, 130);\n"
            "    border-width: 2px;\n"
            "    border-radius:10px;\n"
            "}\n"
            "\n"
            "QPushButton:hover{\n"
            "    background-color: rgb(200, 200, 70);\n"
            "    border-color: rgb(0, 120, 40);\n"
            "    width: 40;\n"
            "    height: 35;\n"
            "}"
        )

    def _disabled_management_button_style(self) -> str:
        return (
            "QPushButton{\n"
            '    font: 400 11pt "Ubuntu";\n'
            "    color: rgb(255, 255,255);\n"
            "    background-color: #606060;\n"
            "    border-color: rgb(0, 100, 130);\n"
            "    border-width: 2px;\n"
            "    border-radius:10px;\n"
            "}\n"
            "\n"
            "QPushButton:hover{\n"
            "    background-color: rgb(00, 140, 70);\n"
            "    border-color: rgb(0, 120, 40);\n"
            "    width: 40;\n"
            "    height: 35;\n"
            "}"
        )
