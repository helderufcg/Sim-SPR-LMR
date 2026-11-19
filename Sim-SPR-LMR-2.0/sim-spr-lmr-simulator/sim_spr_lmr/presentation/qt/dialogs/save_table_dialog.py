"""Behavior wrapper for the generated layer-table export dialog UI."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from tabulate import tabulate

from save_table import Ui_Dialog

VISIBLE_LAYER_FIELDS = ("material", "thickness", "refractiveIndex", "description")
VISIBLE_LAYER_COLUMNS = ("Material", "Thickness (nm)", "Refract. Index", "Description")


# Displays the optical-layer table and exports it in the selected format.
class SaveTableDialog(QtWidgets.QDialog):
    """Dialog that previews and exports the current optical layer table."""

    def __init__(
        self,
        layers: Sequence[dict[str, object]] | None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.layers = list(layers or [])
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowIcon(QtGui.QIcon("icons/LOGO.png"))
        self.setWindowTitle("Save table")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowCloseButtonHint)

        try:
            self.ui.buttonBox.accepted.disconnect()
        except TypeError:
            pass
        self.ui.buttonBox.accepted.connect(self.save_table)

        self.show_table()

    # Builds the preview table from the stored layer dictionaries.
    def show_table(self) -> None:
        """Populate the table preview from the current layer rows."""

        self.ui.tableWidget_layers.setRowCount(len(self.layers))
        for row, layer in enumerate(self.layers):
            for column, field_name in enumerate(VISIBLE_LAYER_FIELDS):
                self.ui.tableWidget_layers.setItem(
                    row,
                    column,
                    QtWidgets.QTableWidgetItem(str(layer.get(field_name, ""))),
                )

    # Exports the table preview and reports success or failure.
    def save_table(self) -> None:
        """Persist the table in the format selected by the user."""

        table = self._build_dataframe_from_preview()
        base_name = self.ui.lineEdit.text().strip() or "Table 1"
        format_index = self.ui.comboBox.currentIndex()

        if format_index == 0:
            latex_code = tabulate(table, headers="keys", tablefmt="latex")
            self._write_text_file(f"{base_name}.tex", latex_code)
            self._show_success("Save to Latex")
        elif format_index == 1:
            table.to_excel(f"{base_name}.xlsx", sheet_name="Materials", index=False)
            self._show_success("Save to Excel")
        elif format_index == 2:
            table.to_csv(f"{base_name}.csv", index=False)
            self._show_success("Save to CSV")
        elif format_index == 3:
            self._write_text_file(f"{base_name}.txt", self._build_plain_text_table())
            self._show_success("Save to Text file")

        self.close()

    def _build_dataframe_from_preview(self) -> pd.DataFrame:
        rows = []
        for row in range(self.ui.tableWidget_layers.rowCount()):
            rows.append(
                [
                    self._table_text(row, column)
                    for column in range(self.ui.tableWidget_layers.columnCount())
                ]
            )
        return pd.DataFrame(rows, columns=VISIBLE_LAYER_COLUMNS)

    def _build_plain_text_table(self) -> str:
        lines = ["Material,Thickness (nm),Refract. Index,Description,"]
        for row in range(self.ui.tableWidget_layers.rowCount()):
            values = [
                self._table_text(row, column)
                for column in range(self.ui.tableWidget_layers.columnCount())
            ]
            lines.append(",".join(values) + ",")
        return "\n".join(lines) + "\n"

    def _table_text(self, row: int, column: int) -> str:
        item = self.ui.tableWidget_layers.item(row, column)
        return item.text() if item is not None else ""

    def _write_text_file(self, file_name: str, content: str) -> None:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(content)

    def _show_success(self, title: str) -> None:
        message = QtWidgets.QMessageBox(self)
        message.setIcon(QtWidgets.QMessageBox.Information)
        message.setWindowTitle(title)
        message.setText("Successfully saved file")
        message.exec()
