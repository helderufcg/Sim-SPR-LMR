"""Controller for collecting parameters, running simulations and plotting results."""

from __future__ import annotations

from typing import Any

from PyQt5 import QtCore, QtWidgets

from sim_spr_lmr.application import (
    SimulationParameterInput,
    SimulationValidationError,
    run_simulation_from_parameters,
    validate_simulation_parameter_input,
    validate_simulation_parameter_input_stage,
)
from sim_spr_lmr.core.optics.response_scale import (
    REFLECTANCE_SCALE_DB,
    REFLECTANCE_SCALE_LINEAR,
)
from sim_spr_lmr.presentation.plotting import build_simulation_summary, render_simulation_result


# Owns parameter collection, validation, execution, progress, and result display.
class SimulationRunController:
    """Own the main simulation execution workflow for the Qt window."""

    def __init__(self, window: Any) -> None:
        self.window = window
        self.install_reflectance_scale_control()

    def install_reflectance_scale_control(self) -> None:
        """Add the prism-only response scale selector beside the graph selector."""

        self.window.reflectance_scale_label = QtWidgets.QLabel(
            "Scale:",
            self.window.grafico1_4,
        )
        self.window.reflectance_scale_label.setObjectName("reflectance_scale_label")
        self.window.reflectance_scale_label.setStyleSheet(
            "color: rgb(10, 25, 90); font: 600 11pt 'Ubuntu'; background: transparent;"
        )

        self.window.reflectance_scale_selector = QtWidgets.QComboBox(
            self.window.grafico1_4
        )
        self.window.reflectance_scale_selector.setObjectName(
            "reflectance_scale_selector"
        )
        self.window.reflectance_scale_selector.addItem(
            "R linear (0–1)",
            REFLECTANCE_SCALE_LINEAR,
        )
        self.window.reflectance_scale_selector.addItem(
            "Reflectance (dB)",
            REFLECTANCE_SCALE_DB,
        )
        self.window.reflectance_scale_selector.setCurrentIndex(
            self.window.reflectance_scale_selector.findData(REFLECTANCE_SCALE_DB)
        )
        self.window.reflectance_scale_selector.setMinimumWidth(155)
        self.window.reflectance_scale_selector.setMaximumWidth(190)
        self.window.reflectance_scale_selector.setStyleSheet(
            self.window.select_graphs.styleSheet()
        )
        self.window.reflectance_scale_selector.setToolTip(
            "Changes only the displayed and exported reflectance scale. "
            "Resonance detection and FWHM remain on the original dB result."
        )

        selector_index = self.window.horizontalLayout_53.indexOf(
            self.window.select_graphs
        )
        self.window.horizontalLayout_53.insertWidget(
            selector_index + 1,
            self.window.reflectance_scale_label,
        )
        self.window.horizontalLayout_53.insertWidget(
            selector_index + 2,
            self.window.reflectance_scale_selector,
        )
        self.window.reflectance_scale_label.hide()
        self.window.reflectance_scale_selector.hide()

    def _is_lmr_spr_prism_result(self) -> bool:
        config = self.window.current_simulation_config
        result = self.window.current_simulation_result
        return bool(
            config is not None
            and result is not None
            and config.simulator == "LMR+SPR"
            and config.coupling == "Prism"
            and result.response_quantity == "reflectance_db"
        )

    def selected_reflectance_scale(self) -> str | None:
        """Return the active display/export scale for a prism result."""

        if not self._is_lmr_spr_prism_result():
            return None
        return str(self.window.reflectance_scale_selector.currentData())

    def sync_reflectance_scale_visibility(self) -> None:
        """Show the selector only for prism reflectance graphs in Sim-LMR+SPR."""

        response_graph = self.window.select_graphs.currentText() in {
            "Reflectance",
            "Reflectance vs. Analyte",
        }
        visible = self._is_lmr_spr_prism_result() and response_graph
        self.window.reflectance_scale_label.setVisible(visible)
        self.window.reflectance_scale_selector.setVisible(visible)

