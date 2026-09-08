"""Qt helpers for layer/analyte edition states and form population.

This module keeps widget styling and edit-mode transitions out of ``main.py``.
The goal is to make the window controller responsible for orchestration, while
this presenter owns the visual state rules of the form.
"""

from typing import Any, Sequence


# Shared styles are centralized here so visual tweaks do not need to touch
# multiple methods spread through the window class.
# Centralized Qt styles describe the visual state of editable controls.
BUTTON_ENABLED_STYLE = (
    'QPushButton{\n'
    '    font: 400 11pt "Ubuntu";\n'
    "    color: rgb(255, 255,255);\n"
    "    background-color: rgb(0, 130, 180);\n"
    "    border-color: rgb(0, 100, 130);\n"
    "    border-width: 2px;\n"
    "    border-radius:10px;\n"
    "}\n\n"
    "QPushButton:hover{\n"
    "    background-color: rgb(00, 140, 70);\n"
    "    border-color: rgb(0, 120, 40);\n"
    "    width: 40;\n"
    "    height: 35;\n"
    "}"
)

BUTTON_DISABLED_STYLE = (
    'QPushButton{\n'
    '    font: 400 11pt "Ubuntu";\n'
    "    color: rgb(255, 255,255);\n"
    "    background-color: #606060;\n"
    "    border-color: rgb(0, 100, 130);\n"
    "    border-width: 2px;\n"
    "    border-radius:10px;\n"
    "}\n\n"
    "QPushButton:hover{\n"
    "    background-color: rgb(00, 140, 70);\n"
    "    border-color: rgb(0, 120, 40);\n"
    "    width: 40;\n"
    "    height: 35;\n"
    "}"
)

# Centralized Qt styles also cover the newer layer controls.
NEW_BUTTON_ENABLED_STYLE = (
    'QPushButton{\n'
    '    font: 400 11pt "Ubuntu";\n'
    "    color: rgb(255, 255,255);\n"
    "    background-color: rgb(0, 70, 120);\n"
    "    border-radius:6px;\n"
    "}\n\n"
    "QPushButton:hover{\n"
    "    background: rgb(0, 0, 255);\n"
    "    width: 40;\n"
    "    height: 35;\n"
    "}"
)

TEXT_ENABLED_STYLE = (
    "color: rgb(10, 25, 90);\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #FF17365D;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;"
)

TEXT_DISABLED_STYLE = (
    "color: #606060;\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #606060;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;"
)

COMBO_ENABLED_STYLE = (
    "QComboBox::drop-down {\n"
    "    width: 25;\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "}\n\n"
    "QComboBox\n"
    "{\n"
    " padding: 1px 18px 1px 3px;\n"
    "color: rgb(10, 25, 90);\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #FF17365D;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;\n"
    "}\n"
    "QComboBox::down-arrow {\n"
    "    top: 1px;\n"
    "    image: url(:/icons/icons/arrow-down.png);\n"
    "    left: 1px;\n"
    "}"
)

COMBO_DISABLED_STYLE = (
    "QComboBox::drop-down {\n"
    "    width: 25;\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "}\n\n"
    "QComboBox\n"
    "{\n"
    " padding: 1px 18px 1px 3px;\n"
    "color: #606060;\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #606060;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;\n"
    "}\n"
    "QComboBox::down-arrow {\n"
    "    top: 1px;\n"
    "    image: url(:/icons/icons/arrow-down.png);\n"
    "    left: 1px;\n"
    "}"
)

SPIN_ENABLED_STYLE = (
    "\nQDoubleSpinBox\n"
    "{\n"
    "color: rgb(10, 25, 90);\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #FF17365D;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;\n"
    "}\n\n"
    "QDoubleSpinBox::up-button\n"
    "{\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "    image: url(:/icons/icons/arrow-up.png);\n"
    "    width: 25;\n"
    "}\n"
    "QDoubleSpinBox::down-button\n"
    "{\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "    image: url(:/icons/icons/arrow-down.png);\n"
    "    width: 25;\n"
    "}"
)

