"""Qt-oriented presentation helpers.

This subpackage owns visual state rules for widgets, leaving ``main.py`` to
focus on signals, navigation and orchestration.
"""

from .layer_editor_presenter import (
    disable_analyte_inputs,
    disable_layer_inputs,
    enable_analyte_inputs,
    enable_layer_inputs,
    populate_analyte_edit_form,
    populate_layer_edit_form,
)
from .controllers import (
    AuxiliaryWindowsController,
    LayerStackController,
    NavigationController,
    SimulationRunController,
)
from .main_window_binder import bind_main_window_events
from .d_shaped_fiber_page import install_d_shaped_fiber_page
from .presenters import DispersionPresenter, FiberFormPresenter
from .range_slider_compat import install_range_slider_compatibility
from .state import SimulationSessionState
from .wizard_navigation import install_wizard_navigation_style

__all__ = [
    "AuxiliaryWindowsController",
    "DispersionPresenter",
    "FiberFormPresenter",
    "LayerStackController",
    "NavigationController",
    "SimulationRunController",
    "SimulationSessionState",
    "bind_main_window_events",
    "install_d_shaped_fiber_page",
    "disable_analyte_inputs",
    "disable_layer_inputs",
    "enable_analyte_inputs",
    "enable_layer_inputs",
    "install_range_slider_compatibility",
    "install_wizard_navigation_style",
    "populate_analyte_edit_form",
    "populate_layer_edit_form",
]
