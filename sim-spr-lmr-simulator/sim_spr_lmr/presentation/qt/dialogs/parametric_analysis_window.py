"""Configure, execute, plot, and export a parametric resonance analysis."""

from __future__ import annotations

from collections.abc import Sequence

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import colormaps
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.figure import Figure
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

from sim_spr_lmr.application import (
    ParametricAnalysisInput,
    build_inclusive_sweep_values,
    run_parametric_analysis,
)
from sim_spr_lmr.core.domain import ParametricAnalysisResult, SimulationConfig
from sim_spr_lmr.infrastructure.exporters import write_parametric_analysis_exports


NAVY = "#0a195a"
MUTED = "#637381"
BUTTON_STYLE = """
QPushButton { min-height: 34px; padding: 0 18px; color: white;
background: #0082b4; border: 1px solid #006482; border-radius: 7px; font-weight: 600; }
QPushButton:hover { background: #008c46; border-color: #007828; }
QPushButton:disabled { background: #737b83; border-color: #626970; color: #e6e9ec; }
"""


# Runs the CPU-bound sweep away from the Qt event thread.
class _ParametricAnalysisWorker(QtCore.QObject):
    completed = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)
    progress_changed = QtCore.pyqtSignal(int)
    message_changed = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self, request: ParametricAnalysisInput) -> None:
        super().__init__()
        self.request = request

    @QtCore.pyqtSlot()
    def run(self) -> None:
        try:
            result = run_parametric_analysis(
                self.request,
                progress_callback=self.progress_changed.emit,
                log_callback=self.message_changed.emit,
            )
            self.completed.emit(result)
        except Exception as error:
            self.failed.emit(str(error))
        finally:
            self.finished.emit()