SPIN_DISABLED_STYLE = (
    "\nQDoubleSpinBox\n"
    "{\n"
    "color: #606060;\n"
    'font: 700 12pt "Ubuntu";\n'
    "border: 2px solid;\n"
    "border-color: #606060;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:10px;\n"
    "}\n\n"
    "QDoubleSpinBox::up-button\n"
    "{\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "    image: url(:/icons/icons/arrow-up.png);\n"
    "    width: 25;\n"
    "}\n"
    "QDoubleSpinBox::down-button\n"
    "{\n"
    "    border-left-width: 1px;\n"
    "    border-left-color: darkgray;\n"
    "    border-left-style: solid;\n"
    "    border-top-right-radius: 3px;\n"
    "    border-bottom-right-radius: 3px;\n"
    "    image: url(:/icons/icons/arrow-down.png);\n"
    "    width: 25;\n"
    "}"
)

EDIT_TOOLTIP = "Click in 'New layer' to enable"


def _set_button(button: Any, enabled: bool, tooltip: str | None = None, style: str | None = None) -> None:
    button.setEnabled(enabled)
    if tooltip is not None:
        button.setToolTip(tooltip)
    button.setStyleSheet(style or (BUTTON_ENABLED_STYLE if enabled else BUTTON_DISABLED_STYLE))


def _set_new_button(button: Any, enabled: bool) -> None:
    button.setEnabled(enabled)
    button.setStyleSheet(NEW_BUTTON_ENABLED_STYLE if enabled else BUTTON_DISABLED_STYLE)


def _set_text_widget(widget: Any, *, enabled: bool | None = None, active: bool) -> None:
    if enabled is not None:
        widget.setEnabled(enabled)
    widget.setStyleSheet(TEXT_ENABLED_STYLE if active else TEXT_DISABLED_STYLE)


def _set_combo_widget(widget: Any, enabled: bool) -> None:
    widget.setEnabled(enabled)
    widget.setStyleSheet(COMBO_ENABLED_STYLE if enabled else COMBO_DISABLED_STYLE)


def _set_spin_widget(widget: Any, active: bool) -> None:
    widget.setStyleSheet(SPIN_ENABLED_STYLE if active else SPIN_DISABLED_STYLE)


def _real_value(value: Any) -> float:
    return float(_complex_value(value).real)


def _imag_value(value: Any) -> float:
    return float(_complex_value(value).imag)


def _complex_value(value: Any) -> complex:
    if isinstance(value, dict):
        return complex(float(value.get("real", 0.0)), float(value.get("imag", 0.0)))
    return complex(value)


def _analyte_step(analyte_indices: Sequence[Any]) -> float:
    if len(analyte_indices) < 2:
        return 0.0
    return _real_value(analyte_indices[1]) - _real_value(analyte_indices[0])


# Enables the controls required to create or edit an optical layer.
def enable_layer_inputs(ui: Any) -> None:
    """Put both layer forms into an enabled "ready to create/edit" state."""

    ui.btn_add_layer.setText("Add Layer")
    _set_button(ui.btn_add_layer, True, "Add layer")
    _set_combo_widget(ui.cbox_material, True)
    _set_text_widget(ui.thickness, enabled=True, active=True)
    _set_text_widget(ui.real_part_index, active=True)
    _set_text_widget(ui.imaginary_part_index, active=True)
    _set_text_widget(ui.description, enabled=True, active=True)

    ui.btn_add_layer_2.setText("Add Layer")
    _set_button(ui.btn_add_layer_2, True, "Add layer")
    _set_combo_widget(ui.cbox_material_2, True)
    _set_text_widget(ui.thickness_2, enabled=True, active=True)
    _set_text_widget(ui.wim_real_part_index, enabled=False, active=False)
    _set_text_widget(ui.wim_imaginary_part_index, enabled=False, active=False)
    _set_text_widget(ui.description_2, enabled=True, active=True)
    ui.warning.setHidden(True)


