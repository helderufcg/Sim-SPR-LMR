"""Behavior wrapper for the external-file instructions dialog."""

from __future__ import annotations

from PyQt5 import QtGui, QtWidgets

from instructions import Ui_Dialog


# Presents instructions before opening external-curve analysis.
class InstructionsDialog(QtWidgets.QDialog):
    """Show instructions, then open the external-curve analysis window."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.external_window: QtWidgets.QWidget | None = None

        self.setWindowIcon(QtGui.QIcon(":/icons/icons/LOGO.png"))
        self.setWindowTitle("Sim-LMR - External File Analyse - Instructions")

        try:
            self.ui.buttonBox.accepted.disconnect()
        except TypeError:
            pass
        self.ui.buttonBox.accepted.connect(self.open_external_file)

    # Closes this dialog and transfers control to the analysis window.
    def open_external_file(self) -> None:
        """Close the instructions dialog and open the external analysis window."""

        from sim_spr_lmr.presentation.qt.dialogs.external_file_analysis_window import (
            ExternalFileAnalysisWindow,
        )

        self.close()
        self.external_window = ExternalFileAnalysisWindow()
        self.external_window.show()
