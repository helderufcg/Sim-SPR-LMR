# UI source files

This directory location for maintained Qt Designer source files and preserved UI references.

Historical Qt Designer files copied from the official version 1.0 are kept in `legacy-v1.0/`. They are reference-only artifacts and are not authoritative sources for regenerating the version 2.0 runtime interface. 

`main_interface_stable_legacy.ui` is a preserved reference for the stable visual lineage associated with the current runtime `Sim_LMR_interface.py`. Opening it in Qt Designer does not reproduce the current runtime exactly, because the runtime Python file to contain manual visual edits that were not carried back into a `.ui` source.

The main runtime file remains: `sim-spr-lmr-simulator/Sim_LMR_interface.py`

Do not regenerate or overwrite that file from Qt Designer until a faithful main-interface `.ui` is reconstructed and validated separately.

The current runtime still imports generated Python modules from:

`sim-spr-lmr-simulator/`

Use the scripts in `tools/` to regenerate those modules:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_resources.ps1
powershell -ExecutionPolicy Bypass -File .\tools\build_ui.ps1
```

`build_ui.ps1` writes generated modules to `.tmp/generated-ui` by default and intentionally excludes `Sim_LMR_interface.py`. Use `-Apply` only for the secondary dialogs whose manual logic has already been extracted.

- `save_files.py`: Its behavior lives in  `sim_spr_lmr/presentation/qt/dialogs/save_files_dialog.py`.
- `save_table.py`: Its behavior lives in  `sim_spr_lmr/presentation/qt/dialogs/save_table_dialog.py`, and the table widget now belongs to `ui/save_table.ui`.
- `instructions.py`: Its behavior lives in `sim_spr_lmr/presentation/qt/dialogs/instructions_dialog.py`.
- `open_extern_file.py`: Its behavior lives in  `sim_spr_lmr/presentation/qt/dialogs/external_file_analysis_window.py`, and the  remove-file buttons now belong to `ui/open_extern_file.ui`.
- `Sim_LMR_interface.py`: frozen runtime artifact. No active `.ui` source is  currently authoritative for this file.
- `main_interface_stable_legacy.ui`: historical/reference only.

Before regenerating resources, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\check_ui_resources.ps1
```

The `.ui` files under `ui/` are the maintained sources for the secondary dialogs. Their generated Python modules remain in `sim-spr-lmr-simulator/` for runtime compatibility, but dialog behavior is implemented under `presentation/qt/dialogs/`. The main window is the exception: `Sim_LMR_interface.py` remains authoritative at runtime and must not be regenerated from `ui/main_interface_stable_legacy.ui`, which is only a visual reference. See this `ui/README_ui.md` before changing or regenerating Qt files.