# Enables the controls required to configure an analyte sweep.
def enable_analyte_inputs(ui: Any) -> None:
    """Enable analyte widgets for both AIM and WIM variants of the form."""

    ui.gb_analyte.setEnabled(True)
    ui.gb_analyte.setToolTip("Analyte refractive index range")
    _set_text_widget(ui.description_3, enabled=True, active=True)
    _set_text_widget(ui.thickness_4, enabled=True, active=True)

    _set_spin_widget(ui.Analyte_refractive_index, True)
    _set_spin_widget(ui.n_sample_analyte, True)
    _set_spin_widget(ui.step_analyte, True)
    ui.btn_add_analyte.setText("Add Layer")
    _set_button(ui.btn_add_analyte, True, "Add analyte")

    ui.gb_analyte_2.setEnabled(True)
    ui.gb_analyte_2.setToolTip("Analyte refractive index range")
    _set_text_widget(ui.description_4, enabled=True, active=True)
    _set_text_widget(ui.thickness_3, enabled=True, active=True)

    _set_spin_widget(ui.Analyte_refractive_index_wim, True)
    _set_spin_widget(ui.n_sample_analyte_wim, True)
    _set_spin_widget(ui.step_analyte_wim, True)
    ui.btn_add_analyte_2.setText("Add Layer")
    _set_button(ui.btn_add_analyte_2, True, "Add analyte")
    ui.warning.setHidden(True)


def disable_analyte_inputs(ui: Any) -> None:
    """Return analyte widgets to the idle/read-only visual state."""

    ui.gb_analyte.setEnabled(False)
    ui.gb_analyte.setToolTip(EDIT_TOOLTIP)
    _set_spin_widget(ui.Analyte_refractive_index, False)
    _set_spin_widget(ui.n_sample_analyte, False)
    _set_spin_widget(ui.step_analyte, False)
    ui.btn_add_analyte.setText("Add Layer")
    _set_button(ui.btn_add_analyte, False, EDIT_TOOLTIP)
    _set_text_widget(ui.description_3, enabled=False, active=False)
    _set_text_widget(ui.thickness_4, enabled=False, active=False)

    ui.gb_analyte_2.setEnabled(False)
    ui.gb_analyte_2.setToolTip(EDIT_TOOLTIP)
    _set_spin_widget(ui.Analyte_refractive_index_wim, False)
    _set_spin_widget(ui.n_sample_analyte_wim, False)
    _set_spin_widget(ui.step_analyte_wim, False)
    ui.btn_add_analyte_2.setText("Add Layer")
    _set_button(ui.btn_add_analyte_2, False, EDIT_TOOLTIP)
    _set_text_widget(ui.description_4, enabled=False, active=False)
    _set_text_widget(ui.thickness_3, enabled=False, active=False)

    _set_button(ui.btn_confirm_edit_2, False)
    _set_button(ui.btn_confirm_edit_4, False)


def disable_layer_inputs(ui: Any) -> None:
    """Return layer widgets to the idle/read-only visual state."""

    _set_combo_widget(ui.cbox_material, False)
    _set_text_widget(ui.thickness, enabled=False, active=False)
    _set_text_widget(ui.real_part_index, enabled=False, active=False)
    _set_text_widget(ui.imaginary_part_index, enabled=False, active=False)
    _set_text_widget(ui.description, enabled=False, active=False)
    ui.btn_add_layer.setText("Add Layer")
    _set_button(ui.btn_add_layer, False, EDIT_TOOLTIP)
    _set_button(ui.btn_confirm_edit, False)

    _set_combo_widget(ui.cbox_material_2, False)
    _set_text_widget(ui.thickness_2, enabled=False, active=False)
    _set_text_widget(ui.wim_real_part_index, enabled=False, active=False)
    _set_text_widget(ui.wim_imaginary_part_index, enabled=False, active=False)
    _set_text_widget(ui.description_2, enabled=False, active=False)
    ui.btn_add_layer_2.setText("Add Layer")
    _set_button(ui.btn_add_layer_2, False, EDIT_TOOLTIP)
    _set_button(ui.btn_confirm_edit_3, False)

    _set_new_button(ui.btn_new_layer, True)
    _set_new_button(ui.btn_new_layer_2, True)