# Converts widget values into domain input for the application layer.
    def collect_simulation_parameter_input(self) -> SimulationParameterInput:
        if self.window.TE_TM_polarization.isChecked():
            polarization = "TE+TM"
        elif self.window.TM_polarization.isChecked():
            polarization = "TM"
        else:
            polarization = "TE"
        is_d_shaped = self.window.session_state.fiber_type_code == 2
        core_material_name = (
            self.window.d_shape_core_material.currentText()
            if is_d_shaped
            else self.window.cbox_core_material.currentText()
        )
        return SimulationParameterInput(
            simulator=self.window.session_state.simulator or "Unknown",
            coupling_mode=self.window.session_state.coupling_mode,
            interrogation_mode=self.window.session_state.interrogation_mode,
            polarization=polarization,
            layer_rows=[dict(layer_row) for layer_row in self.window.layers],
            material_ids=list(self.window.material_id),
            thicknesses_m=list(self.window.d),
            refractive_indices=list(self.window.indexRef),
            analyte_indices=list(self.window.index_ref_analyte),
            aim_incidence_wavelength_nm=self.window.lambda_i.value(),
            aim_scan_start_deg=self.window.a1_3.value(),
            aim_scan_stop_deg=self.window.a2_3.value(),
            wim_incidence_angle_deg=self.window.angle_incidence.value(),
            wim_scan_start_nm=self.window.a1_2.value(),
            wim_scan_stop_nm=self.window.a2_2.value(),
            fiber_type_code=self.window.session_state.fiber_type_code,
            fiber_length_mm=(
                self.window.d_shape_length.value() if is_d_shaped else self.window.L_fiber.value()
            ),
            fiber_core_diameter_um=(
                self.window.d_shape_core_diameter.value()
                if is_d_shaped
                else self.window.D_fiber.value()
            ),
            fiber_numerical_aperture=(
                self.window.d_shape_numerical_aperture.value()
                if is_d_shaped
                else self.window.N_A.value()
            ),
            fiber_outer_diameter_um=(
                self.window.d_shape_outer_diameter.value() if is_d_shaped else 0.0
            ),
            fiber_residual_cladding_um=(
                self.window.d_shape_residual_cladding.value() if is_d_shaped else 0.0
            ),
            fiber_core_material_id=self.core_material_id(core_material_name),
            fiber_core_material_name=core_material_name,
            fiber_use_custom_sellmeier=(
                False if is_d_shaped else self.window.custom_btn.isChecked()
            ),
            fiber_sellmeier_b1=(None if is_d_shaped else self.optional_float(self.window.a1.text())),
            fiber_sellmeier_b2=(None if is_d_shaped else self.optional_float(self.window.a2.text())),
            fiber_sellmeier_b3=(None if is_d_shaped else self.optional_float(self.window.a3.text())),
            fiber_sellmeier_c1=(None if is_d_shaped else self.optional_float(self.window.b1.text())),
            fiber_sellmeier_c2=(None if is_d_shaped else self.optional_float(self.window.b2.text())),
            fiber_sellmeier_c3=(None if is_d_shaped else self.optional_float(self.window.b3.text())),
        )

    def selected_core_material_id(self) -> int | None:
        return self.core_material_id(self.window.cbox_core_material.currentText())

    @staticmethod
    def core_material_id(material_name: str) -> int | None:
        if material_name.strip().lower() in {"silic", "silica"}:
            return 1
        return None

    def optional_float(self, text_value: str) -> float | None:
        normalized_text = text_value.strip()
        if normalized_text == "":
            return None
        return float(normalized_text)

    def reset_simulation_validation_state(self) -> None:
        self.window.warning.setHidden(True)
        self.window.warning_range.setHidden(True)
        self.window.warning_angular.setHidden(True)

    def validate_simulation_before_run(self, parameter_input: SimulationParameterInput):
        self.reset_simulation_validation_state()
        return validate_simulation_parameter_input(parameter_input)

    def validate_simulation_for_stage(
        self,
        parameter_input: SimulationParameterInput,
        stage: str,
    ) -> None:
        self.reset_simulation_validation_state()
        validate_simulation_parameter_input_stage(parameter_input, stage)

    def update_simulation_progress(self, progress_value: int) -> None:
        self.window.progress_value = progress_value
        QtWidgets.QApplication.processEvents()

    def log_simulation_message(self, message: str) -> None:
        self.window.textBrowser.append(message)

