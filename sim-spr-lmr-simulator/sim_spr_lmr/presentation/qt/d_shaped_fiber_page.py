"""Runtime-built characteristics page for D-shaped optical fibers."""

from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Any

from PyQt5 import QtCore, QtGui, QtWidgets


# Styles and dimensions used by the runtime-built D-shaped fiber form.
INPUT_STYLE = (
    "QDoubleSpinBox { color: rgb(10, 25, 90); font: 700 12pt 'Ubuntu'; "
    "border: 2px solid rgb(23, 54, 93); background: rgba(255,255,255,210); "
    "border-radius: 10px; padding: 3px 28px 3px 8px; } "
    "QDoubleSpinBox::up-button { width: 25px; border-left: 1px solid darkgray; "
    "border-top-right-radius: 8px; image: url(:/icons/icons/arrow-up.png); } "
    "QDoubleSpinBox::down-button { width: 25px; border-left: 1px solid darkgray; "
    "border-bottom-right-radius: 8px; image: url(:/icons/icons/arrow-down.png); } "
    "QDoubleSpinBox:focus { border-color: rgb(0, 140, 180); }"
)
INPUT_ERROR_STYLE = (
    "QDoubleSpinBox { color: rgb(135, 18, 18); font: 700 12pt 'Ubuntu'; "
    "border: 2px solid rgb(190, 45, 45); background: rgb(255, 241, 241); "
    "border-radius: 10px; padding: 3px 28px 3px 8px; } "
    "QDoubleSpinBox::up-button { width: 25px; border-left: 1px solid darkgray; "
    "border-top-right-radius: 8px; image: url(:/icons/icons/arrow-up.png); } "
    "QDoubleSpinBox::down-button { width: 25px; border-left: 1px solid darkgray; "
    "border-bottom-right-radius: 8px; image: url(:/icons/icons/arrow-down.png); }"
)
COMBO_STYLE = (
    "QComboBox { color: rgb(10, 25, 90); font: 700 12pt 'Ubuntu'; "
    "border: 2px solid rgb(23, 54, 93); background: rgba(255,255,255,210); "
    "border-radius: 10px; padding: 3px 28px 3px 8px; } "
    "QComboBox::drop-down { width: 25px; border-left: 1px solid darkgray; "
    "border-top-right-radius: 8px; border-bottom-right-radius: 8px; } "
    "QComboBox::down-arrow { image: url(:/icons/icons/arrow-down.png); }"
)
CARD_STYLE = (
    "QGroupBox { color: rgb(23, 54, 93); "
    "border: 1px solid rgba(31, 78, 121, 150); border-radius: 12px; "
    "background: rgba(255,255,255,215); }"
)
SECTION_HEADER_STYLE = (
    "font: 500 12pt 'Ubuntu'; color: white; background: rgb(23, 54, 93); "
    "border: none; border-radius: 6px; padding: 6px 12px;"
)
LABEL_STYLE = "font: 600 10.5pt 'Ubuntu'; color: rgb(23, 54, 93);"
ERROR_STYLE = "font: 600 9pt 'Ubuntu'; color: rgb(176, 32, 32); padding-left: 4px;"
UNIFORM_CARD_HEIGHT = 630
SECTION_HEADER_HEIGHT = 42


