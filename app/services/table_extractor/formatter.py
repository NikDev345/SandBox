"""
Table Formatter

Converts extracted table data into various export formats.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class TableFormatter:
    """
    Converts canonical table structures into
    Excel, CSV, JSON, Markdown and HTML.
    """

    def __init__(self, output_directory: str | Path = "temp/table_extractor"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def _dataframe(self, table: dict[str, Any]) -> pd.DataFrame:
        """
        Convert canonical table into pandas DataFrame.
        """

        rows = table.get("rows", [])

        if not rows:
            return pd.DataFrame()

        headers = rows[0]
        data = rows[1:]

        return pd.DataFrame(data, columns=headers)

    def to_excel(
        self,
        tables: list[dict[str, Any]],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.xlsx"

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            for index, table in enumerate(tables, start=1):

                df = self._dataframe(table)

                sheet = f"Table_{index}"

                df.to_excel(
                    writer,
                    sheet_name=sheet,
                    index=False,
                )

        return str(output)

    def to_csv(
        self,
        tables: list[dict[str, Any]],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.csv"

        df = self._dataframe(tables[0])

        df.to_csv(
            output,
            index=False,
            encoding="utf-8"
        )

        return str(output)

    def to_json(
        self,
        tables: list[dict[str, Any]],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.json"

        with open(output, "w", encoding="utf-8") as file:

            json.dump(
                tables,
                file,
                indent=4,
                ensure_ascii=False,
            )

        return str(output)

    def to_markdown(
        self,
        tables: list[dict[str, Any]],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.md"

        with open(output, "w", encoding="utf-8") as file:

            for index, table in enumerate(tables, start=1):

                df = self._dataframe(table)

                file.write(f"# Table {index}\n\n")

                file.write(df.to_markdown(index=False))

                file.write("\n\n")

        return str(output)

    def to_html(
        self,
        tables: list[dict[str, Any]],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.html"

        with open(output, "w", encoding="utf-8") as file:

            file.write("<html><body>\n")

            for index, table in enumerate(tables, start=1):

                df = self._dataframe(table)

                file.write(f"<h2>Table {index}</h2>")

                file.write(
                    df.to_html(index=False)
                )

                file.write("<br><br>")

            file.write("</body></html>")

        return str(output)

    def export(
        self,
        tables: list[dict[str, Any]],
        filename: str,
        output_format: str,
    ) -> str:
        """
        Export table(s) in the requested format.
        """

        output_format = output_format.lower()

        if output_format == "excel":
            return self.to_excel(tables, filename)

        if output_format == "csv":
            return self.to_csv(tables, filename)

        if output_format == "json":
            return self.to_json(tables, filename)

        if output_format == "markdown":
            return self.to_markdown(tables, filename)

        if output_format == "html":
            return self.to_html(tables, filename)

        raise ValueError(
            f"Unsupported format: {output_format}"
        )