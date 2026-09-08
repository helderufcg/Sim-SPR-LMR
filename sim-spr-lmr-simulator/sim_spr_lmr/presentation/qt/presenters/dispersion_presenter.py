"""Presenter for per-layer dispersion widgets and refractive-index preview."""

from __future__ import annotations

from typing import Any

from numpy import imag, real
from PyQt5 import QtCore, QtWidgets

from sim_spr_lmr.core.materials import (
    DRUDE_DISPERSION_MODEL,
    DRUDE_LORENTZ_DISPERSION_MODEL,
    EXPERIMENTAL_DISPERSION_MODEL,
    FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL,
    calculate_configured_refractive_index,
    default_drude_parameters_for_material,
    material_supports_drude_override,
    material_supports_drude_lorentz,
    material_supports_filmetrics_experimental,
    material_uses_builtin_drude,
    material_uses_builtin_drude_lorentz,
    normalize_dispersion_model_name,
    resolve_material_id,
    supports_dispersion_model,
)


# Manages dynamic dispersion controls and refractive-index previews for each layer.
class DispersionPresenter:
    """Own dynamic dispersion controls added around the generated Qt UI."""

    def __init__(self, window: Any) -> None:
        self.window = window
        self._last_material_names: dict[str, str] = {}

# Creates dispersion widgets that are absent from the generated UI.
    def install_layer_dispersion_controls(self) -> None:
        (
            self.window.aim_dispersion_frame,
            self.window.aim_dispersion_model,
            self.window.aim_drude_lambda_p_label,
            self.window.aim_drude_lambda_p,
            self.window.aim_drude_lambda_c_label,
            self.window.aim_drude_lambda_c,
        ) = self.create_layer_dispersion_frame(
            parent=self.window.gb_layers,
            combo_style_source=self.window.cbox_material,
            text_style_source=self.window.thickness,
            object_prefix="aim",
        )
        self.window.gridLayout_2.addWidget(self.window.aim_dispersion_frame, 5, 0, 1, 3)

        (
            self.window.wim_dispersion_frame,
            self.window.wim_dispersion_model,
            self.window.wim_drude_lambda_p_label,
            self.window.wim_drude_lambda_p,
            self.window.wim_drude_lambda_c_label,
            self.window.wim_drude_lambda_c,
        ) = self.create_layer_dispersion_frame(
            parent=self.window.gb_layers_2,
            combo_style_source=self.window.cbox_material_2,
            text_style_source=self.window.thickness_2,
            object_prefix="wim",
        )
        self.window.gridLayout_6.addWidget(self.window.wim_dispersion_frame, 5, 0, 1, 3)

        (
            self.window.wim_refractive_index_frame,
            self.window.wim_real_part_index,
            self.window.wim_imaginary_part_index,
        ) = self.create_wim_refractive_index_frame()
        self.window.gridLayout_6.removeWidget(self.window.label_description_2)
        self.window.gridLayout_6.removeWidget(self.window.description_2)
        self.window.gridLayout_6.addWidget(
            self.window.wim_refractive_index_frame, 3, 0, 1, 3
        )
        self.window.gridLayout_6.addWidget(
            self.window.label_description_2, 4, 0, 1, 1
        )
        self.window.gridLayout_6.addWidget(self.window.description_2, 4, 1, 1, 2)

        self.sync_layer_dispersion_controls()

    def create_layer_dispersion_frame(
        self,
        *,
        parent: Any,
        combo_style_source: Any,
        text_style_source: Any,
        object_prefix: str,
    ):
        frame = QtWidgets.QFrame(parent)
        frame.setObjectName(f"{object_prefix}_dispersion_frame")
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)

        layout = QtWidgets.QGridLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)

        label = QtWidgets.QLabel(frame)
        label.setObjectName(f"{object_prefix}_dispersion_label")
        label.setStyleSheet('font: 14pt "Ubuntu";')
        label.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p><span style=" color:#ffffff;">Dispersion model:</span></p></body></html>',
                None,
            )
        )
        layout.addWidget(label, 0, 0, 1, 1)

        combo = QtWidgets.QComboBox(frame)
        combo.setObjectName(f"{object_prefix}_dispersion_model")
        combo.addItem("Experimental")
        combo.addItem("Drude")
        combo.setEditable(False)
        combo.setMinimumSize(QtCore.QSize(0, 30))
        combo.setMaximumSize(QtCore.QSize(260, 16777215))
        combo.setStyleSheet(combo_style_source.styleSheet())
        layout.addWidget(combo, 0, 1, 1, 2)

        label_lambda_p = QtWidgets.QLabel(frame)
        label_lambda_p.setObjectName(f"{object_prefix}_drude_lambda_p_label")
        label_lambda_p.setStyleSheet('font: 14pt "Ubuntu";')
        label_lambda_p.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p><span style=" color:#ffffff;">lambda_p (um):</span></p></body></html>',
                None,
            )
        )
        layout.addWidget(label_lambda_p, 1, 0, 1, 1)

        lambda_p = QtWidgets.QLineEdit(frame)
        lambda_p.setObjectName(f"{object_prefix}_drude_lambda_p")
        lambda_p.setMinimumSize(QtCore.QSize(0, 30))
        lambda_p.setMaximumSize(QtCore.QSize(180, 16777215))
        lambda_p.setAlignment(QtCore.Qt.AlignCenter)
        lambda_p.setStyleSheet(text_style_source.styleSheet())
        layout.addWidget(lambda_p, 1, 1, 1, 1)

        label_lambda_c = QtWidgets.QLabel(frame)
        label_lambda_c.setObjectName(f"{object_prefix}_drude_lambda_c_label")
        label_lambda_c.setStyleSheet('font: 14pt "Ubuntu";')
        label_lambda_c.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p><span style=" color:#ffffff;">lambda_c (um):</span></p></body></html>',
                None,
            )
        )
        layout.addWidget(label_lambda_c, 1, 2, 1, 1)

        lambda_c = QtWidgets.QLineEdit(frame)
        lambda_c.setObjectName(f"{object_prefix}_drude_lambda_c")
        lambda_c.setMinimumSize(QtCore.QSize(0, 30))
        lambda_c.setMaximumSize(QtCore.QSize(180, 16777215))
        lambda_c.setAlignment(QtCore.Qt.AlignCenter)
        lambda_c.setStyleSheet(text_style_source.styleSheet())
        layout.addWidget(lambda_c, 1, 3, 1, 1)

        frame.setVisible(False)
        return frame, combo, label_lambda_p, lambda_p, label_lambda_c, lambda_c

    def create_wim_refractive_index_frame(self):
        frame = QtWidgets.QFrame(self.window.gb_layers_2)
        frame.setObjectName("wim_refractive_index_frame")
        frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        frame.setFrameShadow(QtWidgets.QFrame.Raised)

        layout = QtWidgets.QGridLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        real_label = QtWidgets.QLabel(frame)
        real_label.setObjectName("wim_real_part_index_label")
        real_label.setStyleSheet('font: 14pt "Ubuntu";')
        real_label.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p><span style=" color:#ffffff;">'
                "Refractive index - Real part*:</span></p></body></html>",
                None,
            )
        )
        layout.addWidget(real_label, 0, 0, 1, 1)

        real_part = QtWidgets.QLineEdit(frame)
        real_part.setObjectName("wim_real_part_index")
        real_part.setMinimumSize(QtCore.QSize(0, 30))
        real_part.setMaximumSize(QtCore.QSize(180, 16777215))
        real_part.setPlaceholderText("Real")
        real_part.setAlignment(QtCore.Qt.AlignCenter)
        real_part.setStyleSheet(self.window.real_part_index.styleSheet())
        layout.addWidget(real_part, 0, 1, 1, 2)

        imaginary_label = QtWidgets.QLabel(frame)
        imaginary_label.setObjectName("wim_imaginary_part_index_label")
        imaginary_label.setStyleSheet('font: 14pt "Ubuntu";')
        imaginary_label.setText(
            QtCore.QCoreApplication.translate(
                "Widget",
                '<html><head/><body><p><span style=" color:#ffffff;">'
                "Refractive index - Imaginary part:</span></p></body></html>",
                None,
            )
        )
        layout.addWidget(imaginary_label, 1, 0, 1, 1)

        imaginary_part = QtWidgets.QLineEdit(frame)
        imaginary_part.setObjectName("wim_imaginary_part_index")
        imaginary_part.setMinimumSize(QtCore.QSize(0, 30))
        imaginary_part.setMaximumSize(QtCore.QSize(180, 16777215))
        imaginary_part.setPlaceholderText("Imaginary (optional)")
        imaginary_part.setAlignment(QtCore.Qt.AlignCenter)
        imaginary_part.setStyleSheet(self.window.imaginary_part_index.styleSheet())
        layout.addWidget(imaginary_part, 1, 1, 1, 2)

        frame.setVisible(False)
        return frame, real_part, imaginary_part

    def layer_dispersion_context(self, interrogation_mode: str | None = None) -> dict[str, Any]:
        mode = interrogation_mode or self.window.session_state.interrogation_mode_name
        if mode == "AIM":
            return {
                "mode": "AIM",
                "material_widget": self.window.cbox_material,
                "base_combo": self.window.cbox_material,
                "base_text": self.window.thickness,
                "frame": self.window.aim_dispersion_frame,
                "model": self.window.aim_dispersion_model,
                "label_lambda_p": self.window.aim_drude_lambda_p_label,
                "lambda_p": self.window.aim_drude_lambda_p,
                "label_lambda_c": self.window.aim_drude_lambda_c_label,
                "lambda_c": self.window.aim_drude_lambda_c,
            }
        return {
            "mode": "WIM",
            "material_widget": self.window.cbox_material_2,
            "base_combo": self.window.cbox_material_2,
            "base_text": self.window.thickness_2,
            "frame": self.window.wim_dispersion_frame,
            "model": self.window.wim_dispersion_model,
            "label_lambda_p": self.window.wim_drude_lambda_p_label,
            "lambda_p": self.window.wim_drude_lambda_p,
            "label_lambda_c": self.window.wim_drude_lambda_c_label,
            "lambda_c": self.window.wim_drude_lambda_c,
        }

