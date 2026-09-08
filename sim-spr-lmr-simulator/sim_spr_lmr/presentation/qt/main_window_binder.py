"""Signal binding for the legacy generated Qt main window."""

from __future__ import annotations

from PyQt5 import QtCore, QtGui, QtWidgets


# Adds the fiber-characteristics step to the existing breadcrumb hierarchy.
def _install_fiber_breadcrumb_steps(window) -> None:
    """Add the fiber-characteristics step to shared downstream breadcrumbs."""

    def add_step(layout, parent, reference_button, object_name):
        button = QtWidgets.QPushButton(parent)
        button.setObjectName(object_name)
        button.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum,
            QtWidgets.QSizePolicy.Fixed,
        )
        button.setMinimumSize(QtCore.QSize(110, 20))
        button.setMaximumSize(QtCore.QSize(170, 20))
        button.setFont(reference_button.font())
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet(reference_button.styleSheet())

        separator = QtWidgets.QLabel(parent)
        separator.setObjectName(f"{object_name}_separator")
        separator.setMaximumSize(QtCore.QSize(10, 10))
        separator.setPixmap(
            QtGui.QPixmap(
                ":/icons/icons/simbolo-de-setas-duplas-para-a-direita-para-avancar.png"
            )
        )
        separator.setScaledContents(True)

        layout.insertWidget(6, button)
        layout.insertWidget(7, separator)
        button.setVisible(False)
        separator.setVisible(False)
        return button, separator

    (
        window.btn_fiber_characteristics_layers,
        window.label_fiber_characteristics_layers,
    ) = add_step(
        window.horizontalLayout_79,
        window.hierarchy_frame,
        window.btn_interrogation_2,
        "btn_fiber_characteristics_layers",
    )
    (
        window.btn_fiber_characteristics_range,
        window.label_fiber_characteristics_range,
    ) = add_step(
        window.horizontalLayout_56,
        window.frame_hierarq_8,
        window.btn_interrogation_3,
        "btn_fiber_characteristics_range",
    )


# Configures button groups so mutually exclusive choices behave like radio buttons.
def _install_exclusive_selection_groups(window) -> None:
    """Keep each family of selectable cards visually and logically exclusive."""
    groups = {
        "coupling_selection_group": (window.prism_btn, window.fiber_btn),
        "fiber_selection_group": (
            window.cladding_remove_btn,
            window.d_shaped_fiber_btn,
        ),
        "interrogation_selection_group": (window.aim_btn, window.wim_btn),
    }
    for attribute_name, buttons in groups.items():
        group = QtWidgets.QButtonGroup(window)
        group.setExclusive(True)
        for button in buttons:
            button.setCheckable(True)
            button.setAutoExclusive(False)
            group.addButton(button)
        setattr(window, attribute_name, group)


