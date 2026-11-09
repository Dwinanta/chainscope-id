"""Safe CSV exports for user-visible ChainScope data."""

import csv
import math
from numbers import Real
from io import StringIO
from collections.abc import Iterable, Mapping


def _spreadsheet_safe(value: object) -> object:
    if isinstance(value, Real) and not math.isfinite(float(value)):
        return ""
    if not isinstance(value, str):
        return value
    if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def build_csv(rows: Iterable[Mapping], columns: list[str]) -> bytes:
    """Serialize selected columns with UTF-8 BOM and formula-safe text fields."""
    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=columns,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: _spreadsheet_safe(row.get(column, ""))
            for column in columns
        })
    return buffer.getvalue().encode("utf-8-sig")
