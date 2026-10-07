"""Controller for the main wizard navigation in the Qt window."""

from __future__ import annotations

from typing import Any

from PyQt5 import QtCore, QtGui

from sim_spr_lmr.application import SimulationValidationError

# Spectral limits vary by simulator and constrain WIM scan configuration.
DEFAULT_WIM_SPECTRAL_MAX_NM = 2000.0
LMR_SPR_WIM_SPECTRAL_MAX_NM = 4000.0

COUPLING_BUTTON_ENABLED_STYLE = (
    "QPushButton{ background-color: rgb(255, 255, 255);\n"
    "border-color: rgb(31, 78, 121);\n"
    "border-radius: 30px;\n"
    "border-style: outset;\n"
    "border-width: 7px;\n"
    "}\n"
    "QPushButton:hover{ border-color: rgb(255, 170, 0);}\n"
    "\n"
    "QPushButton:checked{ border-color: rgb(0, 170, 0);}"
)

COUPLING_BUTTON_DISABLED_STYLE = (
    "QPushButton{ background-color: rgb(255, 255, 255);\n"
    "border-color: #606060;\n"
    "border-radius: 30px;\n"
    "border-style: outset;\n"
    "border-width: 7px;\n"
    "}\n"
    "QPushButton:hover{ border-color: rgb(255, 170, 0);}\n"
    "\n"
    "QPushButton:checked{ border-color: rgb(0, 170, 0);}"
)


