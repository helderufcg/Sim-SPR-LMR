"""Behavior wrapper for external-curve loading, analysis, and plotting."""

from __future__ import annotations

import os

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from numpy import arange
import matplotlib.pyplot as plt
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

from open_extern_file import Ui_Widget


# These styles reflect whether each external curve slot is loaded or available.
LOAD_BUTTON_ENABLED_STYLE = """
QPushButton{
    font: 400 11pt "Ubuntu";
    color: rgb(255, 255,255);
    background-color: rgb(0, 130, 180);
    border-color: rgb(0, 100, 130);
    border-style: outset;
    border-width: 2px;
    border-radius:5px;
}

QPushButton:hover{
    background-color: rgb(00, 140, 70);
    border-color: rgb(0, 120, 40);
}
"""

LOAD_BUTTON_DISABLED_STYLE = """
QPushButton{
    color: rgb(255, 255,255);
    background-color: #606060;
    border-color: #404040;
    border-style: outset;
    border-width: 2px;
    border-radius:5px;
}

QPushButton:hover{
    background-color: rgb(180, 20, 20);
    border-color: rgb(150, 25, 20);
}
"""

REMOVE_BUTTON_ENABLED_STYLE = """
QPushButton{
    color: rgb(255, 255,255);
    background-color: rgb(0, 130, 180);
    border-color: rgb(0, 100, 130);
    border-style: outset;
    border-width: 3px;
    border-radius:10px;
}
QPushButton:hover{
    background-color: rgb(180, 20, 20);
    border-color: rgb(150, 25, 20);
}
"""

REMOVE_BUTTON_DISABLED_STYLE = """
QPushButton{
    color: rgb(255, 255,255);
    background-color: #606060;
    border-color: #404040;
    border-style: outset;
    border-width: 3px;
    border-radius:10px;
}
"""