# Validates the current configuration and starts the simulation workflow.
    def start_simulation(self) -> None:
        parameter_input = self.collect_simulation_parameter_input()
        try:
            self.validate_simulation_before_run(parameter_input)
        except SimulationValidationError as error:
            self.window.show_simulation_validation_error(error)
            return

        self.window.progressBar.setHidden(False)
        self.window.timer = QtCore.QTimer(self.window)
        self.window.timer.timeout.connect(self.update_progress)
        self.window.timer_interval = 100

        self.window.progress_value = 0
        self.window.progressBar.setValue(0)
        self.window.timer.start(self.window.timer_interval)

        self.window.current_simulation_result = None
        self.window.textBrowser.setText("Calculating...")

        try:
            simulation_execution = run_simulation_from_parameters(
                parameter_input=parameter_input,
                progress_callback=self.update_simulation_progress,
                log_callback=self.log_simulation_message,
            )
        except SimulationValidationError as error:
            self.window.show_simulation_validation_error(error)
            self._stop_progress_at_zero()
            return
        except Exception as error:
            self.window.textBrowser.setText(f"Simulation error:\n{error}")
            self._stop_progress_at_zero()
            return

        self.window.current_simulation_config = simulation_execution.config
        self.window.current_simulation_result = simulation_execution.result
        selector = self.window.reflectance_scale_selector
        selector.blockSignals(True)
        selector.setCurrentIndex(selector.findData(REFLECTANCE_SCALE_DB))
        selector.blockSignals(False)
        self.show_graphs()
        self._enable_export_button()

        self.window.progress_value = 100
        self.window.progressBar.setValue(self.window.progress_value)
        QtWidgets.QApplication.processEvents()
        self.window.timer.stop()

    def update_progress(self) -> None:
        self.window.progressBar.setValue(self.window.progress_value)

    def sync_graph_selector_labels(self) -> None:
        if self.window.current_simulation_result is None:
            return

        if self.window.current_simulation_result.response_quantity == "transmission":
            self.window.select_graphs.setItemText(0, "Transmission")
            self.window.select_graphs.setItemText(1, "Transmission vs. Analyte")
        else:
            self.window.select_graphs.setItemText(0, "Reflectance")
            self.window.select_graphs.setItemText(1, "Reflectance vs. Analyte")

# Renders the selected result graph and updates the summary panel.
    def show_graphs(self, *_args: object) -> None:
        if self.window.current_simulation_result is None:
            return

        self.sync_graph_selector_labels()
        self.sync_reflectance_scale_visibility()
        reflectance_scale = self.selected_reflectance_scale()
        render_simulation_result(
            figure=self.window.figure_,
            graph_name=self.window.select_graphs.currentText(),
            simulation_result=self.window.current_simulation_result,
            reflectance_scale=reflectance_scale,
        )
        self.window.canvas_.draw()
        self.window.textBrowser.setText(
            build_simulation_summary(
                self.window.current_simulation_result,
                reflectance_scale=reflectance_scale,
            )
        )

    def _stop_progress_at_zero(self) -> None:
        self.window.progress_value = 0
        self.window.progressBar.setValue(self.window.progress_value)
        self.window.timer.stop()

    def _enable_export_button(self) -> None:
        self.window.btn_export_data.setEnabled(True)
        self.window.btn_export_data.setStyleSheet(
            "QPushButton{\n"
            '    font: 400 11pt "Ubuntu";\n'
            "    color: rgb(255, 255,255);\n"
            "    background-color: rgba(0, 130, 180,160);\n"
            "    border-color: rgba(0, 100, 130,160);\n"
            "    border-width: 2px;\n"
            "    border-radius:10px;\n"
            "}\n"
            "\n"
            "QPushButton:hover{\n"
            "    background-color: rgb(0, 130, 180);\n"
            "    width: 40;\n"
            "    height: 35;\n"
            "}"
        )