# Connects generated UI signals to controllers and presentation helpers.
def bind_main_window_events(window) -> None:
    """Connect Qt signals while keeping ``MainWindow.__init__`` focused on setup."""

    auxiliary = window.auxiliary_windows
    navigation = window.navigation_controller
    layer_stack = window.layer_stack_controller
    simulation = window.simulation_run_controller
    dispersion = window.dispersion_presenter
    fiber_form = window.fiber_form_presenter

    _install_exclusive_selection_groups(window)
    _install_fiber_breadcrumb_steps(window)
    navigation.update_downstream_breadcrumbs()

    window.btn_close.clicked.connect(window.close)
    window.btn_help.clicked.connect(auxiliary.open_help_center)
    window.btn_minimize.clicked.connect(window.showMinimized)
    window.exit_btn.clicked.connect(window.close)
    window.start_btn.clicked.connect(
        lambda: window.Stacked_windows.setCurrentWidget(window.Select_simulator)
    )

    window.open_btn_ext.clicked.connect(auxiliary.open_from_extern_file)
    window.btn_multip_analyse.setEnabled(False)
    window.btn_multip_analyse.setToolTip(
        "Parametric resonance analysis is currently unavailable in the main simulator."
    )

    for home_button in (
        window.btn_home,
        window.btn_home_2,
        window.btn_home_3,
        window.btn_home_4,
        window.btn_home_5,
        window.btn_home_6,
        window.btn_home_7,
    ):
        home_button.clicked.connect(navigation.go_to_home)
    window.btn_home_d_shape.clicked.connect(navigation.go_to_home)
    window.prev_btn_sel.clicked.connect(navigation.previous_page)

    for coupling_button in (
        window.btn_coupling,
        window.btn_coupling_2,
        window.btn_coupling_3,
        window.btn_coupling_4,
        window.btn_coupling_5,
        window.btn_coupling_6,
    ):
        coupling_button.clicked.connect(
            lambda _checked=False, w=window: w.Stacked_windows.setCurrentWidget(w.coupling_window)
        )
    window.btn_coupling_d_shape.clicked.connect(
        lambda _checked=False, w=window: w.Stacked_windows.setCurrentWidget(w.coupling_window)
    )
    window.btn_fiber_type_d_shape.clicked.connect(
        lambda _checked=False, w=window: w.Stacked_windows.setCurrentWidget(w.select_fiber_window)
    )
    window.btn_fiber_type_2.clicked.connect(
        lambda _checked=False, w=window: w.Stacked_windows.setCurrentWidget(w.select_fiber_window)
    )

    window.btn_interrogation.clicked.connect(
        lambda _checked=False, w=window: w.Stacked_windows.setCurrentWidget(w.interrogation_window)
    )
    for downstream_step in (window.btn_interrogation_2, window.btn_interrogation_3):
        downstream_step.clicked.connect(navigation.open_downstream_intermediate_step)
    for fiber_step in (
        window.btn_fiber_characteristics_layers,
        window.btn_fiber_characteristics_range,
    ):
        fiber_step.clicked.connect(navigation.open_selected_fiber_characteristics)

    window.btn_setting_layers.clicked.connect(
        lambda: window.Stacked_windows.setCurrentWidget(window.layers_window)
    )
    window.btn_setting_layers_2.clicked.connect(
        lambda: window.Stacked_windows.setCurrentWidget(window.layers_window)
    )
    window.spr_btn.clicked.connect(navigation.spr_selected)
    window.lmr_btn.clicked.connect(navigation.lmr_selected)
    if hasattr(window, "lmr_spr_btn"):
        window.lmr_spr_btn.clicked.connect(navigation.lmr_spr_selected)

    window.prism_btn.clicked.connect(navigation.prism_btn_clicked)
    window.fiber_btn.clicked.connect(navigation.fiber_btn_clicked)
    window.d_shaped_fiber_btn.clicked.connect(navigation.d_shaped_fiber_btn_clicked)
    window.prev_btn_coup.clicked.connect(navigation.previous_page)
    window.next_btn_coup.clicked.connect(
        lambda: navigation.next_page(
            op=window.session_state.coupling_mode,
            warning=window.warning_2,
        )
    )

    window.cladding_remove_btn.clicked.connect(navigation.fiber_cr_clicked)
    window.prev_btn_fiber_typ.clicked.connect(navigation.previous_page)
    window.next_btn_fiber_typ.clicked.connect(
        lambda: navigation.next_page(
            op=window.session_state.fiber_type_code,
            warning=window.warning_fiber_typ,
        )
    )

    window.prev_btn_char_fib.clicked.connect(navigation.previous_page)
    window.next_btn_char_fib.clicked.connect(
        lambda: navigation.next_page(op=1, warning=window.label_4)
    )
    window.prev_btn_d_shape.clicked.connect(navigation.previous_page)
    window.next_btn_d_shape.clicked.connect(
        lambda: navigation.next_page(op=2, warning=window.d_shape_warning)
    )

    window.aim_btn.clicked.connect(navigation.aim_btn_clicked)
    window.wim_btn.clicked.connect(navigation.wim_btn_clicked)
    window.prev_btn_inter.clicked.connect(navigation.previous_page)
    window.next_btn_inter.clicked.connect(
        lambda: navigation.next_page(
            op=window.session_state.interrogation_mode,
            warning=window.warning_inter,
        )
    )

    window.prev_btn_config_layers.clicked.connect(navigation.previous_page)
    window.next_btn_config_layers.clicked.connect(
        lambda: navigation.next_page(
            op=window.session_state.interrogation_mode,
            warning=window.label_warning,
        )
    )

    window.lambda_i_slider.valueChanged.connect(
        lambda: window.change_spinbox(window.lambda_i, window.lambda_i_slider)
    )
    window.lambda_i.valueChanged.connect(
        lambda: window.change_slider(window.lambda_i, window.lambda_i_slider)
    )

    window.custom_btn.toggled.connect(fiber_form.enable_gb_coef_sellmeier)

    window.btn_new_layer.clicked.connect(window.set_Enable_True)
    window.btn_new_layer.clicked.connect(window.set_Enable_True_2)
    window.btn_new_layer.clicked.connect(
        lambda: dispersion.set_refractive_index(
            window.cbox_material.currentIndex(),
            window.lambda_i.value() * 1e-9,
        )
    )
    window.cbox_material.currentIndexChanged.connect(
        lambda: dispersion.set_refractive_index(
            window.cbox_material.currentIndex(),
            window.lambda_i.value() * 1e-9,
        )
    )
    window.cbox_material.currentTextChanged.connect(dispersion.sync_layer_dispersion_controls)
    window.lambda_i_slider.valueChanged.connect(
        lambda: dispersion.set_refractive_index(
            window.cbox_material.currentIndex(),
            window.lambda_i.value() * 1e-9,
        )
    )
    window.lambda_i.valueChanged.connect(
        lambda: dispersion.set_refractive_index(
            window.cbox_material.currentIndex(),
            window.lambda_i.value() * 1e-9,
        )
    )

    window.btn_new_layer_2.clicked.connect(window.set_Enable_True)
    window.btn_new_layer_2.clicked.connect(window.set_Enable_True_2)
    window.cbox_material_2.currentTextChanged.connect(dispersion.sync_layer_dispersion_controls)

    window.btn_add_layer.clicked.connect(
        lambda: _handle_layer_primary_action(
            window.btn_add_layer,
            layer_stack,
            window.set_Enable_False_2,
        )
    )
    window.btn_add_analyte.clicked.connect(
        lambda: _handle_analyte_primary_action(
            window.btn_add_analyte,
            layer_stack,
            window.set_Enable_False,
        )
    )
    window.btn_add_layer_2.clicked.connect(
        lambda: _handle_layer_primary_action(
            window.btn_add_layer_2,
            layer_stack,
            window.set_Enable_False_2,
        )
    )
    window.btn_add_analyte_2.clicked.connect(
        lambda: _handle_analyte_primary_action(
            window.btn_add_analyte_2,
            layer_stack,
            window.set_Enable_False,
        )
    )

    window.prev_btn_config_mode.clicked.connect(navigation.previous_page)
    window.btn_edit_layers_3.clicked.connect(
        lambda: window.Stacked_windows.setCurrentWidget(window.layers_window)
    )

    window.angle_Slider.valueChanged.connect(
        lambda: window.change_spinbox(window.angle_incidence, window.angle_Slider)
    )
    window.angle_incidence.valueChanged.connect(
        lambda: window.change_slider(window.angle_incidence, window.angle_Slider)
    )

    window.wavelength_range.valueChanged.connect(
        lambda: window.change_range_spin(window.a1_2, window.a2_2, window.wavelength_range)
    )
    window.a1_2.valueChanged.connect(
        lambda: window.change_range_slider2(
            window.a1_2,
            window.a2_2,
            window.wavelength_range,
            window.warning_range,
        )
    )
    window.a2_2.valueChanged.connect(
        lambda: window.change_range_slider(
            window.a1_2,
            window.a2_2,
            window.wavelength_range,
            window.warning_range,
        )
    )

    window.angular_range.valueChanged.connect(
        lambda: window.change_range_spin(window.a1_3, window.a2_3, window.angular_range)
    )
    window.a1_3.valueChanged.connect(
        lambda: window.change_range_slider2(
            window.a1_3,
            window.a2_3,
            window.angular_range,
            window.warning_angular,
        )
    )
    window.a2_3.valueChanged.connect(
        lambda: window.change_range_slider(
            window.a1_3,
            window.a2_3,
            window.angular_range,
            window.warning_angular,
        )
    )

    window.btn_run.clicked.connect(simulation.start_simulation)
    window.select_graphs.currentIndexChanged.connect(simulation.show_graphs)
    window.reflectance_scale_selector.currentIndexChanged.connect(simulation.show_graphs)
    window.TM_polarization.setChecked(True)

    window.btn_remove_layers.clicked.connect(layer_stack.remove_layers)
    window.btn_edit_layers.clicked.connect(layer_stack.select_edit_layer)
    window.aim_dispersion_model.currentTextChanged.connect(
        dispersion.sync_layer_dispersion_controls
    )
    window.wim_dispersion_model.currentTextChanged.connect(
        dispersion.sync_layer_dispersion_controls
    )
    window.aim_drude_lambda_p.textChanged.connect(dispersion.refresh_aim_preview_if_needed)
    window.aim_drude_lambda_c.textChanged.connect(dispersion.refresh_aim_preview_if_needed)

    if window.btn_confirm_edit is not window.btn_add_layer:
        window.btn_confirm_edit.clicked.connect(layer_stack.edit_layer)
        window.btn_confirm_edit.clicked.connect(window.set_Enable_False_2)

    if window.btn_confirm_edit_3 is not window.btn_add_layer_2:
        window.btn_confirm_edit_3.clicked.connect(layer_stack.edit_layer)
        window.btn_confirm_edit_3.clicked.connect(window.set_Enable_False_2)

    if window.btn_confirm_edit_2 is not window.btn_add_analyte:
        window.btn_confirm_edit_2.clicked.connect(layer_stack.edit_analyte)
        window.btn_confirm_edit_2.clicked.connect(window.set_Enable_False)

    if window.btn_confirm_edit_4 is not window.btn_add_analyte_2:
        window.btn_confirm_edit_4.clicked.connect(layer_stack.edit_analyte)
        window.btn_confirm_edit_4.clicked.connect(window.set_Enable_False)

    window.btn_save_table.clicked.connect(auxiliary.save_table)
    window.btn_save_preset.clicked.connect(layer_stack.save_layer_preset)
    window.btn_load_preset.clicked.connect(layer_stack.load_layer_preset)
    window.btn_delete_preset.clicked.connect(layer_stack.delete_layer_preset)
    window.btn_export_data.clicked.connect(auxiliary.export_data)
    window.btn_new_simulation.clicked.connect(navigation.start_new_simulation)


def _button_requests_edit(button) -> bool:
    return button.text().strip().lower().startswith("confirm")


def _handle_layer_primary_action(button, layer_stack, disable_callback) -> None:
    if _button_requests_edit(button):
        layer_stack.edit_layer()
    else:
        layer_stack.add_layers()
    disable_callback()


def _handle_analyte_primary_action(button, layer_stack, disable_callback) -> None:
    if _button_requests_edit(button):
        layer_stack.edit_analyte()
    else:
        layer_stack.add_analyte()
    disable_callback()
