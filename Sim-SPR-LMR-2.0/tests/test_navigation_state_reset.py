from __future__ import annotations

import unittest
from types import SimpleNamespace

from sim_spr_lmr.presentation.qt.controllers.layer_stack_controller import (
    LayerStackController,
)
from sim_spr_lmr.presentation.qt.controllers.navigation_controller import (
    NavigationController,
)
from sim_spr_lmr.presentation.qt.state import SimulationSessionState


class _WidgetRecorder:
    def __init__(self) -> None:
        self.current_widget = None
        self.enabled = None
        self.hidden = None
        self.text = ""
        self.selection_cleared = False

    def setCurrentWidget(self, widget: object) -> None:
        self.current_widget = widget

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def setChecked(self, checked: bool) -> None:
        self.checked = checked

    def setHidden(self, hidden: bool) -> None:
        self.hidden = hidden

    def setText(self, text: str) -> None:
        self.text = text

    def clearSelection(self) -> None:
        self.selection_cleared = True


class _LayerStackRecorder:
    def __init__(self) -> None:
        self.reset_count = 0

    def reset_layer_stack(self) -> None:
        self.reset_count += 1


class NavigationStateResetTests(unittest.TestCase):
    def test_new_simulation_opens_selection_and_resets_previous_session(self) -> None:
        selection_page = object()
        layer_stack = _LayerStackRecorder()
        state = SimulationSessionState(
            coupling_mode=1,
            interrogation_mode=1,
            simulator="SPR",
            fiber_type_code=1,
        )
        window = SimpleNamespace(
            Stacked_windows=_WidgetRecorder(),
            Select_simulator=selection_page,
            session_state=state,
            layer_stack_controller=layer_stack,
            current_simulation_config=object(),
            current_simulation_result=object(),
            label_title=_WidgetRecorder(),
            label_footer=_WidgetRecorder(),
            aim_btn=_WidgetRecorder(),
            wim_btn=_WidgetRecorder(),
        )
        controller = NavigationController(window)
        controller.configure_coupling_options = lambda **_options: None

        controller.start_new_simulation()

        self.assertIs(window.Stacked_windows.current_widget, selection_page)
        self.assertEqual(state, SimulationSessionState())
        self.assertEqual(layer_stack.reset_count, 1)
        self.assertIsNone(window.current_simulation_config)
        self.assertIsNone(window.current_simulation_result)

    def test_changing_coupling_resets_stack_but_reselecting_it_does_not(self) -> None:
        layer_stack = _LayerStackRecorder()
        state = SimulationSessionState(coupling_mode=1)
        window = SimpleNamespace(
            session_state=state,
            layer_stack_controller=layer_stack,
            warning_2=_WidgetRecorder(),
            cladding_remove_btn=_WidgetRecorder(),
            d_shaped_fiber_btn=_WidgetRecorder(),
            warning_fiber_typ=_WidgetRecorder(),
        )
        controller = NavigationController(window)

        controller.fiber_btn_clicked()
        controller.fiber_btn_clicked()

        self.assertEqual(state.coupling_mode, 2)
        self.assertEqual(layer_stack.reset_count, 1)

    def test_changing_interrogation_mode_resets_stack(self) -> None:
        layer_stack = _LayerStackRecorder()
        state = SimulationSessionState(interrogation_mode=1)
        window = SimpleNamespace(
            session_state=state,
            layer_stack_controller=layer_stack,
            warning_inter=_WidgetRecorder(),
        )

        NavigationController(window).wim_btn_clicked()

        self.assertEqual(state.interrogation_mode, 2)
        self.assertEqual(layer_stack.reset_count, 1)

    def test_selecting_a_simulator_always_starts_with_an_empty_stack(self) -> None:
        layer_stack = _LayerStackRecorder()
        state = SimulationSessionState(simulator="SPR")
        window = SimpleNamespace(
            Stacked_windows=_WidgetRecorder(),
            coupling_window=object(),
            session_state=state,
            layer_stack_controller=layer_stack,
            aim_btn=_WidgetRecorder(),
            wim_btn=_WidgetRecorder(),
            label_title=_WidgetRecorder(),
            label_footer=_WidgetRecorder(),
        )
        controller = NavigationController(window)
        controller.configure_coupling_options = lambda **_options: None
        controller.configure_wim_controls_for_simulator = lambda: None

        controller.spr_selected()

        self.assertEqual(layer_stack.reset_count, 1)


class LayerStackResetTests(unittest.TestCase):
    def test_reset_layer_stack_clears_all_parallel_collections_and_ui(self) -> None:
        table = _WidgetRecorder()
        warning = _WidgetRecorder()
        calls = {"layer_form": 0, "analyte_form": 0}
        window = SimpleNamespace(
            layers=[{"material": "Gold"}],
            material=["Gold"],
            material_id=[4],
            d=[50e-9],
            indexRef=[0.2 + 3j],
            index_ref_analyte=[1.33 + 0j],
            nLayers=1,
            tableWidget_layers=table,
            warning=warning,
            clear_layer_form_inputs=lambda: calls.__setitem__("layer_form", 1),
            clear_analyte_form_inputs=lambda: calls.__setitem__("analyte_form", 1),
        )
        controller = LayerStackController(window)
        controller.show_layers = lambda: None
        controller.sync_layer_management_buttons = lambda: None

        controller.reset_layer_stack()

        self.assertEqual(window.layers, [])
        self.assertEqual(window.material, [])
        self.assertEqual(window.material_id, [])
        self.assertEqual(window.d, [])
        self.assertEqual(window.indexRef, [])
        self.assertEqual(window.index_ref_analyte, [])
        self.assertEqual(window.nLayers, 0)
        self.assertTrue(table.selection_cleared)
        self.assertTrue(warning.hidden)
        self.assertEqual(calls, {"layer_form": 1, "analyte_form": 1})


if __name__ == "__main__":
    unittest.main()