# Enables only model-specific controls supported by the selected material.
    def sync_layer_dispersion_controls(self) -> None:
        for mode in ("AIM", "WIM"):
            context = self.layer_dispersion_context(mode)
            material_name = context["material_widget"].currentText()
            material_changed = self._last_material_names.get(mode) != material_name
            self._last_material_names[mode] = material_name
            supports_drude = material_supports_drude_override(material_name)
            supports_filmetrics = material_supports_filmetrics_experimental(material_name)
            uses_builtin_drude = material_uses_builtin_drude(material_name)
            uses_builtin_drude_lorentz = material_uses_builtin_drude_lorentz(material_name)
            supports_drude_lorentz = material_supports_drude_lorentz(material_name)
            default_label = (
                "Drude–Lorentz"
                if uses_builtin_drude_lorentz
                else "Drude"
                if uses_builtin_drude
                else "Experimental"
            )
            supported_labels = [default_label]
            if supports_filmetrics:
                supported_labels.append("Experimental (Filmetrics)")
            if supports_drude:
                supported_labels.append("Drude")
            if supports_drude_lorentz and not uses_builtin_drude_lorentz:
                supported_labels.append("Drude–Lorentz")

            current_label = context["model"].currentText()
            context["model"].blockSignals(True)
            context["model"].clear()
            context["model"].addItems(supported_labels)
            context["model"].setCurrentText(
                current_label if current_label in supported_labels else default_label
            )
            context["model"].blockSignals(False)
            context["frame"].setVisible(len(supported_labels) > 1)

            if mode == "WIM":
                is_custom = material_name == "Custom"
                is_enabled = context["material_widget"].isEnabled()
                self.window.wim_refractive_index_frame.setVisible(is_custom)
                self.window.wim_real_part_index.setEnabled(is_enabled and is_custom)
                self.window.wim_imaginary_part_index.setEnabled(is_enabled and is_custom)
                if is_custom and material_changed:
                    self.window.wim_real_part_index.setText("")
                    self.window.wim_imaginary_part_index.setText("0")

            if len(supported_labels) == 1:
                context["model"].setCurrentText(default_label)
                context["lambda_p"].setText("")
                context["lambda_c"].setText("")
                continue

            defaults = default_drude_parameters_for_material(material_name)
            if defaults is not None:
                default_lambda_p, default_lambda_c = defaults
                if material_changed or not context["lambda_p"].text().strip():
                    context["lambda_p"].setText(f"{default_lambda_p}")
                if material_changed or not context["lambda_c"].text().strip():
                    context["lambda_c"].setText(f"{default_lambda_c}")

            is_enabled = context["material_widget"].isEnabled()
            is_drude_override = (
                supports_drude
                and self.selected_layer_dispersion_model(mode) == DRUDE_DISPERSION_MODEL
            )

            context["model"].setEnabled(is_enabled)
            context["label_lambda_p"].setVisible(is_drude_override)
            context["lambda_p"].setEnabled(is_enabled and is_drude_override)
            context["lambda_p"].setVisible(is_drude_override)
            context["label_lambda_c"].setVisible(is_drude_override)
            context["lambda_c"].setEnabled(is_enabled and is_drude_override)
            context["lambda_c"].setVisible(is_drude_override)
            context["model"].setStyleSheet(context["base_combo"].styleSheet())
            context["lambda_p"].setStyleSheet(context["base_text"].styleSheet())
            context["lambda_c"].setStyleSheet(context["base_text"].styleSheet())

        self.refresh_aim_preview_if_needed()

    def selected_layer_dispersion_model(self, interrogation_mode: str | None = None) -> str:
        context = self.layer_dispersion_context(interrogation_mode)
        return normalize_dispersion_model_name(context["model"].currentText())

    def selected_layer_drude_parameters(self, interrogation_mode: str | None = None) -> tuple[str, str]:
        context = self.layer_dispersion_context(interrogation_mode)
        return context["lambda_p"].text().strip(), context["lambda_c"].text().strip()

    def populate_layer_dispersion_form(self, layer_edit: dict[str, object], interrogation_mode: int) -> None:
        mode = "AIM" if interrogation_mode == 1 else "WIM"
        context = self.layer_dispersion_context(mode)
        material_name = str(layer_edit.get("material", ""))
        supports_drude = material_supports_drude_override(material_name)
        supports_filmetrics = material_supports_filmetrics_experimental(material_name)
        uses_builtin_drude = material_uses_builtin_drude(material_name)
        uses_builtin_drude_lorentz = material_uses_builtin_drude_lorentz(material_name)
        supports_drude_lorentz = material_supports_drude_lorentz(material_name)

        if (
            not supports_drude
            and not supports_filmetrics
            and not uses_builtin_drude
            and not supports_drude_lorentz
        ):
            context["model"].setCurrentText("Experimental")
            context["lambda_p"].setText("")
            context["lambda_c"].setText("")
            self.sync_layer_dispersion_controls()
            return

        dispersion_model = normalize_dispersion_model_name(
            str(layer_edit.get("dispersionModel", EXPERIMENTAL_DISPERSION_MODEL))
        )
        if uses_builtin_drude and dispersion_model == EXPERIMENTAL_DISPERSION_MODEL:
            dispersion_model = DRUDE_DISPERSION_MODEL
        if uses_builtin_drude_lorentz and dispersion_model == EXPERIMENTAL_DISPERSION_MODEL:
            dispersion_model = DRUDE_LORENTZ_DISPERSION_MODEL
        model_labels = {
            DRUDE_DISPERSION_MODEL: "Drude",
            DRUDE_LORENTZ_DISPERSION_MODEL: "Drude–Lorentz",
            EXPERIMENTAL_DISPERSION_MODEL: "Experimental",
            FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL: "Experimental (Filmetrics)",
        }
        self.sync_layer_dispersion_controls()
        context["model"].setCurrentText(model_labels[dispersion_model])

        defaults = default_drude_parameters_for_material(material_name)
        default_lambda_p = f"{defaults[0]}" if defaults is not None else ""
        default_lambda_c = f"{defaults[1]}" if defaults is not None else ""
        context["lambda_p"].setText(str(layer_edit.get("drudeLambdaP", "")) or default_lambda_p)
        context["lambda_c"].setText(str(layer_edit.get("drudeLambdaC", "")) or default_lambda_c)
        self.sync_layer_dispersion_controls()

    def refresh_aim_preview_if_needed(self) -> None:
        if self.window.session_state.interrogation_mode != 1:
            return
        if not self.window.cbox_material.isEnabled():
            return
        self.set_refractive_index(
            self.window.cbox_material.currentIndex(),
            self.window.lambda_i.value() * 1e-9,
        )

