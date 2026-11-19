"""Controller for secondary windows launched from the main Qt window."""

from __future__ import annotations

from typing import Any

from help_center import HelpCenterDialog


# Coordinates dialogs opened from the main simulation window.
class AuxiliaryWindowsController:
    """Open dialogs that are adjacent to the main simulation workflow."""

    def __init__(self, window: Any) -> None:
        self.window = window

# Reuses the help dialog so repeated clicks do not create duplicates.
    def open_help_center(self) -> None:
        if getattr(self.window, "help_center_window", None) is None:
            self.window.help_center_window = HelpCenterDialog(self.window)

        self.window.help_center_window.show()
        self.window.help_center_window.raise_()
        self.window.help_center_window.activateWindow()

# Opens a preview dialog for exporting the current layer table.
    def save_table(self) -> None:
        from sim_spr_lmr.presentation.qt.dialogs import SaveTableDialog

        self.window.dialog = SaveTableDialog(
            layers=self.window.layers,
            parent=self.window,
        )
        self.window.ui = self.window.dialog.ui
        self.window.dialog.show()

    def open_from_extern_file(self) -> None:
        from sim_spr_lmr.presentation.qt.dialogs import InstructionsDialog

        self.window.new_window = InstructionsDialog(parent=self.window)
        self.window.ui_2 = self.window.new_window.ui
        self.window.new_window.show()

# Opens the parametric-analysis workflow with the current context.
    def open_parametric_analysis(self) -> None:
        """Open the UI-only shell for configuring a future parameter sweep."""

        from sim_spr_lmr.presentation.qt.dialogs import ParametricAnalysisWindow

        session = self.window.session_state
        analyte_step_widget = getattr(
            self.window,
            "step_analyte_wim"
            if session.interrogation_mode_name == "WIM"
            else "step_analyte",
            None,
        )
        context = {
            "layers": self.window.layers,
            "thicknesses_m": self.window.d,
            "analyte_indices": self.window.index_ref_analyte,
            "analyte_step": (
                float(analyte_step_widget.value())
                if analyte_step_widget is not None
                else None
            ),
            "coupling": session.coupling_mode_name,
            "interrogation_mode": session.interrogation_mode_name,
            "incidence_angle_deg": (
                float(self.window.angle_incidence.value())
                if hasattr(self.window, "angle_incidence")
                else None
            ),
            "simulation_config": self.window.current_simulation_config,
        }
        if getattr(self.window, "parametric_analysis_window", None) is None:
            self.window.parametric_analysis_window = ParametricAnalysisWindow(
                parent=self.window,
                **context,
            )
        else:
            self.window.parametric_analysis_window.refresh_context(**context)
        self.window.parametric_analysis_window.show()
        self.window.parametric_analysis_window.raise_()
        self.window.parametric_analysis_window.activateWindow()

    def export_data(self) -> None:
        from sim_spr_lmr.presentation.qt.dialogs import SaveFilesDialog

        if self.window.current_simulation_result is None:
            return

        self.window.save_window = SaveFilesDialog(
            simulation_result=self.window.current_simulation_result,
            reflectance_scale=(
                self.window.simulation_run_controller.selected_reflectance_scale()
            ),
            parent=self.window,
        )
        self.window.ui_3 = self.window.save_window.ui
        self.window.save_window.show()
