import csv
from io import StringIO

import math

from chainscope.exports import build_csv


def test_build_csv_includes_requested_columns_and_preserves_numbers():
    exported = build_csv(
        [{"coin_id": "bitcoin", "amount": 1.25, "ignored": "private"}],
        ["coin_id", "amount"],
    )
    rows = list(csv.DictReader(StringIO(exported.decode("utf-8-sig"))))

    assert rows == [{"coin_id": "bitcoin", "amount": "1.25"}]


def test_build_csv_neutralizes_spreadsheet_formula_strings():
    exported = build_csv(
        [{"strategy_tag": " =HYPERLINK(\"https://invalid\")"}],
        ["strategy_tag"],
    )

    assert "' =HYPERLINK" in exported.decode("utf-8-sig")


def test_build_csv_leaves_missing_market_values_blank():
    exported = build_csv([{"price": math.nan}], ["price"])

    assert list(csv.DictReader(StringIO(exported.decode("utf-8-sig")))) == [
        {"price": ""}
    ]