# Calculates and displays the material index at the selected wavelength.
    def set_refractive_index(self, material: int, lambda_i: float) -> None:
        material_id = self.selected_layer_material_id()

        if not supports_dispersion_model(material_id):
            self.window.real_part_index.setEnabled(True)
            self.window.real_part_index.setText("")
            self.window.imaginary_part_index.setEnabled(True)
            self.window.imaginary_part_index.setText("")
            return

        dispersion_model = self.selected_layer_dispersion_model("AIM")
        drude_lambda_p_text, drude_lambda_c_text = self.selected_layer_drude_parameters("AIM")
        try:
            drude_lambda_p = None if drude_lambda_p_text == "" else float(drude_lambda_p_text)
            drude_lambda_c = None if drude_lambda_c_text == "" else float(drude_lambda_c_text)
            n = calculate_configured_refractive_index(
                material_id,
                lambda_i,
                material_name=self.window.cbox_material.currentText(),
                dispersion_model=dispersion_model,
                drude_lambda_p_um=drude_lambda_p,
                drude_lambda_c_um=drude_lambda_c,
            )
        except ValueError:
            self.window.real_part_index.setText("")
            self.window.imaginary_part_index.setText("")
            return
        self.window.real_part_index.setText(str(round(real(n), 5)))
        self.window.imaginary_part_index.setText(str(round(imag(n), 5)))

    def selected_layer_material_id(self) -> int:
        if self.window.session_state.interrogation_mode == 1:
            material_name = self.window.cbox_material.currentText()
        else:
            material_name = self.window.cbox_material_2.currentText()
        return resolve_material_id(material_name)

    def reset_layer_form_dispersion_defaults(self) -> None:
        for mode in ("AIM", "WIM"):
            context = self.layer_dispersion_context(mode)
            material_name = context["material_widget"].currentText()
            defaults = default_drude_parameters_for_material(material_name)
            context["model"].setCurrentText(
                "Drude–Lorentz"
                if material_uses_builtin_drude_lorentz(material_name)
                else "Drude"
                if material_uses_builtin_drude(material_name)
                else "Experimental"
            )
            if defaults is None:
                context["lambda_p"].setText("")
                context["lambda_c"].setText("")
            else:
                context["lambda_p"].setText(f"{defaults[0]}")
                context["lambda_c"].setText(f"{defaults[1]}")
        self.sync_layer_dispersion_controls()
