"""
Table Formatter

Converts extracted table data into various export formats.
"""

from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import table

from app.services.table_extractor.parser import ParsedTable

from app.services.table_extractor.parser import ParsedTable


class TableFormatter:
    """
    Converts canonical table structures into
    Excel, CSV, JSON, Markdown and HTML.
    """

    def __init__(self, output_directory: str | Path = "temp/table_extractor"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def _dataframe(self, table: ParsedTable) -> pd.DataFrame:

        data = asdict(table)

        headers = data["headers"]

        rows = [
            [cell.text for cell in row.cells]
            for row in data["rows"]
        ]

        return pd.DataFrame(rows, columns=headers)

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
        tables: list[ParsedTable],
        filename: str,
    ) -> str:

        output = self.output_directory / f"{filename}.json"

        serializable = [asdict(table) for table in tables]

        with open(output, "w", encoding="utf-8") as file:
            json.dump(
                serializable,
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