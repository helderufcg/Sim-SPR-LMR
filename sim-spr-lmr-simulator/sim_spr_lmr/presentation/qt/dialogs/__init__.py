"""Dialog wrappers that keep behavior out of generated Qt UI modules."""

from .external_file_analysis_window import ExternalFileAnalysisWindow
from .instructions_dialog import InstructionsDialog
from .parametric_analysis_window import ParametricAnalysisWindow
from .save_files_dialog import SaveFilesDialog
from .save_table_dialog import SaveTableDialog

__all__ = [
    "ExternalFileAnalysisWindow",
    "InstructionsDialog",
    "ParametricAnalysisWindow",
    "SaveFilesDialog",
    "SaveTableDialog",
]
