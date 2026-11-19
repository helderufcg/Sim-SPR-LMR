"""Presenter for fiber form visual state."""

from __future__ import annotations

from typing import Any


# Styles indicate whether Sellmeier coefficients can be edited.
SELLMEIER_ENABLED_STYLE = (
    '/*{font: 14pt "Ubuntu";\n'
    "color: rgb(255, 255, 255);\n"
    "	background-color: rgba(255, 255, 255,20);\n"
    "}*/\n"
    "\n"
    "QGroupBox  {\n"
    "	background-color: rgba(255, 255, 255,70);\n"
    '	font: 14pt "Ubuntu";\n'
    "    border: 2px solid;\n"
    "    border-color: #FF17365D;\n"
    "    margin-top: 25px;\n"
    "    border-bottom-left-radius: 20px;\n"
    "	border-bottom-right-radius: 20px;\n"
    "}\n"
    "\n"
    "QGroupBox::title  {\n"
    "    subcontrol-origin: margin;\n"
    "    subcontrol-position: top center;\n"
    "    padding: 5px 8000px 5px 8000px;\n"
    "    background-color: #FF17365D;\n"
    "    color: rgb(255, 255, 255);\n"
    "}\n"
    "QLineEdit{\n"
    "padding: 1px 18px 1px 3px;\n"
    "color: rgb(10, 25, 90);\n"
    'font: 700 12pt "Ubuntu";\n'
    " border: 2px solid;\n"
    "border-color: #FF17365D;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:8px;\n"
    "}"
    "QToolTip { "
    "background-color: black; "
    "color: white; "
    "border: black solid 1px"
    "}"
)

SELLMEIER_DISABLED_STYLE = (
    '/*{font: 14pt "Ubuntu";\n'
    "color: rgb(255, 255, 255);\n"
    "	background-color: rgba(255, 255, 255,20);\n"
    "}*/\n"
    "\n"
    "QGroupBox  {\n"
    "	background-color: rgba(255, 255, 255,70);\n"
    '	font: 14pt "Ubuntu";\n'
    "    border: 2px solid;\n"
    "    border-color: #606060;\n"
    "    margin-top: 25px;\n"
    "    border-bottom-left-radius: 20px;\n"
    "	border-bottom-right-radius: 20px;\n"
    "}\n"
    "\n"
    "QGroupBox::title  {\n"
    "    subcontrol-origin: margin;\n"
    "    subcontrol-position: top center;\n"
    "    padding: 5px 8000px 5px 8000px;\n"
    "    background-color: #606060;\n"
    "    color: rgb(255, 255, 255);\n"
    "}\n"
    "\n"
    "QLineEdit{\n"
    "padding: 1px 18px 1px 3px;\n"
    "color: rgb(10, 25, 90);\n"
    'font: 700 12pt "Ubuntu";\n'
    " border: 2px solid;\n"
    "border-color: #606060;\n"
    "background-color: rgba(255, 255, 255,210);\n"
    "border-radius:8px;\n"
    "}\n"
    "\n"
    "QPushButton{\n"
    '	font: 400 11pt "Ubuntu";\n'
    "	color: rgb(255, 255,255);\n"
    "	background-color: #606060;\n"
    "	border-color: rgb(0, 100, 130);\n"
    "	border-width: 2px;\n"
    "	border-radius:8px;\n"
    "}\n"
    "\n"
    "QPushButton:hover{\n"
    "	background-color: rgb(00, 140, 70);\n"
    "	border-color: rgb(0, 120, 40);\n"
    "	width: 40;\n"
    "	height: 35;\n"
    "}"
    "QToolTip { "
    "background-color: black; "
    "color: white; "
    "border: black solid 1px"
    "}"
)

ADD_COEFFICIENT_ENABLED_STYLE = (
    "QPushButton{\n"
    '	font: 400 11pt "Ubuntu";\n'
    "	color: rgb(255, 255,255);\n"
    "	background-color: rgb(0, 130, 180);\n"
    "	border-color: rgb(0, 100, 130);\n"
    "	border-width: 2px;\n"
    "	border-radius:8px;\n"
    "}\n"
    "\n"
    "QPushButton:hover{\n"
    "	background-color: rgb(00, 140, 70);\n"
    "	border-color: rgb(0, 120, 40);\n"
    "	width: 40;\n"
    "	height: 35;\n"
    "}"
)


# Controls the visual state of fiber material and Sellmeier fields.
class FiberFormPresenter:
    """Own visual enable/disable state for custom Sellmeier coefficients."""

    def __init__(self, window: Any) -> None:
        self.window = window

    def enable_gb_coef_sellmeier(self) -> None:
        if self.window.custom_btn.isChecked():
            self.window.coef_sellmeier_gb.setToolTip("Fill in the coefficients")
            self.window.coef_sellmeier_gb.setStyleSheet(SELLMEIER_ENABLED_STYLE)
            self.window.coef_sellmeier_gb.setEnabled(True)
            self.window.btn_add_coef.setStyleSheet(ADD_COEFFICIENT_ENABLED_STYLE)
            return

        self.window.coef_sellmeier_gb.setToolTip("Click in 'Custom' radio button to enable")
        self.window.coef_sellmeier_gb.setStyleSheet(SELLMEIER_DISABLED_STYLE)
        self.window.coef_sellmeier_gb.setEnabled(False)