# Keeps the preview image centered and proportional when the window is resized.
class AspectRatioPixmapLabel(QtWidgets.QLabel):
    """QLabel that keeps its source image sharp and aspect-ratio correct."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._source_pixmap = QtGui.QPixmap()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(360, 230)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def set_source_pixmap(self, pixmap: QtGui.QPixmap) -> None:
        self._source_pixmap = pixmap
        self._rescale_pixmap()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._rescale_pixmap()

    def _rescale_pixmap(self) -> None:
        if self._source_pixmap.isNull():
            return
        target = QtCore.QSize(max(self.width() - 20, 1), max(self.height() - 20, 1))
        self.setPixmap(
            self._source_pixmap.scaled(
                target,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )


# Small widget factories keep field construction consistent across the page.
def _spin_box(
    parent: QtWidgets.QWidget,
    *,
    object_name: str,
    minimum: float,
    maximum: float,
    value: float,
    decimals: int,
    step: float,
    suffix: str,
) -> QtWidgets.QDoubleSpinBox:
    widget = QtWidgets.QDoubleSpinBox(parent)
    widget.setObjectName(object_name)
    widget.setRange(minimum, maximum)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    widget.setSuffix(suffix)
    widget.setAlignment(QtCore.Qt.AlignCenter)
    widget.setMinimumWidth(175)
    widget.setMaximumWidth(220)
    widget.setMinimumHeight(32)
    widget.setMaximumHeight(36)
    widget.setStyleSheet(INPUT_STYLE)
    return widget


def _field_label(text: str, parent: QtWidgets.QWidget) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text, parent)
    label.setStyleSheet(LABEL_STYLE)
    label.setTextFormat(QtCore.Qt.RichText)
    label.setWordWrap(True)
    label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    return label


def _error_label(object_name: str, parent: QtWidgets.QWidget) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel("", parent)
    label.setObjectName(object_name)
    label.setWordWrap(True)
    label.setStyleSheet(ERROR_STYLE)
    label.setVisible(False)
    return label


def _add_field(
    layout: QtWidgets.QGridLayout,
    row: int,
    *,
    label_html: str,
    widget: QtWidgets.QWidget,
    parent: QtWidgets.QWidget,
    error: QtWidgets.QLabel | None = None,
) -> int:
    layout.addWidget(_field_label(label_html, parent), row, 0)
    layout.addWidget(widget, row, 1)
    row += 1
    if error is not None:
        layout.addWidget(error, row, 1)
        row += 1
    return row


def _set_field_error(
    widget: QtWidgets.QDoubleSpinBox,
    error_label: QtWidgets.QLabel,
    message: str,
) -> None:
    has_error = bool(message)
    widget.setStyleSheet(INPUT_ERROR_STYLE if has_error else INPUT_STYLE)
    error_label.setText(f"Warning: {message}" if has_error else "")
    error_label.setVisible(has_error)


# Builds and attaches the D-shaped fiber characteristics page at runtime.
def install_d_shaped_fiber_page(window: Any) -> None:
    """Create and register the D-shaped geometry page on the main wizard."""

    page = QtWidgets.QWidget()
    page.setObjectName("d_shaped_characteristics")
    page.setFont(QtGui.QFont("Ubuntu", 10))
    page_layout = QtWidgets.QVBoxLayout(page)
    # Keep the navigation controls aligned with the other wizard pages, which
    # anchor their Previous/Next row directly above the application footer.
    page_layout.setContentsMargins(20, 8, 20, 0)
    page_layout.setSpacing(8)

    breadcrumb = QtWidgets.QFrame(page)
    breadcrumb.setObjectName("d_shape_breadcrumb")
    breadcrumb.setStyleSheet("background: transparent;")
    breadcrumb_layout = QtWidgets.QHBoxLayout(breadcrumb)
    breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
    breadcrumb_layout.setSpacing(8)

    window.btn_home_d_shape = QtWidgets.QPushButton(breadcrumb)
    window.btn_home_d_shape.setObjectName("btn_home_d_shape")
    window.btn_home_d_shape.setFixedSize(20, 20)
    window.btn_home_d_shape.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    window.btn_home_d_shape.setIcon(QtGui.QIcon(":/icons/icons/casa.png"))
    window.btn_home_d_shape.setIconSize(QtCore.QSize(20, 20))
    window.btn_home_d_shape.setStyleSheet("background: transparent; border: none;")
    window.btn_home_d_shape.setToolTip("Home")
    breadcrumb_layout.addWidget(window.btn_home_d_shape)

    def add_breadcrumb_separator() -> None:
        separator_label = QtWidgets.QLabel("»", breadcrumb)
        separator_label.setStyleSheet("font: 600 13pt 'Ubuntu'; color: white;")
        separator_label.setAlignment(QtCore.Qt.AlignCenter)
        separator_label.setFixedWidth(12)
        breadcrumb_layout.addWidget(separator_label)

    add_breadcrumb_separator()
    window.btn_coupling_d_shape = QtWidgets.QPushButton("Optical Coupling", breadcrumb)
    window.btn_coupling_d_shape.setObjectName("btn_coupling_d_shape")
    window.btn_coupling_d_shape.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    window.btn_coupling_d_shape.setStyleSheet(
        "QPushButton { color: white; font: 500 10.5pt 'Ubuntu'; "
        "text-decoration: underline; background: transparent; border: none; padding: 0; }"
    )
    breadcrumb_layout.addWidget(window.btn_coupling_d_shape)
    add_breadcrumb_separator()

    window.btn_fiber_type_d_shape = QtWidgets.QPushButton("Fiber configuration", breadcrumb)
    window.btn_fiber_type_d_shape.setObjectName("btn_fiber_type_d_shape")
    window.btn_fiber_type_d_shape.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
    window.btn_fiber_type_d_shape.setStyleSheet(
        "QPushButton { color: white; font: 500 10.5pt 'Ubuntu'; "
        "text-decoration: underline; background: transparent; border: none; padding: 0; }"
    )
    breadcrumb_layout.addWidget(window.btn_fiber_type_d_shape)
    add_breadcrumb_separator()

    breadcrumb_current = QtWidgets.QLabel("D-shaped fiber characteristics", breadcrumb)
    breadcrumb_current.setObjectName("d_shape_breadcrumb_current")
    breadcrumb_current.setStyleSheet("font: 500 10.5pt 'Ubuntu'; color: white;")
    breadcrumb_layout.addWidget(breadcrumb_current)
    breadcrumb_layout.addStretch(1)
    page_layout.addWidget(breadcrumb)

    title = QtWidgets.QLabel("Characteristics of D-shaped fiber with residual cladding", page)
    title.setObjectName("d_shaped_characteristics_title")
    title.setAlignment(QtCore.Qt.AlignCenter)
    title.setStyleSheet('font: 500 18pt "Ubuntu"; color: white; padding: 4px;')
    page_layout.addWidget(title)

    description = QtWidgets.QLabel(
        "Configure the polished-fiber geometry and optical properties. "
        "The residual cladding is inserted automatically in the optical stack.",
        page,
    )
    description.setWordWrap(True)
    description.setAlignment(QtCore.Qt.AlignCenter)
    description.setStyleSheet(
        'font: 500 10.5pt "Ubuntu"; color: rgba(255,255,255,225); '
        "background: transparent; padding: 2px 12px;"
    )
    description.setMaximumWidth(1120)
    page_layout.addWidget(description, 0, QtCore.Qt.AlignHCenter)

    body_scroll = QtWidgets.QScrollArea(page)
    body_scroll.setObjectName("d_shape_body_scroll")
    body_scroll.setWidgetResizable(True)
    body_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
    body_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
    body_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

    body = QtWidgets.QWidget()
    body.setStyleSheet("background: transparent;")
    body_layout = QtWidgets.QHBoxLayout(body)
    body_layout.setContentsMargins(24, 4, 24, 4)
    body_layout.setSpacing(18)
    body_layout.setAlignment(QtCore.Qt.AlignVCenter)

    geometry_group = QtWidgets.QGroupBox("", body)
    geometry_group.setObjectName("d_shaped_geometry_group")
    geometry_group.setMinimumWidth(400)
    geometry_group.setMaximumWidth(570)
    geometry_group.setFixedHeight(UNIFORM_CARD_HEIGHT)
    geometry_group.setStyleSheet(CARD_STYLE)
    geometry_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    geometry_layout = QtWidgets.QGridLayout(geometry_group)
    geometry_layout.setContentsMargins(18, 16, 18, 18)
    geometry_layout.setHorizontalSpacing(18)
    geometry_layout.setVerticalSpacing(7)
    geometry_layout.setColumnStretch(0, 1)

    window.d_shape_length = _spin_box(
        geometry_group,
        object_name="d_shape_length",
        minimum=0.01,
        maximum=100.0,
        value=10.0,
        decimals=2,
        step=0.1,
        suffix=" mm",
    )
    window.d_shape_length.setToolTip("L: length of the polished D-shaped sensing region.")

    window.d_shape_core_diameter = _spin_box(
        geometry_group,
        object_name="d_shape_core_diameter",
        minimum=0.1,
        maximum=1000.0,
        value=9.0,
        decimals=2,
        step=0.1,
        suffix=" um",
    )
    window.d_shape_core_diameter.setToolTip(
        "D_cr = 2*r_core: core diameter; r_core is the core radius."
    )

    window.d_shape_outer_diameter = _spin_box(
        geometry_group,
        object_name="d_shape_outer_diameter",
        minimum=1.0,
        maximum=2000.0,
        value=125.0,
        decimals=2,
        step=1.0,
        suffix=" um",
    )
    window.d_shape_outer_diameter.setToolTip(
        "D_cl = 2*r_cl: total fiber diameter; r_cl is the fiber outer radius."
    )

    window.d_shape_residual_cladding = _spin_box(
        geometry_group,
        object_name="d_shape_residual_cladding",
        minimum=0.0,
        maximum=500.0,
        value=1.0,
        decimals=3,
        step=0.1,
        suffix=" um",
    )
    window.d_shape_residual_cladding.setToolTip(
        "d_cl: residual cladding thickness between the core boundary and the D surface."
    )

    window.d_shape_core_error = _error_label("d_shape_core_error", geometry_group)
    window.d_shape_residual_error = _error_label("d_shape_residual_error", geometry_group)

    geometry_heading = QtWidgets.QLabel("Geometry", geometry_group)
    geometry_heading.setObjectName("d_shape_geometry_heading")
    geometry_heading.setStyleSheet(SECTION_HEADER_STYLE)
    geometry_heading.setFixedHeight(SECTION_HEADER_HEIGHT)
    geometry_heading.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    geometry_layout.addWidget(geometry_heading, 0, 0, 1, 2)

    row = 1
    row = _add_field(
        geometry_layout,
        row,
        label_html="Longitudinal D-region length, <i>L</i>",
        widget=window.d_shape_length,
        parent=geometry_group,
    )
    row = _add_field(
        geometry_layout,
        row,
        label_html="Core diameter, <i>D</i><sub>cr</sub> = 2<i>r</i><sub>core</sub>",
        widget=window.d_shape_core_diameter,
        parent=geometry_group,
        error=window.d_shape_core_error,
    )
    row = _add_field(
        geometry_layout,
        row,
        label_html="Fiber outer diameter, <i>D</i><sub>cl</sub> = 2<i>r</i><sub>cl</sub>",
        widget=window.d_shape_outer_diameter,
        parent=geometry_group,
    )
    row = _add_field(
        geometry_layout,
        row,
        label_html="Residual cladding thickness, <i>d</i><sub>cl</sub>",
        widget=window.d_shape_residual_cladding,
        parent=geometry_group,
        error=window.d_shape_residual_error,
    )

    separator = QtWidgets.QFrame(geometry_group)
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setStyleSheet("color: rgba(31, 78, 121, 90);")
    geometry_layout.addWidget(separator, row, 0, 1, 2)
    row += 1

    derived_label = _field_label(
        "D-surface width, <i>W</i> "
        "<span style='font-size:9pt; color:#52697c;'>(derived)</span>",
        geometry_group,
    )
    window.d_shape_polished_width = QtWidgets.QLineEdit(geometry_group)
    window.d_shape_polished_width.setObjectName("d_shape_polished_width")
    window.d_shape_polished_width.setReadOnly(True)
    window.d_shape_polished_width.setAlignment(QtCore.Qt.AlignCenter)
    window.d_shape_polished_width.setMinimumWidth(175)
    window.d_shape_polished_width.setMaximumWidth(220)
    window.d_shape_polished_width.setMinimumHeight(32)
    window.d_shape_polished_width.setMaximumHeight(36)
    window.d_shape_polished_width.setStyleSheet(
        "QLineEdit { color: rgb(10, 25, 90); font: 700 12pt 'Ubuntu'; "
        "border: 2px solid rgb(82, 105, 125); background: rgb(236,241,246); "
        "border-radius: 10px; padding: 3px 8px; }"
    )
    formula_tooltip = (
        "Calculated automatically: W = 2*sqrt(r_cl^2 - h^2), "
        "where h = r_core + d_cl is the center-to-D-surface distance."
    )
    derived_label.setToolTip(formula_tooltip)
    window.d_shape_polished_width.setToolTip(formula_tooltip)
    geometry_layout.addWidget(derived_label, row, 0)
    geometry_layout.addWidget(window.d_shape_polished_width, row, 1)
    row += 1

    derived_badge = QtWidgets.QLabel("CALCULATED AUTOMATICALLY | read-only", geometry_group)
    derived_badge.setObjectName("d_shape_derived_badge")
    derived_badge.setAlignment(QtCore.Qt.AlignCenter)
    derived_badge.setToolTip(formula_tooltip)
    derived_badge.setStyleSheet(
        "font: 600 8.5pt 'Ubuntu'; color: rgb(55, 78, 96); "
        "background: rgb(224,232,239); border-radius: 7px; padding: 3px 7px;"
    )
    geometry_layout.addWidget(derived_badge, row, 1)
    geometry_layout.setRowStretch(row + 1, 1)

    optical_group = QtWidgets.QGroupBox("", body)
    optical_group.setObjectName("d_shaped_optical_group")
    optical_group.setMinimumWidth(400)
    optical_group.setMaximumWidth(570)
    optical_group.setFixedHeight(UNIFORM_CARD_HEIGHT)
    optical_group.setStyleSheet(CARD_STYLE)
    optical_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    optical_layout = QtWidgets.QGridLayout(optical_group)
    optical_layout.setContentsMargins(18, 16, 18, 18)
    optical_layout.setHorizontalSpacing(18)
    optical_layout.setVerticalSpacing(10)
    optical_layout.setColumnStretch(0, 1)

    window.d_shape_numerical_aperture = _spin_box(
        optical_group,
        object_name="d_shape_numerical_aperture",
        minimum=0.001,
        maximum=1.0,
        value=0.12,
        decimals=3,
        step=0.01,
        suffix="",
    )
    window.d_shape_numerical_aperture.setToolTip(
        "NA: numerical aperture used to derive the fluorinated-cladding index."
    )

    window.d_shape_core_material = QtWidgets.QComboBox(optical_group)
    window.d_shape_core_material.setObjectName("d_shape_core_material")
    window.d_shape_core_material.addItem("Silica")
    window.d_shape_core_material.addItem("PMMA")
    window.d_shape_core_material.setMinimumWidth(175)
    window.d_shape_core_material.setMaximumWidth(220)
    window.d_shape_core_material.setMinimumHeight(32)
    window.d_shape_core_material.setMaximumHeight(36)
    window.d_shape_core_material.setStyleSheet(COMBO_STYLE)
    window.d_shape_core_material.setToolTip(
        "n_cr(lambda): dispersive refractive index of the fiber core."
    )

    optical_heading = QtWidgets.QLabel("Optical Properties", optical_group)
    optical_heading.setObjectName("d_shape_optical_heading")
    optical_heading.setStyleSheet(SECTION_HEADER_STYLE)
    optical_heading.setFixedHeight(SECTION_HEADER_HEIGHT)
    optical_heading.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    optical_layout.addWidget(optical_heading, 0, 0, 1, 2)

    _add_field(
        optical_layout,
        2,
        label_html="Numerical aperture, <i>NA</i>",
        widget=window.d_shape_numerical_aperture,
        parent=optical_group,
    )
    _add_field(
        optical_layout,
        3,
        label_html="Core material, <i>n</i><sub>cr</sub>(&lambda;)",
        widget=window.d_shape_core_material,
        parent=optical_group,
    )

    optical_layout.setRowStretch(1, 1)
    optical_layout.setRowStretch(4, 1)

    preview_group = QtWidgets.QGroupBox("", body)
    preview_group.setObjectName("d_shaped_preview_group")
    preview_group.setMinimumWidth(400)
    preview_group.setMaximumWidth(570)
    preview_group.setFixedHeight(UNIFORM_CARD_HEIGHT)
    preview_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    preview_group.setStyleSheet(CARD_STYLE)
    preview_layout = QtWidgets.QVBoxLayout(preview_group)
    preview_layout.setContentsMargins(14, 16, 14, 14)
    preview_layout.setSpacing(8)

    preview_heading = QtWidgets.QLabel("Geometry Preview", preview_group)
    preview_heading.setObjectName("d_shape_preview_heading")
    preview_heading.setStyleSheet(SECTION_HEADER_STYLE)
    preview_heading.setFixedHeight(SECTION_HEADER_HEIGHT)
    preview_heading.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    preview_layout.addWidget(preview_heading)

    window.d_shape_geometry_preview = AspectRatioPixmapLabel(preview_group)
    window.d_shape_geometry_preview.setObjectName("d_shape_geometry_preview")
    window.d_shape_geometry_preview.setStyleSheet(
        "background: white; border: 1px solid rgba(31,78,121,100); border-radius: 10px;"
    )
    image_path = Path(__file__).resolve().parents[3] / "icons" / "D-shaped geometry.png"
    preview_pixmap = QtGui.QPixmap(str(image_path))
    if preview_pixmap.isNull():
        window.d_shape_geometry_preview.setText(
            "Geometry image unavailable.\nExpected: icons/D-shaped geometry.png"
        )
        window.d_shape_geometry_preview.setStyleSheet(
            "font: 600 10pt 'Ubuntu'; color: rgb(150,30,30); "
            "background: white; border: 1px solid rgb(190,45,45); border-radius: 10px;"
        )
    else:
        window.d_shape_geometry_preview.set_source_pixmap(preview_pixmap)
        window.d_shape_geometry_preview.setToolTip(str(image_path))
    preview_layout.addWidget(window.d_shape_geometry_preview, 1)

    notation = QtWidgets.QLabel(
        "<b>Notation</b>"
        "<table width='100%' cellspacing='0' cellpadding='0'>"
        "<tr>"
        "<td width='48%' valign='top'>"
        "<i>r</i><sub>core</sub>: core radius<br>"
        "<i>r</i><sub>cl</sub>: fiber outer radius<br>"
        "<i>d</i><sub>cl</sub>: residual cladding thickness<br>"
        "<i>L</i>: longitudinal length of the D region<br>"
        "θ<sub>i</sub>: incidence angle relative to the normal"
        "</td>"
        "<td width='4%'>&nbsp;</td>"
        "<td width='48%' valign='top'>"
        "<i>h</i> = <i>r</i><sub>core</sub> + <i>d</i><sub>cl</sub>: center-to-D-surface distance<br>"
        "<i>d</i><sub>p</sub> = <i>r</i><sub>cl</sub> − <i>h</i>: polishing depth<br>"
        "<i>W</i> = 2√(<i>r</i><sub>cl</sub><sup>2</sup> − <i>h</i><sup>2</sup>): D-surface width<br>"
        "<i>D</i><sub>eff</sub> = <i>r</i><sub>cl</sub> + <i>h</i>: D-surface-to-opposite-side distance"
        "</td>"
        "</tr>"
        "</table>",
        preview_group,
    )
    notation.setObjectName("d_shape_notation")
    notation.setTextFormat(QtCore.Qt.RichText)
    notation.setWordWrap(True)
    notation.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
    notation.setStyleSheet(
        "font: 9pt 'Ubuntu'; color: rgb(28,48,68); "
        "background: rgba(230,238,245,205); border-radius: 8px; padding: 10px 12px;"
    )
    # Let the two-column legend grow only when a narrower window wraps text.
    # On wide screens it stays compact so the geometry drawing receives more height.
    notation.setMinimumHeight(210)
    notation.setMaximumHeight(270)
    notation.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    notation.setToolTip(
        "The form accepts diameters D_cr = 2*r_core and D_cl = 2*r_cl."
    )
    preview_layout.addWidget(notation)

    body_layout.addWidget(geometry_group, 1)
    body_layout.addWidget(preview_group, 1)
    body_layout.addWidget(optical_group, 1)
    body_scroll.setWidget(body)
    page_layout.addWidget(body_scroll, 1)

    window.d_shape_warning = QtWidgets.QLabel("", page)
    window.d_shape_warning.setObjectName("d_shape_warning")
    window.d_shape_warning.setAlignment(QtCore.Qt.AlignCenter)
    window.d_shape_warning.setWordWrap(True)
    window.d_shape_warning.setStyleSheet('font: 600 9.5pt "Ubuntu"; color: #B21222;')
    page_layout.addWidget(window.d_shape_warning)

    actions = QtWidgets.QHBoxLayout()
    window.prev_btn_d_shape = QtWidgets.QPushButton("Previous", page)
    window.prev_btn_d_shape.setObjectName("prev_btn_d_shape")
    window.next_btn_d_shape = QtWidgets.QPushButton("Next", page)
    window.next_btn_d_shape.setObjectName("next_btn_d_shape")
    actions.addWidget(window.prev_btn_d_shape)
    actions.addStretch(1)
    actions.addWidget(window.next_btn_d_shape)
    page_layout.addLayout(actions)

    def update_geometry_feedback() -> None:
        core_diameter = window.d_shape_core_diameter.value()
        outer_diameter = window.d_shape_outer_diameter.value()
        residual = window.d_shape_residual_cladding.value()
        outer_radius = outer_diameter / 2.0
        polishing_depth = core_diameter / 2.0 + residual

        core_error = ""
        if core_diameter >= outer_diameter:
            core_error = "Core diameter must be smaller than the fiber outer diameter."

        residual_error = ""
        if residual > outer_radius:
            residual_error = "Residual cladding cannot exceed the fiber radius."
        elif not core_error and polishing_depth >= outer_radius:
            residual_error = (
                "Core radius plus residual cladding must remain smaller than the fiber radius."
            )

        _set_field_error(
            window.d_shape_core_diameter,
            window.d_shape_core_error,
            core_error,
        )
        _set_field_error(
            window.d_shape_residual_cladding,
            window.d_shape_residual_error,
            residual_error,
        )

        is_valid = not core_error and not residual_error
        window.next_btn_d_shape.setEnabled(is_valid)
        window.d_shape_warning.setText(
            "" if is_valid else "Review the highlighted geometry values before continuing."
        )

        if is_valid:
            width = 2.0 * sqrt(max(outer_radius**2 - polishing_depth**2, 0.0))
            window.d_shape_polished_width.setText(f"{width:.2f} um")
        else:
            window.d_shape_polished_width.setText("Unavailable")

    window.d_shape_outer_diameter.valueChanged.connect(update_geometry_feedback)
    window.d_shape_core_diameter.valueChanged.connect(update_geometry_feedback)
    window.d_shape_residual_cladding.valueChanged.connect(update_geometry_feedback)
    update_geometry_feedback()

    window.d_shaped_characteristics = page
    window.Stacked_windows.addWidget(page)