# Copies stored analyte data into the corresponding edit widgets.
def populate_analyte_edit_form(
    ui: Any,
    *,
    layer_edit: dict[str, Any],
    analyte_indices: Sequence[Any],
    interrogation_mode: int,
) -> None:
    """Fill analyte form fields and switch the UI into analyte edit mode."""

    enable_analyte_inputs(ui)
    analyte_start = _real_value(analyte_indices[0]) if analyte_indices else 0.0
    analyte_count = len(analyte_indices)
    analyte_step = _analyte_step(analyte_indices)

    if interrogation_mode == 1:
        ui.Analyte_refractive_index.setValue(analyte_start)
        ui.n_sample_analyte.setValue(analyte_count)
        ui.step_analyte.setValue(analyte_step)
        ui.thickness_4.setText(layer_edit["thickness"])
        ui.description_3.setText(layer_edit["description"])
        _set_button(ui.btn_add_analyte, False, EDIT_TOOLTIP)
        ui.btn_confirm_edit_2.setText("Confirm edit")
        _set_button(ui.btn_confirm_edit_2, True, "Confirm edit")
        return

    ui.Analyte_refractive_index_wim.setValue(analyte_start)
    ui.n_sample_analyte_wim.setValue(analyte_count)
    ui.step_analyte_wim.setValue(analyte_step)
    ui.thickness_3.setText(layer_edit["thickness"])
    ui.description_4.setText(layer_edit["description"])
    _set_button(ui.btn_add_analyte_2, False, EDIT_TOOLTIP)
    ui.btn_confirm_edit_4.setText("Confirm edit")
    _set_button(ui.btn_confirm_edit_4, True, "Confirm edit")


# Copies stored layer data into the layer editor widgets.
def populate_layer_edit_form(
    ui: Any,
    *,
    layer_edit: dict[str, Any],
    interrogation_mode: int,
    refractive_index: Any | None = None,
) -> None:
    """Fill layer form fields and switch the UI into layer edit mode."""

    enable_layer_inputs(ui)

    if interrogation_mode == 1:
        ui.cbox_material.setCurrentText(layer_edit["material"])
        ui.thickness.setText(layer_edit["thickness"])
        ui.description.setText(layer_edit["description"])

        is_custom = layer_edit["material"] == "Custom"
        layer_refractive_index = _complex_value(
            refractive_index if refractive_index is not None else layer_edit["refractiveIndex"]
        )
        ui.real_part_index.setEnabled(is_custom)
        ui.imaginary_part_index.setEnabled(is_custom)
        ui.real_part_index.setText(f"{_real_value(layer_refractive_index)}")
        ui.imaginary_part_index.setText(f"{_imag_value(layer_refractive_index)}")

        _set_new_button(ui.btn_new_layer, False)
        _set_button(ui.btn_add_layer, False, EDIT_TOOLTIP)
        ui.btn_confirm_edit.setText("Confirm edit")
        _set_button(ui.btn_confirm_edit, True, "Confirm edit")
        return

    ui.cbox_material_2.setCurrentText(layer_edit["material"])
    ui.thickness_2.setText(layer_edit["thickness"])
    ui.description_2.setText(layer_edit["description"])
    if layer_edit["material"] == "Custom":
        layer_refractive_index = _complex_value(
            refractive_index if refractive_index is not None else layer_edit["refractiveIndex"]
        )
        ui.wim_real_part_index.setText(f"{_real_value(layer_refractive_index)}")
        ui.wim_imaginary_part_index.setText(f"{_imag_value(layer_refractive_index)}")
    _set_new_button(ui.btn_new_layer_2, False)
    _set_button(ui.btn_add_layer_2, False, EDIT_TOOLTIP)
    ui.btn_confirm_edit_3.setText("Confirm edit")
    _set_button(ui.btn_confirm_edit_3, True, "Confirm edit")


def restore_manual_layer_refractive_index(
    ui: Any,
    *,
    material_name: str,
    refractive_index: Any,
    interrogation_mode: int,
) -> None:
    if material_name != "Custom":
        return

    layer_refractive_index = _complex_value(refractive_index)
    if interrogation_mode != 1:
        ui.wim_real_part_index.setEnabled(True)
        ui.wim_imaginary_part_index.setEnabled(True)
        ui.wim_real_part_index.setText(f"{_real_value(layer_refractive_index)}")
        ui.wim_imaginary_part_index.setText(f"{_imag_value(layer_refractive_index)}")
        return

    ui.real_part_index.setEnabled(True)
    ui.imaginary_part_index.setEnabled(True)
    ui.real_part_index.setText(f"{_real_value(layer_refractive_index)}")
    ui.imaginary_part_index.setText(f"{_imag_value(layer_refractive_index)}")