# Loads external curves, calculates resonance metrics, and plots the datasets.
class ExternalFileAnalysisWindow(QtWidgets.QWidget):
    """Load up to two curves from files, plot them, and show SPR metrics."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent, QtCore.Qt.Window)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self._expose_ui_members()

        self.n_file = [0, 0]
        self.graphs = [None, None]
        self.res_angle_1 = 0.0
        self.res_angle_2 = 0.0

        self.setWindowIcon(QtGui.QIcon(":/icons/icons/LOGO.png"))
        self.setWindowTitle("Sim-LMR - External File Analyse")
        self.setMinimumSize(QtCore.QSize(800, 740))

        self.figure = plt.figure(dpi=250)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.verticalLayout_2.addWidget(self.canvas)
        self.verticalLayout_3.addWidget(self.toolbar)

        self.set_enable(self.btn_load_1, self.btn_remove_1)
        self.set_enable(self.btn_load_2, self.btn_remove_2)

        self.btn_load_1.clicked.connect(self.open_1)
        self.btn_load_2.clicked.connect(self.open_2)
        self.spin_delta_index.valueChanged.connect(self.sensibility)
        self.btn_remove_1.clicked.connect(self.remove_file_1)
        self.btn_remove_2.clicked.connect(self.remove_file_2)

    def _expose_ui_members(self) -> None:
        """Keep old self.widget_name access while behavior moves out of pyuic."""

        for name, value in vars(self.ui).items():
            setattr(self, name, value)

    def open_1(self) -> None:
        self.n_file[0] = 1
        self.open_file(self.checkBox_file1, self.label_title1)

    def open_2(self) -> None:
        self.n_file[1] = 1
        self.open_file(self.checkBox_file2, self.label_title2)

    # Reads the selected file, validates its first two columns, and updates the slot.
    def open_file(self, checkbox: QtWidgets.QCheckBox, label_title: QtWidgets.QLabel) -> None:
        try:
            path_1 = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open File",
                filter="Text Files (*.txt) ;; CSV Files (*.csv)",
            )[0]

            if path_1:
                checkbox.setChecked(True)
                label_title.setHidden(False)
                label_title.setText(f"Name: {os.path.basename(path_1)}")
            else:
                label_title.setHidden(False)
                label_title.setText(
                    QtCore.QCoreApplication.translate(
                        "Widget",
                        '<html><head/><body><p align="center"><span style=" font-weight:400; color:#d41010;">'
                        "Error opening file. check the format!</span></p></body></html>",
                        None,
                    )
                )

            try:
                df = pd.read_csv(path_1, encoding="latin1")
                x, y = self._curve_columns_from_dataframe(df)

                if self.n_file == [1, 0]:
                    self.print_parameters_1(x, y, self.Qline_fwhm, self.Qline_min_ref, self.Qline_resonance)
                    self.set_desable(self.btn_load_1, self.btn_remove_1)
                    self.show_graph(x, y, "blue", "Curve 1")
                    self.graphs[0] = [x, y]

                if self.n_file == [0, 1]:
                    self.print_parameters_1(x, y, self.Qline_fwhm_2, self.Qline_min_ref_2, self.Qline_resonance_2)
                    self.set_desable(self.btn_load_2, self.btn_remove_2)
                    self.show_graph(x, y, "red", "Curve 2")
                    self.graphs[1] = [x, y]

                if self.n_file == [1, 1]:
                    if self.Qline_resonance.text() == "":
                        self.print_parameters_2(
                            x,
                            y,
                            self.Qline_fwhm,
                            self.Qline_min_ref,
                            self.Qline_resonance,
                            self.Qline_delta_res,
                            self.spin_delta_index,
                            self.Qline_sensibility,
                            self.Qline_QF,
                        )
                        self.set_desable(self.btn_load_1, self.btn_remove_1)
                        self.graphs[0] = [x, y]
                        self.show_graph(x, y, "blue", "Curve 1")

                    if self.Qline_resonance_2.text() == "":
                        self.print_parameters_2(
                            x,
                            y,
                            self.Qline_fwhm_2,
                            self.Qline_min_ref_2,
                            self.Qline_resonance_2,
                            self.Qline_delta_res,
                            self.spin_delta_index,
                            self.Qline_sensibility,
                            self.Qline_QF,
                        )
                        self.set_desable(self.btn_load_2, self.btn_remove_2)
                        self.graphs[1] = [x, y]
                        self.show_graph(x, y, "red", "Curve 2")

            except Exception:
                label_title.setHidden(False)
                label_title.setText(
                    QtCore.QCoreApplication.translate(
                        "Widget",
                        '<html><head/><body><p align="center"><span style=" font-weight:400; color:#d41010;">'
                        "Error reading file. Check the format!</span></p></body></html>",
                        None,
                    )
                )

        except Exception:
            label_title.setHidden(False)
            label_title.setText(
                QtCore.QCoreApplication.translate(
                    "Widget",
                    '<html><head/><body><p align="center"><span style=" font-weight:400; color:#d41010;">'
                    "Error opening file!</span></p></body></html>",
                    None,
                )
                )

    # Draws the loaded curve and refreshes the embedded Matplotlib canvas.
    def show_graph(self, x, y, colors: str, labels: str) -> None:
        font = {"size": 5, "family": "Sans-Serif"}

        self.figure.subplots_adjust(
            left=0.160,
            bottom=0.195,
            right=0.930,
            top=0.950,
            wspace=0.1,
            hspace=0.2,
        )

        axes = self.figure.gca()
        axes.plot(x, y, color=colors, label=labels)
        axes.grid(True, alpha=0.3)
        axes.set_ylabel("Reflectance", fontdict=font)
        axes.set_yticks(arange(0, 1.2, step=0.2))
        axes.tick_params(axis="both", labelsize=5)
        axes.legend()

        self.canvas.draw()

    def set_desable(self, btn_load: QtWidgets.QPushButton, btn_remove: QtWidgets.QPushButton) -> None:
        btn_load.setEnabled(False)
        btn_load.setStyleSheet(LOAD_BUTTON_DISABLED_STYLE)
        btn_remove.setEnabled(True)
        btn_remove.setStyleSheet(REMOVE_BUTTON_ENABLED_STYLE)

    def _curve_columns_from_dataframe(self, dataframe: pd.DataFrame) -> tuple[list[float], list[float]]:
        if dataframe.shape[1] < 2:
            raise ValueError("External curve files must have at least two columns.")

        curve = dataframe.iloc[:, :2].apply(pd.to_numeric, errors="coerce").dropna()
        if curve.empty:
            raise ValueError("External curve files must contain numeric X and Y values.")

        return curve.iloc[:, 0].tolist(), curve.iloc[:, 1].tolist()

    # Extracts resonance position, minimum reflectance, and FWHM from a curve.
    def _resonance_parameters(self, x_axis, y_axis) -> tuple[float, float, float]:
        if len(x_axis) != len(y_axis) or len(x_axis) < 3:
            raise ValueError("External curve files must contain at least three points.")

        id_resonance = min(range(len(y_axis)), key=lambda index: y_axis[index])
        x1, x2, _id1, _id2, _y_med = self.defFWHM(x_axis, y_axis)

        return x_axis[id_resonance], min(y_axis), abs(x2 - x1)

    def print_parameters_1(
        self,
        x_axis,
        y_axis,
        fwhm: QtWidgets.QLineEdit,
        min_reflectance: QtWidgets.QLineEdit,
        resonance_point: QtWidgets.QLineEdit,
    ) -> None:
        self.res_angle_1, min_value, width = self._resonance_parameters(x_axis, y_axis)

        fwhm.setText(f"{width:.6f}")
        min_reflectance.setText(f"{min_value:.6f}")
        resonance_point.setText(f"{self.res_angle_1:.6f}")

    def print_parameters_2(
        self,
        x_axis,
        y_axis,
        fwhm: QtWidgets.QLineEdit,
        min_reflectance: QtWidgets.QLineEdit,
        resonance_point: QtWidgets.QLineEdit,
        delta_res: QtWidgets.QLineEdit,
        delta_index: QtWidgets.QDoubleSpinBox,
        sensibility: QtWidgets.QLineEdit,
        qf: QtWidgets.QLineEdit,
    ) -> None:
        self.res_angle_2, min_value, width = self._resonance_parameters(x_axis, y_axis)

        delta_resonance = abs(self.res_angle_2 - self.res_angle_1)

        fwhm.setText(f"{width:.6f}")
        min_reflectance.setText(f"{min_value:.6f}")
        resonance_point.setText(f"{self.res_angle_2:.6f}")
        delta_res.setText(f"{delta_resonance:.6f}")

        delta_analyte = delta_index.value()
        sens = delta_resonance / delta_analyte
        sensibility.setText(f"{sens:.6f}")

        qf.setText(f"{(sens / width):.6f}")

    def sensibility(self, *_args) -> None:
        if not self.Qline_fwhm_2.text():
            return

        delta_resonance = abs(self.res_angle_2 - self.res_angle_1)
        delta_analyte = self.spin_delta_index.value()
        sens = delta_resonance / delta_analyte
        self.Qline_sensibility.setText(f"{sens:.6f}")
        fwhm = float(self.Qline_fwhm_2.text().replace(",", "."))
        self.Qline_QF.setText(f"{(sens / fwhm):.6f}")

    # Finds half-maximum crossings used to calculate the resonance width.
    def defFWHM(self, theta_i, curve):
        x = list(theta_i)
        y = list(curve)

        try:
            id_min = y.index(min(y))

            y_min = y[id_min]
            left_base = max(y[: id_min + 1])
            right_base = max(y[id_min:])
            y_base = min(left_base, right_base)
            y_med = y_min + (y_base - y_min) / 2

            id_left = None
            for i in range(id_min - 1, -1, -1):
                if y[i] > y_med and y[i + 1] <= y_med:
                    id_left = i
                    break

            id_right = None
            for i in range(id_min, len(y) - 1):
                if y[i] <= y_med and y[i + 1] > y_med:
                    id_right = i
                    break

            if id_left is None or id_right is None:
                id_fallback = 1 if len(y) > 1 else 0
                return 0.0, 1.0, 0, id_fallback, y_med

            x1 = x[id_left] + (x[id_left + 1] - x[id_left]) * (
                (y_med - y[id_left]) / (y[id_left + 1] - y[id_left])
            )
            x2 = x[id_right] + (x[id_right + 1] - x[id_right]) * (
                (y_med - y[id_right]) / (y[id_right + 1] - y[id_right])
            )

            return x1, x2, id_left, id_right, y_med
        except Exception:
            return 0.0, 1.0, 0, 1, 0.5

    def remove_file_1(self) -> None:
        self.n_file[0] = 0
        self.remove_file()

    def remove_file_2(self) -> None:
        self.n_file[1] = 0
        self.remove_file()

    def remove_file(self) -> None:
        if self.n_file == [0, 1]:
            self.set_enable(self.btn_load_1, self.btn_remove_1)
            self.checkBox_file1.setChecked(False)
            self.label_title1.setText("Empty")

            self.Qline_resonance.clear()
            self.Qline_fwhm.clear()
            self.Qline_min_ref.clear()

            self.Qline_delta_res.clear()
            self.Qline_sensibility.clear()
            self.Qline_QF.clear()

            self.figure.clear()
            if self.graphs[1] is not None:
                self.show_graph(self.graphs[1][0], self.graphs[1][1], "red", "Curve 2")

        if self.n_file == [1, 0]:
            self.set_enable(self.btn_load_2, self.btn_remove_2)
            self.checkBox_file2.setChecked(False)
            self.label_title2.setText("Empty")

            self.Qline_resonance_2.clear()
            self.Qline_fwhm_2.clear()
            self.Qline_min_ref_2.clear()

            self.Qline_delta_res.clear()
            self.Qline_sensibility.clear()
            self.Qline_QF.clear()

            self.figure.clear()
            if self.graphs[0] is not None:
                self.show_graph(self.graphs[0][0], self.graphs[0][1], "blue", "Curve 1")

        if self.n_file == [0, 0]:
            if self.Qline_resonance.text() == "":
                self.set_enable(self.btn_load_2, self.btn_remove_2)
                self.checkBox_file2.setChecked(False)
                self.label_title2.setText("Empty")

                self.Qline_resonance_2.clear()
                self.Qline_fwhm_2.clear()
                self.Qline_min_ref_2.clear()

            if self.Qline_resonance_2.text() == "":
                self.set_enable(self.btn_load_1, self.btn_remove_1)
                self.checkBox_file1.setChecked(False)
                self.label_title1.setText("Empty")

                self.Qline_resonance.clear()
                self.Qline_fwhm.clear()
                self.Qline_min_ref.clear()

            self.figure.clear()
            self.canvas.draw()

    def set_enable(self, btn_load: QtWidgets.QPushButton, btn_remove: QtWidgets.QPushButton) -> None:
        btn_load.setEnabled(True)
        btn_load.setStyleSheet(LOAD_BUTTON_ENABLED_STYLE)
        btn_remove.setEnabled(False)
        btn_remove.setStyleSheet(REMOVE_BUTTON_DISABLED_STYLE)