# Coordinates wizard choices, button states, and page transitions.
class NavigationController:
    """Coordinate wizard choices and page transitions."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def __getattr__(self, name: str) -> Any:
        return getattr(self.window, name)

    def _reset_layer_stack(self) -> None:
        """Discard a stack that belongs to a previous wizard configuration."""
        layer_stack_controller = getattr(self.window, "layer_stack_controller", None)
        if layer_stack_controller is not None:
            layer_stack_controller.reset_layer_stack()

    def _reset_layer_stack_if_changed(self, previous: object, selected: object) -> None:
        if previous not in (None, "", 0) and previous != selected:
            self._reset_layer_stack()

    def _reset_simulation_session(self) -> None:
        self._reset_layer_stack()
        self.session_state.reset()
        self.window.current_simulation_config = None
        self.window.current_simulation_result = None

    def _prepare_new_simulation(self) -> None:
        self._reset_simulation_session()
        self.label_title.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center"><span style=" font-size:11pt;">Simulator</span></p></body></html>',
                None,
            )
        )
        self.label_footer.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center"> </p></body></html>',
                None,
            )
        )
        self.configure_coupling_options(allow_prism=True, allow_fiber=True)
        self.aim_btn.setEnabled(True)
        self.wim_btn.setEnabled(True)

    def start_new_simulation(self) -> None:
        """Start a clean wizard directly at the simulator selection page."""
        self._prepare_new_simulation()
        self.Stacked_windows.setCurrentWidget(self.Select_simulator)

    def go_to_home(self) -> None:
        self._prepare_new_simulation()
        self.Stacked_windows.setCurrentWidget(self.home_window)

    def open_downstream_intermediate_step(self) -> None:
        """Open the step represented before layers in the active workflow."""
        target = (
            self.select_fiber_window
            if self.session_state.coupling_mode == 2
            else self.interrogation_window
        )
        self.Stacked_windows.setCurrentWidget(target)

    def open_selected_fiber_characteristics(self) -> None:
        """Return to the characteristics page of the selected fiber type."""
        target = (
            self.d_shaped_characteristics
            if self.session_state.fiber_type_code == 2
            else self.characteristics_fiber
        )
        self.Stacked_windows.setCurrentWidget(target)

    def update_downstream_breadcrumbs(self) -> None:
        """Keep shared layer/range breadcrumbs consistent with the selected route."""
        is_fiber = self.session_state.coupling_mode == 2
        fiber_name = (
            "D-shaped fiber"
            if self.session_state.fiber_type_code == 2
            else "Multimode fiber"
        )

        for coupling_button in (self.btn_coupling_3, self.btn_coupling_4):
            coupling_button.setText("Optical Coupling")

        for intermediate_button in (self.btn_interrogation_2, self.btn_interrogation_3):
            intermediate_button.setText(
                "Fiber configuration" if is_fiber else "Interrogation Mode"
            )

        for fiber_button, separator in (
            (self.btn_fiber_characteristics_layers, self.label_fiber_characteristics_layers),
            (self.btn_fiber_characteristics_range, self.label_fiber_characteristics_range),
        ):
            fiber_button.setText(fiber_name)
            fiber_button.setVisible(is_fiber)
            separator.setVisible(is_fiber)

        if is_fiber:
            self.btn_setting_layers.setText("Layer configuration")
            self.btn_setting_layers_2.setText("Layer configuration")
            self.btn_config_range.setText("WIM configuration")
        else:
            self.btn_setting_layers.setText("Setting Layers")
            self.btn_setting_layers_2.setText("Setting Layers")
            mode = "AIM" if self.session_state.interrogation_mode == 1 else "WIM"
            self.btn_config_range.setText(f"Configure {mode} mode")

    def set_coupling_button_state(self, button: Any, *, enabled: bool) -> None:
        button.setChecked(False)
        button.setEnabled(enabled)
        button.setStyleSheet(
            COUPLING_BUTTON_ENABLED_STYLE if enabled else COUPLING_BUTTON_DISABLED_STYLE
        )

# Updates the available coupling choices and their visual state.
    def configure_coupling_options(
        self,
        *,
        allow_prism: bool,
        allow_fiber: bool,
        show_d_shaped_fiber: bool = False,
    ) -> None:
        self.session_state.reset_navigation_choices()
        self.set_coupling_button_state(self.prism_btn, enabled=allow_prism)
        self.set_coupling_button_state(self.fiber_btn, enabled=allow_fiber)
        self.d_shaped_fiber_btn.setVisible(show_d_shaped_fiber)
        d_shaped_option = getattr(self.window, "d_shaped_fiber_option", None)
        if d_shaped_option is not None:
            d_shaped_option.setVisible(show_d_shaped_fiber)
        self.set_coupling_button_state(
            self.d_shaped_fiber_btn,
            enabled=allow_fiber and show_d_shaped_fiber,
        )
        self.warning_2.setText("")

    def configure_wim_controls_for_simulator(self) -> None:
        is_lmr_spr = self.session_state.is_lmr_spr
        is_fiber = self.session_state.coupling_mode == 2
        spectral_max = (
            LMR_SPR_WIM_SPECTRAL_MAX_NM
            if is_lmr_spr
            else DEFAULT_WIM_SPECTRAL_MAX_NM
        )

        current_start = float(self.a1_2.value())
        current_stop = float(self.a2_2.value())

        if current_start < 0.0:
            current_start = 0.0
        elif current_start > spectral_max:
            current_start = spectral_max

        if current_stop < 0.0:
            current_stop = 0.0
        elif current_stop > spectral_max:
            current_stop = spectral_max

        if is_lmr_spr and (current_start, current_stop) == (400.0, 1000.0):
            current_start = 500.0
            current_stop = 2500.0

        if current_stop < current_start:
            current_stop = current_start

        self.a1_2.setRange(0.0, spectral_max)
        self.a2_2.setRange(0.0, spectral_max)
        self.wavelength_range.setRange(0.0, spectral_max)
        self.wavelength_range.setValue((current_start, current_stop))
        self.a1_2.setValue(current_start)
        self.a2_2.setValue(current_stop)

        self.wavelength_incident_2.setVisible(not is_fiber)
        self.wavelength_incident_2.setEnabled(not is_fiber)
        self.configure_wim_result_illustration(is_fiber=is_fiber)

    def configure_wim_result_illustration(self, *, is_fiber: bool) -> None:
        if is_fiber:
            fiber_icon = (
                ":/icons/icons/D-shaped fiber.png"
                if self.session_state.fiber_type_code == 2
                else ":/icons/icons/fiber.png"
            )
            self.pushButton_10.setIcon(QtGui.QIcon(fiber_icon))
            return
        self.pushButton_10.setIcon(QtGui.QIcon(":/icons/icons/wim.png"))

    def spr_selected(self) -> None:
        self._reset_layer_stack()
        self.Stacked_windows.setCurrentWidget(self.coupling_window)
        self.session_state.simulator = "SPR"
        self.configure_coupling_options(allow_prism=True, allow_fiber=True)
        self.configure_wim_controls_for_simulator()
        self.aim_btn.setEnabled(True)
        self.wim_btn.setEnabled(True)
        self.label_title.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center"><span style=" font-size:11pt;">Sim-SPR</span></p></body></html>',
                None,
            )
        )
        self.label_footer.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center">Sim-SPR v02.0_a</p></body></html>',
                None,
            )
        )

    def lmr_selected(self) -> None:
        self._reset_layer_stack()
        self.Stacked_windows.setCurrentWidget(self.coupling_window)
        self.session_state.simulator = "LMR"
        self.configure_coupling_options(allow_prism=True, allow_fiber=True)
        self.configure_wim_controls_for_simulator()
        self.aim_btn.setEnabled(True)
        self.wim_btn.setEnabled(True)
        self.label_title.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center"><span style=" font-size:11pt;">Sim-LMR</span></p></body></html>',
                None,
            )
        )
        self.label_footer.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center">Sim-LMR v02.0_a</p></body></html>',
                None,
            )
        )

    def lmr_spr_selected(self) -> None:
        self._reset_layer_stack()
        self.Stacked_windows.setCurrentWidget(self.coupling_window)
        self.session_state.simulator = "LMR+SPR"
        self.configure_coupling_options(
            allow_prism=True,
            allow_fiber=True,
            show_d_shaped_fiber=True,
        )
        self.configure_wim_controls_for_simulator()
        self.aim_btn.setEnabled(False)
        self.aim_btn.setChecked(False)
        self.wim_btn.setEnabled(True)
        self.wim_btn.setChecked(False)
        self.TE_polarization.setEnabled(True)
        self.TM_polarization.setEnabled(True)
        self.TE_TM_polarization.setEnabled(True)
        self.TM_polarization.setChecked(True)
        self.label_title.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center"><span style=" font-size:11pt;">Sim-SPR+LMR</span></p></body></html>',
                None,
            )
        )
        self.label_footer.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p align="center">Sim-SPR+LMR v02.0_a</p></body></html>',
                None,
            )
        )
        self.warning_2.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#d49c10;\">- Sim-SPR+LMR supports Prism or Optical Fiber coupling - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#d49c10;\">- This implementation runs in WIM with TE, TM, or unpolarized (TE + TM) light - </span></pre></body></html>",
            )
        )

    def prism_btn_clicked(self) -> None:
        self._reset_layer_stack_if_changed(self.session_state.coupling_mode, 1)
        self.warning_2.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">- Coupling through Prism selected - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">Next to continue...</span></pre></body></html>"))
        self.session_state.coupling_mode = 1

    def fiber_btn_clicked(self) -> None:
        self._reset_layer_stack_if_changed(self.session_state.coupling_mode, 2)
        self.warning_2.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#37eb00;\">- Coupling through Optical Fiber selected - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">Next to continue...</span></pre></body></html>"))
        self.session_state.coupling_mode = 2
        self.session_state.fiber_type_code = 0
        self.cladding_remove_btn.setChecked(False)
        self.d_shaped_fiber_btn.setChecked(False)
        self.warning_fiber_typ.setText("")

    def d_shaped_fiber_btn_clicked(self) -> None:
        self.warning_fiber_typ.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                "<html><head/><body><pre align=\"center\"><span style=\"font-weight:500; "
                "font-family:'monospace'; color:#37eb00;\">- D-shaped fiber with residual "
                "cladding selected - </span></pre><pre align=\"center\"><span style=\"font-weight:500; "
                "font-family:'monospace'; color:#37eb00;\">Next to continue..."
                "</span></pre></body></html>",
            )
        )
        self.session_state.fiber_type_code = 2

    def fiber_cr_clicked(self) -> None:
        self.warning_fiber_typ.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#37eb00;\">- Cladding-removed multimode fiber selected - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">Next to continue...</span></pre></body></html>"))
        self.session_state.fiber_type_code = 1

# Routes the Next action according to the page currently shown in the wizard.
    def next_page(self, op: int, warning: Any) -> None:
        match self.Stacked_windows.currentWidget():
            case self.coupling_window:
                self._next_from_coupling(op, warning)
            case self.interrogation_window:
                self._next_from_interrogation(op, warning)
            case self.layers_window:
                self._next_from_layers(warning)
            case self.select_fiber_window:
                self._next_from_select_fiber(op, warning)
            case self.characteristics_fiber:
                self._next_from_fiber_characteristics(warning)
            case self.d_shaped_characteristics:
                self._next_from_fiber_characteristics(warning)

    def previous_page(self) -> None:
        match self.Stacked_windows.currentWidget():
            case self.Select_simulator:
                self.Stacked_windows.setCurrentWidget(self.home_window)
            case self.coupling_window:
                self.Stacked_windows.setCurrentWidget(self.Select_simulator)
            case self.interrogation_window:
                self.Stacked_windows.setCurrentWidget(self.coupling_window)
            case self.layers_window:
                if self.session_state.coupling_mode == 1:
                    self.Stacked_windows.setCurrentWidget(self.interrogation_window)
                elif self.session_state.fiber_type_code == 2:
                    self.Stacked_windows.setCurrentWidget(self.d_shaped_characteristics)
                else:
                    self.Stacked_windows.setCurrentWidget(self.characteristics_fiber)
            case self.select_fiber_window:
                self.Stacked_windows.setCurrentWidget(self.coupling_window)
            case self.interval_setting:
                self.Stacked_windows.setCurrentWidget(self.layers_window)
            case self.characteristics_fiber:
                self.Stacked_windows.setCurrentWidget(self.select_fiber_window)
            case self.d_shaped_characteristics:
                self.Stacked_windows.setCurrentWidget(self.select_fiber_window)

    def aim_btn_clicked(self) -> None:
        self._reset_layer_stack_if_changed(self.session_state.interrogation_mode, 1)
        self.warning_inter.setText(QtCore.QCoreApplication.translate(
            "Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#37eb00;\">- Angular interrogation mode selected - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">Next to continue...</span></pre></body></html>"))
        self.session_state.interrogation_mode = 1

    def wim_btn_clicked(self) -> None:
        self._reset_layer_stack_if_changed(self.session_state.interrogation_mode, 2)
        self.warning_inter.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#37eb00;\">- Wavelength interrogation mode selected - </span></pre><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#37eb00;\">Next to continue...</span></pre></body></html>"))
        self.session_state.interrogation_mode = 2

    def _next_from_coupling(self, op: int, warning: Any) -> None:
        if op == 0:
            warning.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#B21222;\">- *! Select a valid option !* - </span></pre></body></html>"))
        elif op == 1:
            self.Stacked_windows.setCurrentWidget(self.interrogation_window)
        elif op == 2:
            self.session_state.fiber_type_code = 0
            self.cladding_remove_btn.setChecked(False)
            self.d_shaped_fiber_btn.setChecked(False)
            self.warning_fiber_typ.setText("")
            self.Stacked_windows.setCurrentWidget(self.select_fiber_window)
        else:
            warning.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#B21222;\">- *! Select a valid option !* - </span></pre></body></html>"))

    def _next_from_interrogation(self, op: int, warning: Any) -> None:
        self.warning.setHidden(True)
        self.figure_.clear()
        self.canvas_.draw()
        if op == 0:
            warning.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#B21222;\">- *! Select a valid option !* - </span></pre></body></html>"))
        elif op == 1:
            self._open_aim_layer_page(warning)
        else:
            self._open_wim_layer_page()

    def _open_aim_layer_page(self, warning: Any) -> None:
        if self.session_state.coupling_mode == 2:
            warning.setText(QtCore.QCoreApplication.translate(
                "Widget",
                "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#B21222;\">- Optical-fiber coupling supports only WIM - </span></pre></body></html>",
            ))
            return
        if self.session_state.is_lmr_spr:
            self.textBrowser_2.setText("You have selected PRISM coupling and WAVELENGTH INTERROGATION MODE."
                            "\n\nTo continue your simulation:"
                            "\n\t* Add the prism as the first layer;"
                            "\n\t* Add one or more resonant coatings;"
                            "\n\t* Add the analyte as the final semi-infinite medium."
                            "\n\nPrism results are reported as reflectance in dB.")
            self.textBrowser.setText("Select the spectral range and incidence angle;"
                                    "\nClick 'Run' to calculate the prism reflectance spectrum in dB.")
            return
        self.Stacked_windows.setCurrentWidget(self.layers_window)
        self.stacked_layers.setCurrentWidget(self.page_layers_aim)
        self.Stacked_config_mode.setCurrentWidget(self.page_AIM_config)
        self.btn_config_range.setText("Configure AIM mode")
        self.update_downstream_breadcrumbs()
        self.textBrowser_2.setText("You have already selected PRISM coupling and ANGULAR INTERROGATION MODE."
                        "\n\nTo continue your simulation:\n"
                        "\n\t* Enter the operating wavelength in your simulation, in the 'Incident wavelength' field;"
                        "\n\t* Add at least 3 layers to build your sensor structure;"
                        "\n\t* In the 'Layers' field, add optical substrate layers, thin films and adhesion layers;"
                        "\n\t* Don't forget to add the analyte analysis range, in the 'Analyte refractive " "index range' field."
                        "\n\nIn the table below you can see the added layers.")
        self.textBrowser.setText("Select the analysis angular range in the 'Angular range' field;"
                                "\nClick the 'Run' button to start the calculations;"
                                "\nYou can choose which chart to view in the combobox below the chart area;")

    def _open_wim_layer_page(self) -> None:
        self.configure_wim_controls_for_simulator()
        self.Stacked_windows.setCurrentWidget(self.layers_window)
        self.stacked_layers.setCurrentWidget(self.page_layers_wim)
        self.Stacked_config_mode.setCurrentWidget(self.page_WIM_config)
        self.btn_config_range.setText("Configure WIM mode")
        self.update_downstream_breadcrumbs()
        if self.session_state.coupling_mode == 2:
            self.textBrowser_2.setText("You have selected OPTICAL FIBER coupling and WAVELENGTH INTERROGATION MODE."
                            "\n\nTo continue your simulation:\n"
                            "\n\t* Configure the fiber parameters using the fiber screen;"
                            "\n\t* Add the coating stack over the exposed core;"
                                    "\n\t* Add at least one coating before the analyte;"
                            "\n\t* Add the analyte refractive-index range."
                            "\n\nIn the table below you can see the added layers.")
            self.textBrowser.setText("Select the wavelength range in the 'Spectral range' field;"
                                    "\nClick the 'Run' button to calculate the normalized transmission spectrum;"
                                    "\nThe response is the normalized multimode-fiber transmission.")
            return
        self.textBrowser_2.setText("You have already selected PRISM coupling and WAVELENGTH INTERROGATION MODE."
                        "\n\nTo continue your simulation:\n"
                        "\n\t* Add at least 3 layers to build your sensor structure;"
                        "\n\t* In the 'Layers' field, add optical substrate layers, thin films and adhesion layers;"
                        "\n\t* Don't forget to add the analyte analysis range, in the 'Analyte refractive " "index range' field."
                        "\n\nIn the table below you can see the added layers.")
        self.textBrowser.setText("Select the wavelength range of the analysis in the 'Spectral range' field   and add the incidence angle in the 'Incidence angle' field;"
                                "\nClick the 'Run' button to start the calculations;"
                                "\nYou can choose which chart to view in the combobox below the chart area.")

    def _next_from_layers(self, warning: Any) -> None:
        minimum_layers = (
            2
            if self.session_state.coupling_mode == 2
            else 3
        )
        if self.nLayers < minimum_layers:
            self.warning.setHidden(False)
            self.warning.setText(QtCore.QCoreApplication.translate("Widget", f"<html><head/><body><p align=\"center\"><a name=\"tw-target-text\"/><span style=\" font-size:14pt; font-weight:400; color:#d41010;\"># Insert at least {minimum_layers} layers #</span><p align=\"center\"><span style=\" font-size:14pt; font-weight:400; color:#d41010;\"># {self.nLayers} layer(s) added # </span></body></html>", None))
            return

        try:
            self.validate_simulation_for_stage(
                self.collect_simulation_parameter_input(),
                stage="layers",
            )
        except SimulationValidationError as error:
            warning.setText(
                QtCore.QCoreApplication.translate(
                    "Widget",
                    f"<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#B21222;\">- {error.messages[0]} - </span></pre></body></html>",
                    None,
                )
            )
            self.show_simulation_validation_error(error)
            return
        self.update_downstream_breadcrumbs()
        self.Stacked_windows.setCurrentWidget(self.interval_setting)

    def _next_from_select_fiber(self, op: int, warning: Any) -> None:
        if op == 0:
            warning.setText(QtCore.QCoreApplication.translate("Widget", "<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a name=\"tw-target-text-container\"/><span style=\" font-weight:500; font-family:\'monospace\'; color:#B21222;\">- *! Select a valid option !* - </span></pre></body></html>"))
            return
        if op == 2:
            self.Stacked_windows.setCurrentWidget(self.d_shaped_characteristics)
        else:
            self.Stacked_windows.setCurrentWidget(self.characteristics_fiber)

    def _next_from_fiber_characteristics(self, warning: Any) -> None:
        try:
            self.validate_simulation_for_stage(
                self.collect_simulation_parameter_input(),
                stage="fiber",
            )
        except SimulationValidationError as error:
            warning.setText(
                QtCore.QCoreApplication.translate(
                    "Widget",
                    f"<html><head/><body><pre align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-weight:500; font-family:'monospace'; color:#B21222;\">- {error.messages[0]} - </span></pre></body></html>",
                    None,
                )
            )
            self.show_simulation_validation_error(error)
            return
        if self.session_state.coupling_mode == 2:
            coating_location = (
                "over the automatically modeled residual cladding"
                if self.session_state.fiber_type_code == 2
                else "over the exposed core"
            )
            self.session_state.interrogation_mode = 2
            self.configure_wim_controls_for_simulator()
            self.stacked_layers.setCurrentWidget(self.page_layers_wim)
            self.Stacked_config_mode.setCurrentWidget(self.page_WIM_config)
            self.btn_config_range.setText("Configure WIM mode")
            self.textBrowser_2.setText("You have selected OPTICAL FIBER coupling and WAVELENGTH INTERROGATION MODE."
                            "\n\nTo continue your simulation:\n"
                            f"\n\t* Add the coating stack {coating_location};"
                            "\n\t* Add at least one coating before the analyte;"
                            "\n\t* Add the analyte analysis range."
                            "\n\nIn the table below you can see the added layers.")
            self.textBrowser.setText("Select the wavelength range of the analysis in the 'Spectral range' field;"
                                    "\nClick the 'Run' button to start the calculations;"
                                    "\nThe output is the normalized transmission spectrum of the fiber sensor.")
        self.update_downstream_breadcrumbs()
        self.Stacked_windows.setCurrentWidget(self.layers_window)
