"""State shared by the main Qt window and its controllers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
# Stores the choices made while moving through the simulation wizard.
class SimulationSessionState:
    """Current simulation choices made through the wizard."""

    coupling_mode: int = 0
    interrogation_mode: int = 0
    simulator: str = ""
    fiber_type_code: int = 0

    # Clears every session choice and returns the wizard to its initial state.
    def reset(self) -> None:
        self.coupling_mode = 0
        self.interrogation_mode = 0
        self.simulator = ""
        self.fiber_type_code = 0

    # Clears navigation choices while preserving the selected simulator.
    def reset_navigation_choices(self) -> None:
        self.coupling_mode = 0
        self.interrogation_mode = 0
        self.fiber_type_code = 0

    @property
    def is_lmr_spr(self) -> bool:
        return self.simulator == "LMR+SPR"

    @property
    def interrogation_mode_name(self) -> str:
        if self.interrogation_mode == 1:
            return "AIM"
        if self.interrogation_mode == 2:
            return "WIM"
        return "Unknown"

    @property
    def coupling_mode_name(self) -> str:
        if self.coupling_mode == 1:
            return "Prism"
        if self.coupling_mode == 2:
            return "Fiber"
        return "Unknown"
