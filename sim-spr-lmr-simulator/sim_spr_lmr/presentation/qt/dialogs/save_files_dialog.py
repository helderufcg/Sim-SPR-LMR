"""Behavior wrapper for the generated save-files dialog UI."""

from __future__ import annotations

from PyQt5 import QtCore, QtGui, QtWidgets

from save_files import Ui_Dialog
from sim_spr_lmr.core.domain import SimulationResult
from sim_spr_lmr.infrastructure.exporters import (
    build_parameters_preview,
    build_reflectance_preview,
    build_simulation_export_package,
    write_simulation_export_package,
)


# Previews the current result and delegates export formatting to infrastructure services.
class SaveFilesDialog(QtWidgets.QDialog):
    """Dialog that previews and exports the current simulation result."""

    def __init__(
        self,
        simulation_result: SimulationResult | None,
        parent: QtWidgets.QWidget | None = None,
        reflectance_scale: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.simulation_result = simulation_result
        self.reflectance_scale = reflectance_scale
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowIcon(QtGui.QIcon("icons/LOGO.png"))
        self.setWindowTitle("Save Files")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowCloseButtonHint)

        # The generated UI connects accepted to accept(); this dialog validates
        # and exports before closing, so it owns the Save button behavior.
        try:
            self.ui.buttonBox.accepted.disconnect()
        except TypeError:
            pass
        self.ui.buttonBox.accepted.connect(self.save_file)

        self.show_text()

    # Populates the preview area with parameters and simulation data.
    def show_text(self) -> None:
        """Populate the preview fields with the exportable simulation data."""

        if self.simulation_result is None:
            self.ui.show_file_parameters.setText("No simulation result available.")
            self.ui.show_file_reflectance.setText("")
            return

        if getattr(self.simulation_result, "response_quantity", "reflectance") == "transmission":
            self.ui.save_reflectance.setText("Transmission vs. Analyte")
        else:
            self.ui.save_reflectance.setText("Reflectance vs. Analyte")

        self.ui.show_file_parameters.setText(
            build_parameters_preview(self.simulation_result, self.reflectance_scale)
        )
        self.ui.show_file_reflectance.setText(
            build_reflectance_preview(self.simulation_result, self.reflectance_scale)
        )

    # Validates the destination and writes the selected export package.
    def save_file(self) -> None:
        """Persist selected export artifacts and close on success."""

        if self.simulation_result is None:
            self._show_message(
                QtWidgets.QMessageBox.Warning,
                "No simulation result available for export.",
            )
            return

        include_reflectance = (
            self.ui.save_default.isChecked() or self.ui.save_reflectance.isChecked()
        )
        include_parameters = (
            self.ui.save_default.isChecked() or self.ui.save_parameters.isChecked()
        )

        if not include_reflectance and not include_parameters:
            self._show_message(
                QtWidgets.QMessageBox.Warning,
                "Select at least one export option.",
            )
            return

        export_package = build_simulation_export_package(
            simulation_result=self.simulation_result,
            base_name=self.ui.file_name.text(),
            reflectance_scale=self.reflectance_scale,
        )
        write_simulation_export_package(
            export_package=export_package,
            include_reflectance=include_reflectance,
            include_parameters=include_parameters,
        )

        self._show_message(QtWidgets.QMessageBox.Information, "Successfully saved file")
        self.close()

    def _show_message(self, icon: QtWidgets.QMessageBox.Icon, text: str) -> None:
        message = QtWidgets.QMessageBox(self)
        message.setIcon(icon)
        message.setWindowTitle("Save Simulation Data")
        message.setText(text)
        message.exec()
