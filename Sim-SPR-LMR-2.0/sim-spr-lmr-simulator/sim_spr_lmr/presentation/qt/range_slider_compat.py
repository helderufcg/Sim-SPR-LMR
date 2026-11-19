"""Runtime compatibility for range sliders kept out of generated UI modules."""

from __future__ import annotations

from PyQt5 import QtCore, QtWidgets

try:
# The optional dependency is used when available; the proxy below is the fallback.
    from qtrangeslider import QDoubleRangeSlider, QRangeSlider
except ImportError:  # pragma: no cover - exercised only without optional dependency.
    QDoubleRangeSlider = None
    QRangeSlider = None


RANGE_SLIDER_STYLE = """
QSlider {
    min-height: 20px;
}
QSlider::groove:horizontal {
    border: 0px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #888, stop:1 #ddd);
    height: 20px;
    border-radius: 10px;
}
QSlider::handle {
    background: qradialgradient(cx:0, cy:0, radius: 1.2, fx:0.35,
                                fy:0.3, stop:0 #eef, stop:1 #002);
    height: 20px;
    width: 20px;
    border-radius: 10px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF17365D, stop:1 #77a);
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
}
QRangeSlider {
    qproperty-barColor: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF17365D, stop:1 #77a);
}
"""


# Exposes a range-slider API backed by conventional Qt spin boxes.
class RangeSliderProxy(QtCore.QObject):
    """Range-slider-like API backed by two spin boxes.

    The app can still run if the optional ``qtrangeslider`` package is missing;
    in that case the two numeric inputs remain the source of truth.
    """

    valueChanged = QtCore.pyqtSignal()

    def __init__(self, start_widget, stop_widget, placeholder_widget=None):
        super().__init__()
        self._start_widget = start_widget
        self._stop_widget = stop_widget
        self._placeholder_widget = placeholder_widget
        self._start_widget.valueChanged.connect(self._emit_if_changed)
        self._stop_widget.valueChanged.connect(self._emit_if_changed)

    def value(self):
        return (float(self._start_widget.value()), float(self._stop_widget.value()))

    def setValue(self, value):
        try:
            start_value, stop_value = value
        except (TypeError, ValueError):
            return

        current_start, current_stop = self.value()
        if current_start == float(start_value) and current_stop == float(stop_value):
            return

        self._start_widget.setValue(float(start_value))
        self._stop_widget.setValue(float(stop_value))

    def setRange(self, minimum, maximum):
        self._start_widget.setRange(float(minimum), float(maximum))
        self._stop_widget.setRange(float(minimum), float(maximum))

    def setEnabled(self, enabled):
        if self._placeholder_widget is not None:
            self._placeholder_widget.setEnabled(enabled)

    def setVisible(self, visible):
        if self._placeholder_widget is not None:
            self._placeholder_widget.setVisible(visible)

    def _emit_if_changed(self, *_args):
        self.valueChanged.emit()


# Replaces or augments the generated UI with a compatible range control.
def install_range_slider_compatibility(
    window,
    *,
    range_attr_name: str,
    placeholder_attr_name: str,
    start_widget,
    stop_widget,
    range_bounds: tuple[float, float],
    default_value: tuple[float, float],
    single_step: float,
) -> None:
    """Replace a generated QSlider placeholder with a QDoubleRangeSlider."""

    current_widget = getattr(window, range_attr_name, None)
    if _is_range_slider(current_widget):
        return

    placeholder_widget = getattr(window, placeholder_attr_name, current_widget)
    if QDoubleRangeSlider is None or not isinstance(placeholder_widget, QtWidgets.QWidget):
        start_widget.setValue(float(default_value[0]))
        stop_widget.setValue(float(default_value[1]))
        proxy = RangeSliderProxy(start_widget, stop_widget, placeholder_widget)
        proxy.setRange(*range_bounds)
        setattr(window, range_attr_name, proxy)
        return

    range_widget = QDoubleRangeSlider(QtCore.Qt.Horizontal, placeholder_widget.parentWidget())
    range_widget.setObjectName(range_attr_name)
    range_widget.setMinimumSize(QtCore.QSize(300, 25))
    range_widget.setMaximumSize(QtCore.QSize(16777215, 25))
    range_widget.setSizePolicy(placeholder_widget.sizePolicy())
    range_widget.setRange(*range_bounds)
    range_widget.setSingleStep(single_step)
    range_widget.setValue(default_value)
    range_widget.setStyleSheet(RANGE_SLIDER_STYLE)

    parent_layout = placeholder_widget.parentWidget().layout()
    if parent_layout is not None:
        parent_layout.replaceWidget(placeholder_widget, range_widget)

    placeholder_widget.setObjectName(f"{placeholder_widget.objectName()}_legacy")
    placeholder_widget.hide()
    placeholder_widget.setEnabled(False)
    placeholder_widget.deleteLater()

    start_widget.setValue(float(range_widget.value()[0]))
    stop_widget.setValue(float(range_widget.value()[1]))
    setattr(window, range_attr_name, range_widget)


def _is_range_slider(widget) -> bool:
    slider_classes = tuple(
        slider_class
        for slider_class in (QDoubleRangeSlider, QRangeSlider)
        if slider_class is not None
    )
    return bool(slider_classes) and isinstance(widget, slider_classes)
