"""Pembuat laporan PDF mingguan untuk ChainScope ID.

Catatan: fpdf2 dengan font default (Helvetica) hanya mendukung Latin-1.
Karakter non-Latin-1 (mis. em-dash, tanda ≈) akan dikonversi otomatis.
"""

from datetime import datetime, timezone

import pandas as pd
from fpdf import FPDF


# ---------------------------------------------------------------------------
# Helper format (ASCII-safe untuk PDF)
# ---------------------------------------------------------------------------

_UNICODE_REPLACEMENTS = {
    "\u2014": "-",    # em dash
    "\u2013": "-",    # en dash
    "\u2248": "~",    # approx
    "\u2192": "->",   # right arrow
    "\u2190": "<-",   # left arrow
    "\u2022": "-",    # bullet
    "\u00b7": ".",    # middle dot
}


def _safe(text) -> str:
    """Konversi ke string Latin-1 yang aman untuk fpdf2."""
    s = str(text)
    for bad, good in _UNICODE_REPLACEMENTS.items():
        s = s.replace(bad, good)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _money(value, currency: str) -> str:
    """Format ringkas nilai uang (ASCII-safe)."""
    if value is None or pd.isna(value):
        return "-"
    v = float(value)
    if currency.upper() == "IDR":
        if abs(v) >= 1_000_000_000_000:
            return f"Rp{v / 1_000_000_000_000:.2f} T"
        if abs(v) >= 1_000_000_000:
            return f"Rp{v / 1_000_000_000:.2f} M"
        if abs(v) >= 1_000_000:
            return f"Rp{v / 1_000_000:.2f} jt"
        return f"Rp{v:,.0f}".replace(",", ".")
    abs_v = abs(v)
    if abs_v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f} B"
    if abs_v >= 1_000_000:
        return f"${v / 1_000_000:.2f} M"
    return f"${v:,.2f}"


def _percent(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):+.2f}%"


# ---------------------------------------------------------------------------
# Kelas PDF
# ---------------------------------------------------------------------------

class ChainScopeReport(FPDF):
    """Subclass FPDF dengan header & footer kustom."""

    def __init__(self, report_title: str = "ChainScope ID - Laporan Mingguan"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.report_title = report_title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, _safe(self.report_title), new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 9)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.cell(0, 5, f"Digenerate: {ts}", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Halaman {self.page_no()}", align="C")


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_weekly_report(
    market_df: pd.DataFrame,
    currency: str,
    data_source: str,
    top_n: int = 10,
) -> bytes:
    """Bangun PDF laporan mingguan, kembalikan bytes."""
    pdf = ChainScopeReport()
    pdf.add_page()

    # --- Info umum ---
    src_label = "Data live CoinGecko" if data_source == "LIVE" else "Data DEMO (contoh)"
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        _safe(
            f"Sumber data   : {src_label}\n"
            f"Mata uang     : {currency}\n"
            f"Koin dianalisis: {len(market_df)}"
        ),
    )
    pdf.ln(4)

    # --- Ringkasan 3 teratas ---
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Ringkasan Koin Teratas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for _, row in market_df.head(3).iterrows():
        name = row.get("name", "-")
        sym = str(row.get("symbol", "")).upper()
        price = _money(row.get("current_price"), currency)
        chg = _percent(row.get("price_change_percentage_24h"))
        pdf.cell(
            0, 6,
            _safe(f"- {name} ({sym}): {price}  ({chg} 24 jam)"),
            new_x="LMARGIN", new_y="NEXT",
        )
    pdf.ln(4)

    # --- Tabel Top N ---
    effective_n = min(top_n, len(market_df))
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(
        0, 8,
        _safe(f"Tabel Top {effective_n} Koin"),
        new_x="LMARGIN", new_y="NEXT",
    )

    if effective_n == 0:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, "Tidak ada data koin yang tersedia.",
                 new_x="LMARGIN", new_y="NEXT")
    else:
        col_widths = [70, 20, 55, 30]
        headers = ["Nama", "Simbol", f"Harga ({currency})", "Perub 24j"]

        pdf.set_font("Helvetica", "B", 9)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, _safe(h), border=1, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for _, row in market_df.head(effective_n).iterrows():
            name = _safe(str(row.get("name", "-")))[:38]
            sym = _safe(str(row.get("symbol", "")).upper())[:8]
            price = _money(row.get("current_price"), currency)
            chg = _percent(row.get("price_change_percentage_24h"))
            for w, val in zip(col_widths, [name, sym, price, chg]):
                pdf.cell(w, 7, val, border=1)
            pdf.ln()

    pdf.ln(6)

    # --- Disclaimer ---
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0, 5,
        _safe(
            "Disclaimer: Laporan ini hanya menyajikan data pasar publik. "
            "Bukan saran investasi dan tidak menjamin keuntungan. "
            "Selalu lakukan riset mandiri sebelum mengambil keputusan."
        ),
    )

    return bytes(pdf.output())