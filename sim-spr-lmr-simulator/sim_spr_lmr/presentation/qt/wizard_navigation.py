"""Shared visual treatment for the wizard Previous/Next controls."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from PyQt5 import QtCore, QtGui, QtWidgets


# Shared visual constants keep navigation consistent across wizard pages.
WIZARD_NAVIGATION_STYLE = (
    "QPushButton { color: white; font: 600 11pt 'Ubuntu'; "
    "background-color: rgb(0, 130, 180); "
    "border: 2px solid rgb(0, 100, 130); "
    "border-radius: 8px; padding: 4px 12px; } "
    "QPushButton:hover { background-color: rgb(0, 140, 70); "
    "border-color: rgb(0, 105, 55); } "
    "QPushButton:pressed { background-color: rgb(0, 105, 145); } "
    "QPushButton:disabled { color: rgb(220, 220, 220); "
    "background-color: rgb(105, 120, 130); "
    "border-color: rgb(90, 100, 110); }"
)

_BUTTON_SIZE = QtCore.QSize(120, 34)
_ICON_SIZE = QtCore.QSize(22, 22)
_BUTTON_SPACING = 12
_PREVIOUS_ICON = ":/icons/icons/simbolo-de-setas-duplas-para-a-esquerda.png"
_NEXT_ICON = ":/icons/icons/simbolo-de-setas-duplas-para-a-direita-para-avancar.png"


def _is_wizard_navigation_button(button: QtWidgets.QPushButton) -> bool:
    name = button.objectName()
    return name.startswith("prev_btn_") or name.startswith("next_btn_")


# Navigation buttons are grouped by their direct parent layout before styling.
def _direct_button_layouts(
    window: QtWidgets.QWidget,
    buttons: Iterable[QtWidgets.QPushButton],
) -> dict[QtWidgets.QLayout, list[QtWidgets.QPushButton]]:
    """Group navigation buttons by the layout that directly contains them."""

    button_ids = {id(button): button for button in buttons}
    grouped: dict[QtWidgets.QLayout, list[QtWidgets.QPushButton]] = defaultdict(list)

    layouts = list(window.findChildren(QtWidgets.QLayout))
    root_layout = window.layout()
    if root_layout is not None and root_layout not in layouts:
        layouts.append(root_layout)

    for layout in layouts:
        for index in range(layout.count()):
            widget = layout.itemAt(index).widget()
            if widget is not None and id(widget) in button_ids:
                grouped[layout].append(button_ids[id(widget)])

    return grouped


def _position_navigation_at_edges(
    layout: QtWidgets.QLayout,
    buttons: Iterable[QtWidgets.QPushButton],
) -> None:
    """Place Previous at the lower-left and Next at the lower-right."""

    buttons = list(buttons)
    previous = next(
        (button for button in buttons if button.objectName().startswith("prev_btn_")),
        None,
    )
    next_button = next(
        (button for button in buttons if button.objectName().startswith("next_btn_")),
        None,
    )

    # These are dedicated navigation layouts. Taking their items only changes
    # presentation; the QPushButton instances, signals and enabled state remain intact.
    while layout.count():
        layout.takeAt(0)

    parent = layout.parentWidget()
    # Runtime-built pages can nest this row inside a layout that already has
    # horizontal margins. Avoid doubling the distance from the screen edges.
    horizontal_margin = 20 if parent is not None and parent.layout() is layout else 0
    layout.setContentsMargins(horizontal_margin, 0, horizontal_margin, 0)
    layout.setSpacing(_BUTTON_SPACING)
    if previous is not None:
        layout.addWidget(previous)
    layout.addStretch(1)
    if next_button is not None:
        layout.addWidget(next_button)


# Applies size, icons, spacing, and placement to Previous/Next buttons.
def install_wizard_navigation_style(window: QtWidgets.QWidget) -> None:
    """Apply the reusable wizard navigation style after UI construction.

    Buttons are discovered by the existing ``prev_btn_*``/``next_btn_*`` naming
    convention. This keeps generated and runtime-built pages visually aligned
    without duplicating styles in each screen.
    """

    buttons = [
        button
        for button in window.findChildren(QtWidgets.QPushButton)
        if _is_wizard_navigation_button(button)
    ]
    previous_icon = QtGui.QIcon(_PREVIOUS_ICON)
    next_icon = QtGui.QIcon(_NEXT_ICON)

    for button in buttons:
        is_next = button.objectName().startswith("next_btn_")
        button.setText("Next" if is_next else "Previous")
        button.setIcon(next_icon if is_next else previous_icon)
        button.setFixedSize(_BUTTON_SIZE)
        button.setIconSize(_ICON_SIZE)
        button.setLayoutDirection(
            QtCore.Qt.RightToLeft if is_next else QtCore.Qt.LeftToRight
        )
        button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet(WIZARD_NAVIGATION_STYLE)

    for layout, grouped_buttons in _direct_button_layouts(window, buttons).items():
        _position_navigation_at_edges(layout, grouped_buttons)