# Provides controls, progress feedback, plots, and exports for parameter sweeps.
class ParametricAnalysisWindow(QtWidgets.QWidget):
    """Run one-dimensional sweeps without mutating the conventional workflow."""

    THICKNESS = "thickness"
    INCIDENCE_ANGLE = "incidence_angle"

    def __init__(
        self,
        *,
        layers: Sequence[dict[str, object]] = (),
        thicknesses_m: Sequence[float] = (),
        analyte_indices: Sequence[complex] = (),
        analyte_step: float | None = None,
        coupling: str = "Unknown",
        interrogation_mode: str = "Unknown",
        incidence_angle_deg: float | None = None,
        simulation_config: SimulationConfig | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent, QtCore.Qt.Window)
        self.setObjectName("parametric_analysis_window")
        self.setWindowTitle("Sim-LMR - Parametric Resonance Analysis")
        self.setWindowIcon(QtGui.QIcon(":/icons/icons/LOGO.png"))
        self.resize(1280, 800)
        self.setMinimumSize(1040, 680)
        self._layers: list[dict[str, object]] = []
        self._thicknesses_m: list[float] = []
        self._coupling = "Unknown"
        self._interrogation_mode = "Unknown"
        self._incidence_angle_deg: float | None = None
        self._analyte_step: float | None = None
        self._base_config: SimulationConfig | None = None
        self._analysis_result: ParametricAnalysisResult | None = None
        self._worker: _ParametricAnalysisWorker | None = None
        self._worker_thread: QtCore.QThread | None = None
        self._status_state = "warning"
        self._build_ui()
        self.refresh_context(
            layers=layers,
            thicknesses_m=thicknesses_m,
            analyte_indices=analyte_indices,
            analyte_step=analyte_step,
            coupling=coupling,
            interrogation_mode=interrogation_mode,
            incidence_angle_deg=incidence_angle_deg,
            simulation_config=simulation_config,
        )

    # Builds configuration controls, graph canvases, and status widgets.
    def _build_ui(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#parametric_analysis_window {{ background: white; }}
            QLabel#window_title {{ color: white; font-size: 22px; font-weight: 700; }}
            QLabel#window_subtitle {{ color: #d8eff9; font-size: 12px; }}
            QLabel#section_title {{ color: {NAVY}; font-size: 15px; font-weight: 700; }}
            QGroupBox {{ color: {NAVY}; font-weight: 700; border: 1px solid #c9d6df;
            border-radius: 8px; margin-top: 12px; padding-top: 10px; background: #f5f8fb; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
            QComboBox, QDoubleSpinBox {{ min-height: 30px; padding: 0 7px; background: white;
            border: 1px solid #aabac5; border-radius: 5px; }}
            QTabWidget::pane {{ border: 1px solid #c9d6df; border-radius: 6px; }}
            QTabBar::tab {{
                padding: 8px 18px;
                margin-right: 4px;
                min-width: 230px;
                color: {NAVY};
                border: 1px solid #c9d6df;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                background: #eef2f5;
            }}
            QTabBar::tab:selected {{ background: #dceef7; font-weight: 700; }}
            """
        )
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        header = QtWidgets.QFrame(self)
        header.setStyleSheet(f"background: {NAVY};")
        header_layout = QtWidgets.QVBoxLayout(header)
        header_layout.setContentsMargins(28, 17, 28, 17)
        title = QtWidgets.QLabel("Parametric Resonance Analysis", header)
        title.setObjectName("window_title")
        subtitle = QtWidgets.QLabel(
            "Configure a one-dimensional sweep while keeping the analyte refractive index fixed.",
            header,
        )
        subtitle.setObjectName("window_subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        body = QtWidgets.QHBoxLayout()
        body.setContentsMargins(22, 18, 22, 14)
        body.setSpacing(18)
        root.addLayout(body, 1)

        controls = QtWidgets.QFrame(self)
        controls.setMinimumWidth(315)
        controls.setMaximumWidth(390)
        controls_layout = QtWidgets.QVBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)
        self.preview_notice = QtWidgets.QLabel(
            "Run the conventional simulation once to establish the optical configuration.",
            controls,
        )
        self.preview_notice.setWordWrap(True)
        self.preview_notice.setStyleSheet(
            "background: #fff7d6; color: #694f00; border: 1px solid #e1c75b; "
            "border-radius: 6px; padding: 9px;"
        )
        controls_layout.addWidget(self.preview_notice)

        context_group = QtWidgets.QGroupBox("Simulation context", controls)
        context_form = QtWidgets.QFormLayout(context_group)
        self.coupling_value = QtWidgets.QLabel("Unknown", context_group)
        self.coupling_value.setObjectName("coupling_value")
        self.mode_value = QtWidgets.QLabel("Unknown", context_group)
        self.mode_value.setObjectName("interrogation_mode_value")
        context_form.addRow("Coupling:", self.coupling_value)
        context_form.addRow("Interrogation:", self.mode_value)
        controls_layout.addWidget(context_group)

        sweep_group = QtWidgets.QGroupBox("Sweep configuration", controls)
        sweep_form = QtWidgets.QFormLayout(sweep_group)
        self.parameter_selector = QtWidgets.QComboBox(sweep_group)
        self.parameter_selector.setObjectName("parameter_selector")
        self.parameter_selector.addItem("Layer thickness", self.THICKNESS)
        self.parameter_selector.addItem("Incidence angle", self.INCIDENCE_ANGLE)
        sweep_form.addRow("Parameter:", self.parameter_selector)
        self.layer_label = QtWidgets.QLabel("Layer:", sweep_group)
        self.layer_selector = QtWidgets.QComboBox(sweep_group)
        self.layer_selector.setObjectName("layer_selector")
        sweep_form.addRow(self.layer_label, self.layer_selector)
        self.initial_value = self._new_value_spinbox("initial_value", sweep_group)
        self.final_value = self._new_value_spinbox("final_value", sweep_group)
        self.step_value = self._new_value_spinbox("step_value", sweep_group)
        sweep_form.addRow("Initial:", self.initial_value)
        sweep_form.addRow("Final:", self.final_value)
        sweep_form.addRow("Step:", self.step_value)
        controls_layout.addWidget(sweep_group)

        analyte_group = QtWidgets.QGroupBox("Fixed analyte", controls)
        analyte_layout = QtWidgets.QVBoxLayout(analyte_group)
        analyte_help = QtWidgets.QLabel(
            "The selected index is the fixed reference. Sensitivity uses it and "
            "the next conventional analyte step.",
            analyte_group,
        )
        analyte_help.setWordWrap(True)
        analyte_help.setStyleSheet(f"color: {MUTED}; font-weight: 400;")
        self.analyte_selector = QtWidgets.QComboBox(analyte_group)
        self.analyte_selector.setObjectName("fixed_analyte_selector")
        analyte_layout.addWidget(analyte_help)
        analyte_layout.addWidget(self.analyte_selector)
        controls_layout.addWidget(analyte_group)

        self.availability_note = QtWidgets.QLabel(controls)
        self.availability_note.setObjectName("parameter_availability_note")
        self.availability_note.setWordWrap(True)
        self.availability_note.setStyleSheet(f"color: {MUTED};")
        controls_layout.addWidget(self.availability_note)
        self.progress_bar = QtWidgets.QProgressBar(controls)
        self.progress_bar.setObjectName("parametric_analysis_progress")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        controls_layout.addWidget(self.progress_bar)
        controls_layout.addStretch(1)
        self.run_button = QtWidgets.QPushButton("Run parametric analysis", controls)
        self.run_button.setObjectName("run_parametric_analysis_button")
        self.run_button.setEnabled(False)
        self.run_button.setToolTip(
            "Available after a conventional simulation is completed successfully. "
            "The parametric analysis reuses its optical configuration."
        )
        self.run_button.setStyleSheet(BUTTON_STYLE)
        controls_layout.addWidget(self.run_button)
        body.addWidget(controls)

        outputs = QtWidgets.QFrame(self)
        outputs_layout = QtWidgets.QVBoxLayout(outputs)
        outputs_layout.setContentsMargins(0, 0, 0, 0)
        outputs_layout.setSpacing(10)
        outputs_title = QtWidgets.QLabel("Analysis outputs", outputs)
        outputs_title.setObjectName("section_title")
        outputs_layout.addWidget(outputs_title)
        self.output_tabs = QtWidgets.QTabWidget(outputs)
        self.output_tabs.setObjectName("parametric_output_tabs")
        self.output_tabs.tabBar().setElideMode(QtCore.Qt.ElideNone)
        self.output_tabs.tabBar().setExpanding(False)
        self.output_tabs.tabBar().setUsesScrollButtons(False)
        self.spectra_tab = QtWidgets.QWidget()
        self.metrics_tab = QtWidgets.QWidget()
        self.sensitivity_tab = QtWidgets.QWidget()
        self.output_tabs.addTab(self.spectra_tab, "Spectra")
        self.output_tabs.addTab(self.metrics_tab, "Resonance position and FWHM")
        self.output_tabs.addTab(self.sensitivity_tab, "Sensitivity and FOM")
        outputs_layout.addWidget(self.output_tabs, 1)

        spectra_layout = QtWidgets.QVBoxLayout(self.spectra_tab)
        spectra_layout.setContentsMargins(18, 18, 18, 18)
        self.spectra_figure = Figure(dpi=100, tight_layout={"pad": 2.2})
        self.spectra_canvas = FigureCanvas(self.spectra_figure)
        self.spectra_canvas.setObjectName("spectra_canvas")
        spectra_layout.addWidget(self.spectra_canvas)
        metrics_layout = QtWidgets.QVBoxLayout(self.metrics_tab)
        metrics_layout.setContentsMargins(18, 18, 18, 18)
        self.metrics_figure = Figure(
            dpi=100,
            tight_layout={"pad": 2.2, "h_pad": 2.8},
        )
        self.metrics_canvas = FigureCanvas(self.metrics_figure)
        self.metrics_canvas.setObjectName("resonance_metrics_canvas")
        metrics_layout.addWidget(self.metrics_canvas)

        sensitivity_layout = QtWidgets.QVBoxLayout(self.sensitivity_tab)
        sensitivity_layout.setContentsMargins(18, 18, 18, 18)
        self.sensitivity_figure = Figure(
            dpi=100,
            tight_layout={"pad": 2.2, "h_pad": 2.8},
        )
        self.sensitivity_canvas = FigureCanvas(self.sensitivity_figure)
        self.sensitivity_canvas.setObjectName("sensitivity_quality_factor_canvas")
        sensitivity_layout.addWidget(self.sensitivity_canvas)
        body.addWidget(outputs, 1)

        footer = QtWidgets.QFrame(self)
        footer.setStyleSheet("border-top: 1px solid #d5dfe6; background: #f7fafc;")
        footer_layout = QtWidgets.QHBoxLayout(footer)
        footer_layout.setContentsMargins(22, 10, 22, 10)
        footer_layout.addStretch(1)
        self.export_button = QtWidgets.QPushButton("Export results", footer)
        self.export_button.setObjectName("export_parametric_results_button")
        self.export_button.setEnabled(False)
        self.export_button.setToolTip("Export will be enabled after results are available.")
        self.export_button.setStyleSheet(BUTTON_STYLE)
        close_button = QtWidgets.QPushButton("Close", footer)
        close_button.setObjectName("close_parametric_analysis_button")
        close_button.setStyleSheet(BUTTON_STYLE)
        close_button.clicked.connect(self.close)
        footer_layout.addWidget(self.export_button)
        footer_layout.addWidget(close_button)
        root.addWidget(footer)

        self.parameter_selector.currentIndexChanged.connect(self._sync_parameter_controls)
        self.layer_selector.currentIndexChanged.connect(self._sync_thickness_defaults)
        self.parameter_selector.currentIndexChanged.connect(self._invalidate_analysis_result)
        self.layer_selector.currentIndexChanged.connect(self._invalidate_analysis_result)
        self.analyte_selector.currentIndexChanged.connect(self._invalidate_analysis_result)
        for spinbox in (self.initial_value, self.final_value, self.step_value):
            spinbox.valueChanged.connect(self._invalidate_analysis_result)
        self.run_button.clicked.connect(self._start_analysis)
        self.export_button.clicked.connect(self._export_results)
        self._draw_empty_graphs()

    @staticmethod
    def _new_value_spinbox(
        object_name: str,
        parent: QtWidgets.QWidget,
    ) -> QtWidgets.QDoubleSpinBox:
        spinbox = QtWidgets.QDoubleSpinBox(parent)
        spinbox.setObjectName(object_name)
        spinbox.setDecimals(2)
        spinbox.setRange(0.0, 1_000_000.0)
        spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        return spinbox

    # Refreshes sweep choices from the current conventional simulation context.
    def refresh_context(
        self,
        *,
        layers: Sequence[dict[str, object]],
        thicknesses_m: Sequence[float],
        analyte_indices: Sequence[complex],
        analyte_step: float | None = None,
        coupling: str,
        interrogation_mode: str,
        incidence_angle_deg: float | None,
        simulation_config: SimulationConfig | None = None,
    ) -> None:
        """Refresh selectors from the current main-window configuration."""

        self._layers = [dict(layer) for layer in layers]
        self._thicknesses_m = [float(value) for value in thicknesses_m]
        self._coupling = coupling
        self._interrogation_mode = interrogation_mode
        self._incidence_angle_deg = incidence_angle_deg
        self._base_config = simulation_config
        self._analyte_step = self._resolve_analyte_step(
            analyte_step,
            simulation_config.analyte_indices if simulation_config is not None else (),
            analyte_indices,
        )
        self.coupling_value.setText(coupling)
        self.mode_value.setText(interrogation_mode)
        self._populate_layers()
        self._populate_analytes(analyte_indices)
        self._sync_angle_availability()
        self._sync_parameter_controls()
        self._invalidate_analysis_result()
        self._sync_run_button_availability()

    def _populate_layers(self) -> None:
        self.layer_selector.blockSignals(True)
        self.layer_selector.clear()
        for index, layer in enumerate(self._layers):
            material = str(layer.get("material", "")).strip() or f"Layer {index + 1}"
            if material.casefold() == "analyte":
                continue
            if self._coupling == "Prism" and index == 0:
                continue
            thickness_m = self._thicknesses_m[index] if index < len(self._thicknesses_m) else 0.0
            self.layer_selector.addItem(
                f"Layer {index + 1} — {material} ({thickness_m * 1e9:.4g} nm)",
                {"index": index, "thickness_nm": thickness_m * 1e9},
            )
        if self.layer_selector.count() == 0:
            self.layer_selector.addItem("No finite coating layer available", None)
            self.layer_selector.setEnabled(False)
        else:
            self.layer_selector.setEnabled(True)
        self.layer_selector.blockSignals(False)
        self._sync_thickness_defaults()

    def _populate_analytes(self, analyte_indices: Sequence[complex]) -> None:
        self.analyte_selector.clear()
        for analyte_index in analyte_indices:
            value = complex(analyte_index)
            label = f"{value.real:.6g} RIU"
            if abs(value.imag) > 0.0:
                label = f"{value.real:.6g} {value.imag:+.6g}j RIU"
            self.analyte_selector.addItem(label, value)
        if self.analyte_selector.count() == 0:
            self.analyte_selector.addItem("No analyte index available", None)
            self.analyte_selector.setEnabled(False)
        else:
            self.analyte_selector.setEnabled(True)

    @staticmethod
    def _resolve_analyte_step(
        explicit_step: float | None,
        *index_sequences: Sequence[complex],
    ) -> float | None:
        if (
            explicit_step is not None
            and np.isfinite(explicit_step)
            and explicit_step > 0.0
        ):
            return float(explicit_step)
        for indices in index_sequences:
            for left, right in zip(indices[:-1], indices[1:], strict=False):
                candidate = abs(complex(right).real - complex(left).real)
                if np.isfinite(candidate) and candidate > 0.0:
                    return float(candidate)
        return None

    def _sync_angle_availability(self) -> None:
        angle_available = self._coupling == "Prism" and self._interrogation_mode == "WIM"
        angle_item = self.parameter_selector.model().item(1)
        angle_item.setEnabled(angle_available)
        if angle_available:
            self.availability_note.setText(
                "Incidence-angle sweep is available because the current configuration uses Prism + WIM."
            )
            return
        if self.parameter_selector.currentData() == self.INCIDENCE_ANGLE:
            self.parameter_selector.setCurrentIndex(0)
        self.availability_note.setText(
            "Incidence-angle sweep is available only for prism coupling in WIM."
        )

    def _sync_parameter_controls(self, *_args: object) -> None:
        is_thickness = self.parameter_selector.currentData() == self.THICKNESS
        self.layer_label.setVisible(is_thickness)
        self.layer_selector.setVisible(is_thickness)
        for spinbox in (self.initial_value, self.final_value, self.step_value):
            spinbox.setSuffix(" nm" if is_thickness else " °")
            spinbox.setRange(0.0, 1_000_000.0 if is_thickness else 89.9999)
        if is_thickness:
            self._sync_thickness_defaults()
        else:
            angle = max(0.0, min(float(self._incidence_angle_deg or 0.0), 89.9999))
            self.initial_value.setValue(angle)
            self.final_value.setValue(min(angle + 1.0, 89.9999))
            self.step_value.setValue(0.1)
        self._sync_graph_axis_labels()

    def _sync_thickness_defaults(self, *_args: object) -> None:
        if self.parameter_selector.currentData() != self.THICKNESS:
            return
        layer_data = self.layer_selector.currentData()
        thickness = float(layer_data.get("thickness_nm", 0.0)) if isinstance(layer_data, dict) else 0.0
        self.initial_value.setValue(thickness)
        self.final_value.setValue(thickness + 10.0)
        self.step_value.setValue(1.0)

    def _sync_run_button_availability(self) -> None:
        if self._worker_thread is not None:
            self.run_button.setEnabled(False)
            return
        layer_data = self.layer_selector.currentData()
        fixed_analyte = self.analyte_selector.currentData()
        is_thickness = self.parameter_selector.currentData() == self.THICKNESS
        ready = bool(
            self._base_config is not None
            and fixed_analyte is not None
            and self._analyte_step is not None
            and self._analyte_step > 0.0
            and (not is_thickness or isinstance(layer_data, dict))
        )
        self.run_button.setEnabled(ready)
        self.run_button.setToolTip(
            "Run the parameter sweep; sensitivity uses the selected analyte index "
            "and the next conventional analyte step."
            if ready
            else (
                "Available after a conventional simulation is completed successfully. "
                "The parametric analysis reuses its optical configuration."
            )
        )
        if self._base_config is None:
            self._set_status(
                "Run the conventional simulation once to establish the optical configuration.",
                "warning",
            )
        elif self._analyte_step is None or self._analyte_step <= 0.0:
            self._set_status(
                "Set a positive analyte step in the conventional simulation to calculate sensitivity.",
                "warning",
            )
        elif self._analysis_result is None and self._status_state != "error":
            self._set_status("Ready to run the parametric analysis.", "ready")

    def _invalidate_analysis_result(self, *_args: object) -> None:
        if self._worker_thread is not None:
            return
        self._status_state = ""
        self._analysis_result = None
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self._draw_empty_graphs()
        self._sync_graph_axis_labels()
        self._sync_run_button_availability()

    # Validates the sweep request and starts it in a worker thread.
    def _start_analysis(self) -> None:
        if self._base_config is None:
            self._set_status("Run the conventional simulation first.", "error")
            return
        try:
            parameter_values = build_inclusive_sweep_values(
                self.initial_value.value(),
                self.final_value.value(),
                self.step_value.value(),
            )
            fixed_analyte = self.analyte_selector.currentData()
            if fixed_analyte is None:
                raise ValueError("Select a fixed analyte refractive index.")
            layer_data = self.layer_selector.currentData()
            layer_index = (
                int(layer_data["index"])
                if self.parameter_selector.currentData() == self.THICKNESS
                and isinstance(layer_data, dict)
                else None
            )
            request = ParametricAnalysisInput(
                base_config=self._base_config,
                parameter_kind=str(self.parameter_selector.currentData()),
                parameter_values=parameter_values,
                fixed_analyte_index=complex(fixed_analyte),
                layer_index=layer_index,
                analyte_step=self._analyte_step,
            )
        except (KeyError, TypeError, ValueError) as error:
            self._set_status(str(error), "error")
            return

        self._analysis_result = None
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._set_running(True)
        self._set_status("Starting parametric analysis...", "running")

        self._worker_thread = QtCore.QThread(self)
        self._worker = _ParametricAnalysisWorker(request)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress_changed.connect(self.progress_bar.setValue)
        self._worker.message_changed.connect(
            lambda message: self._set_status(message, "running")
        )
        self._worker.completed.connect(self._handle_analysis_completed)
        self._worker.failed.connect(self._handle_analysis_failed)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._handle_worker_thread_finished)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

    @QtCore.pyqtSlot(object)
    # Displays completed tracks and enables result export.
    def _handle_analysis_completed(self, result: ParametricAnalysisResult) -> None:
        self._analysis_result = result
        self.progress_bar.setValue(100)
        self._render_analysis_result(result)
        self.export_button.setEnabled(True)
        self._set_status(
            f"Analysis completed in {result.runtime_seconds:.3f} s. "
            f"Tracked resonances: {len(result.resonance_tracks)}.",
            "success",
        )

    @QtCore.pyqtSlot(str)
    def _handle_analysis_failed(self, message: str) -> None:
        self._analysis_result = None
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self._set_status(f"Analysis error: {message}", "error")

    @QtCore.pyqtSlot()
    def _handle_worker_thread_finished(self) -> None:
        self._worker = None
        self._worker_thread = None
        self._set_running(False)
        self._sync_run_button_availability()

    def _set_running(self, running: bool) -> None:
        self.parameter_selector.setEnabled(not running)
        self.analyte_selector.setEnabled(not running and self.analyte_selector.currentData() is not None)
        self.layer_selector.setEnabled(
            not running
            and self.parameter_selector.currentData() == self.THICKNESS
            and isinstance(self.layer_selector.currentData(), dict)
        )
        for spinbox in (self.initial_value, self.final_value, self.step_value):
            spinbox.setEnabled(not running)
        self.run_button.setEnabled(False if running else self.run_button.isEnabled())

    # Writes the completed sweep to CSV and companion export files.
    def _export_results(self) -> None:
        if self._analysis_result is None:
            return
        selected_path, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export parametric analysis",
            "parametric_analysis.csv",
            "CSV Files (*.csv)",
        )
        if not selected_path:
            return
        try:
            written_paths = write_parametric_analysis_exports(
                self._analysis_result,
                selected_path,
            )
        except OSError as error:
            self._set_status(f"Export error: {error}", "error")
            return
        self._set_status(
            "Exported: " + ", ".join(path.name for path in written_paths),
            "success",
        )

    def _set_status(self, message: str, state: str) -> None:
        styles = {
            "warning": ("#fff7d6", "#694f00", "#e1c75b"),
            "ready": ("#e8f4fa", "#164e63", "#8bc4dc"),
            "running": ("#e8f4fa", "#164e63", "#8bc4dc"),
            "success": ("#e7f7ed", "#166534", "#86c99a"),
            "error": ("#fdecec", "#991b1b", "#e6a3a3"),
        }
        background, color, border = styles[state]
        self._status_state = state
        self.preview_notice.setText(message)
        self.preview_notice.setStyleSheet(
            f"background: {background}; color: {color}; border: 1px solid {border}; "
            "border-radius: 6px; padding: 9px;"
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._worker_thread is not None:
            self._set_status("Wait for the running analysis to finish before closing.", "warning")
            event.ignore()
            return
        super().closeEvent(event)

    def _draw_empty_graphs(self) -> None:
        self.spectra_figure.clear()
        self.metrics_figure.clear()
        self.sensitivity_figure.clear()
        spectra_axes = self.spectra_figure.add_subplot()
        spectra_axes.set_title("Response spectra")
        spectra_axes.set_xlabel("Wavelength (nm)")
        spectra_axes.set_ylabel("Reflectance / Transmission")
        self._style_graph_axes(spectra_axes)
        self._add_empty_message(spectra_axes)
        resonance_axes = self.metrics_figure.add_subplot(211)
        resonance_axes.set_title("Resonance position vs. swept parameter")
        resonance_axes.set_xlabel("Layer thickness (nm)")
        resonance_axes.set_ylabel("Resonance position")
        self._style_graph_axes(resonance_axes)
        self._add_empty_message(resonance_axes)
        fwhm_axes = self.metrics_figure.add_subplot(212)
        fwhm_axes.set_title("FWHM vs. swept parameter")
        fwhm_axes.set_xlabel("Layer thickness (nm)")
        fwhm_axes.set_ylabel("FWHM")
        self._style_graph_axes(fwhm_axes)
        self._add_empty_message(fwhm_axes)

        sensitivity_axes = self.sensitivity_figure.add_subplot(211)
        sensitivity_axes.set_title("Sensitivity vs. Layer thickness")
        sensitivity_axes.set_xlabel("Layer thickness (nm)")
        sensitivity_axes.set_ylabel("Sensitivity")
        self._style_graph_axes(sensitivity_axes)
        self._add_empty_message(sensitivity_axes)
        quality_factor_axes = self.sensitivity_figure.add_subplot(212)
        quality_factor_axes.set_title("Figure of merit vs. Layer thickness")
        quality_factor_axes.set_xlabel("Layer thickness (nm)")
        quality_factor_axes.set_ylabel("Figure of merit")
        self._style_graph_axes(quality_factor_axes)
        self._add_empty_message(quality_factor_axes)

    # Renders response spectra and tracked resonance metrics in the analysis tabs.
    def _render_analysis_result(self, result: ParametricAnalysisResult) -> None:
        self.spectra_figure.clear()
        spectra_axes = self.spectra_figure.add_subplot()
        parameter_values = np.asarray(result.parameter_values, dtype=float)
        color_minimum = float(np.min(parameter_values))
        color_maximum = float(np.max(parameter_values))
        if np.isclose(color_minimum, color_maximum):
            color_minimum -= 0.5
            color_maximum += 0.5
        color_normalizer = Normalize(vmin=color_minimum, vmax=color_maximum)
        color_map = colormaps["viridis"]
        for parameter_value, response_curve, color in zip(
            result.parameter_values,
            result.response_curves,
            color_map(color_normalizer(parameter_values)),
            strict=False,
        ):
            spectra_axes.plot(
                result.response_axis,
                response_curve,
                color=color,
                linewidth=1.5,
            )
        spectra_axes.set_title(
            f"Response spectra — fixed analyte {result.fixed_analyte_index.real:g} RIU"
        )
        spectra_axes.set_xlabel(
            f"{result.response_axis_label} ({result.response_axis_unit})"
        )
        spectra_axes.set_ylabel(self._response_quantity_label(result.response_quantity))
        self._style_graph_axes(spectra_axes)
        color_scale = self.spectra_figure.colorbar(
            ScalarMappable(norm=color_normalizer, cmap=color_map),
            ax=spectra_axes,
            pad=0.025,
            fraction=0.045,
        )
        color_scale.set_label(result.parameter_axis_label, fontsize=11, labelpad=9)
        color_scale.ax.tick_params(labelsize=10, width=1.1, length=4)
        color_scale.outline.set_linewidth(1.1)
        if len(parameter_values) <= 12:
            color_scale.set_ticks(parameter_values)

        self.metrics_figure.clear()
        resonance_axes = self.metrics_figure.add_subplot(211)
        fwhm_axes = self.metrics_figure.add_subplot(212)
        self._plot_track_metric(
            resonance_axes,
            result,
            "positions",
            f"Resonance position ({result.response_axis_unit})",
            "Resonance position",
        )
        self._plot_track_metric(
            fwhm_axes,
            result,
            "fwhm",
            f"FWHM ({result.response_axis_unit})",
            "FWHM",
        )

        self.sensitivity_figure.clear()
        sensitivity_axes = self.sensitivity_figure.add_subplot(211)
        quality_factor_axes = self.sensitivity_figure.add_subplot(212)
        self._plot_track_metric(
            sensitivity_axes,
            result,
            "sensitivity",
            f"Sensitivity ({result.sensitivity_unit})",
            "Sensitivity",
        )
        self._plot_track_metric(
            quality_factor_axes,
            result,
            "quality_factor",
            f"Figure of merit ({result.quality_factor_unit})",
            "Figure of merit",
        )

        self.spectra_canvas.draw_idle()
        self.metrics_canvas.draw_idle()
        self.sensitivity_canvas.draw_idle()

    @staticmethod
    def _plot_track_metric(
        axes,
        result: ParametricAnalysisResult,
        metric_name: str,
        y_label: str,
        title_prefix: str,
    ) -> None:
        for track in result.resonance_tracks:
            axes.plot(
                result.parameter_values,
                getattr(track, metric_name),
                "-o",
                markersize=3,
                linewidth=1.1,
                label=track.label,
            )
        axes.set_title(f"{title_prefix} vs. {result.parameter_name}")
        axes.set_xlabel(result.parameter_axis_label)
        axes.set_ylabel(y_label)
        ParametricAnalysisWindow._style_graph_axes(axes)
        if result.resonance_tracks:
            axes.legend(fontsize=9)
        else:
            axes.text(
                0.5,
                0.5,
                "No resonance was detected",
                transform=axes.transAxes,
                ha="center",
                va="center",
                color=MUTED,
            )

    @staticmethod
    def _response_quantity_label(response_quantity: str) -> str:
        if response_quantity == "transmission":
            return "Normalized Transmission"
        if response_quantity == "reflectance_db":
            return "Reflectance (dB)"
        return "Reflectance"

    def _sync_graph_axis_labels(self) -> None:
        is_thickness = self.parameter_selector.currentData() == self.THICKNESS
        swept_parameter_name = "Layer thickness" if is_thickness else "Incidence angle"
        swept_parameter_label = "Layer thickness (nm)" if is_thickness else "Incidence angle (°)"

        metric_titles = ("Resonance position", "FWHM")
        for axes, metric_title in zip(self.metrics_figure.axes, metric_titles, strict=False):
            axes.set_title(f"{metric_title} vs. {swept_parameter_name}")
            axes.set_xlabel(swept_parameter_label)

        sensitivity_titles = ("Sensitivity", "Figure of merit")
        for axes, metric_title in zip(
            self.sensitivity_figure.axes,
            sensitivity_titles,
            strict=False,
        ):
            axes.set_title(f"{metric_title} vs. {swept_parameter_name}")
            axes.set_xlabel(swept_parameter_label)

        if self.spectra_figure.axes:
            spectral_axis_label = (
                "Wavelength (nm)"
                if self._interrogation_mode == "WIM"
                else "Incidence angle (°)"
            )
            self.spectra_figure.axes[0].set_xlabel(spectral_axis_label)

        self.spectra_canvas.draw_idle()
        self.metrics_canvas.draw_idle()
        self.sensitivity_canvas.draw_idle()

    @staticmethod
    def _style_graph_axes(axes) -> None:
        axes.title.set_fontsize(13)
        axes.title.set_fontweight("medium")
        axes.title.set_y(1.03)
        axes.xaxis.label.set_fontsize(11)
        axes.yaxis.label.set_fontsize(11)
        axes.xaxis.labelpad = 8
        axes.yaxis.labelpad = 8
        axes.tick_params(axis="both", labelsize=10, width=1.1, length=4, pad=5)
        for spine in axes.spines.values():
            spine.set_linewidth(1.1)
        axes.grid(True, alpha=0.25, linewidth=0.8)

    @staticmethod
    def _add_empty_message(axes) -> None:
        axes.text(
            0.5, 0.5, "Results will appear here", transform=axes.transAxes,
            ha="center", va="center", color=MUTED,
        )
        axes.grid(True, alpha=0.2, linewidth=0.8)
