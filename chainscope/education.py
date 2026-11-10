"""Beginner-friendly financial intelligence and wealth management education modules."""

FINANCIAL_CONCEPTS = [
    {
        "id": "net_worth",
        "title": "Apa itu Kekayaan Bersih (Net Worth)?",
        "summary": "Kekayaan Bersih = Total Seluruh Aset − Total Seluruh Kewajiban (Utang).",
        "explanation": (
            "Kekayaan bersih adalah indikator kesehatan finansial sejati Anda. "
            "Banyak orang merasa kaya karena memiliki mobil atau saldo bank yang besar, "
            "tetapi jika aset tersebut dibeli dari utang yang belum lunas, kekayaan bersihnya bisa jadi kecil atau bahkan minus. "
            "Fokus utama dalam membangun kekayaan adalah menumbuhkan selisih positif antara aset produktif dan utang."
        ),
        "formula": "Kekayaan Bersih = (Kas + Tabungan + Saham + Crypto + Properti) − (KPR + Kartu Kredit + Pinjaman)",
        "action_tip": "Tinjau kekayaan bersih Anda setiap awal bulan untuk memastikan kurvanya konsisten naik dari tahun ke tahun.",
    },
    {
        "id": "cash_flow",
        "title": "Arus Kas (Cash Flow) & Savings Rate",
        "summary": "Arus Kas Bersih = Total Pemasukan Bulanan − Total Pengeluaran Bulanan.",
        "explanation": (
            "Arus kas adalah urat nadi keuangan Anda. Sebesar apapun penghasilan Anda, "
            "jika pengeluaran selalu setara atau lebih besar dari pemasukan (arus kas negatif), "
            "Anda tidak akan pernah memiliki modal untuk berinvestasi. "
            "Idealnya, sisihkan minimal 20% dari total pemasukan bersih sebagai tabungan/investasi (Savings Rate)."
        ),
        "formula": "Savings Rate (%) = ((Pemasukan − Pengeluaran) / Pemasukan) × 100%",
        "action_tip": "Prioritaskan menabung di awal (pay yourself first) segera setelah menerima gaji, bukan menabung dari sisa uang di akhir bulan.",
    },
    {
        "id": "emergency_fund",
        "title": "Dana Darurat (Emergency Fund)",
        "summary": "Penyangga likuid senilai 3 hingga 6 bulan pengeluaran bulanan rutin.",
        "explanation": (
            "Dana darurat adalah benteng pertahanan sebelum Anda mulai berinvestasi di aset berisiko seperti saham atau crypto. "
            "Tujuannya adalah mengamankan kebutuhan hidup jika terjadi musibah seperti kehilangan pekerjaan, sakit, atau renovasi darurat, "
            "sehingga Anda tidak perlu menjual aset investasi Anda saat pasar sedang jatuh (crash)."
        ),
        "formula": "Target Dana Darurat = Pengeluaran Bulanan × (3 sampai 6)",
        "action_tip": "Simpan dana darurat di instrumen yang aman dan likuid (reksa dana pasar uang, tabungan bank terpisah, atau deposito fleksibel).",
    },
    {
        "id": "asset_allocation",
        "title": "Alokasi Aset & Diversifikasi",
        "summary": "Menyebarkan modal ke berbagai kelas aset agar tidak rentan terhadap kejatuhan satu instrumen.",
        "explanation": (
            "Prinsip 'don't put all your eggs in one basket'. Membagi kekayaan ke dalam: "
            "1. Aset Likuid & Aman (Kas, Deposito, Pasar Uang)\n"
            "2. Aset Bertumbuh (Saham, Indeks IDX/S&P500)\n"
            "3. Aset Berisiko Tinggi & Peluang Tinggi (Crypto, Web3 Tokens)\n"
            "4. Aset Riil (Emas, Properti)\n"
            "Komposisi disesuaikan dengan usia dan profil toleransi risiko Anda."
        ),
        "formula": "Total Portofolio = Kas (10-20%) + Saham (40-60%) + Crypto (5-15%) + Emas/Lainnya (10-20%)",
        "action_tip": "Lakukan rebalancing setiap 6 atau 12 bulan jika proporsi salah satu aset melonjak terlalu dominan.",
    },
    {
        "id": "debt_management",
        "title": "Memahami Utang: Produktif vs Konsumtif",
        "summary": "Utang produktif menghasilkan nilai tambah; utang konsumtif membebani masa depan Anda.",
        "explanation": (
            "Utang produktif digunakan untuk membeli aset yang nilainya bertambah atau menghasilkan arus kas (misal: modal bisnis atau KPR rumah pertama). "
            "Utang konsumtif digunakan untuk membeli barang yang nilainya langsung terdepresiasi (misal: cicilan gadget mewah, paylater liburan, atau baju bermerek). "
            "Pastikan total cicilan bulanan Anda tidak melebihi 30% dari penghasilan bersih bulanan."
        ),
        "formula": "Debt-to-Income Ratio = (Total Cicilan Bulanan / Total Pemasukan Bulanan) × 100% (Maksimal 30%)",
        "action_tip": "Segera lunasi utang berbunga tinggi (kartu kredit, paylater) sebelum memulai investasi agresif.",
    },
]


def get_all_educational_topics() -> list[dict]:
    """Return all structured beginner-friendly financial education modules."""
    return FINANCIAL_CONCEPTS


def get_topic_by_id(topic_id: str) -> dict | None:
    """Retrieve specific educational module details."""
    return next((t for t in FINANCIAL_CONCEPTS if t["id"] == topic_id), None)
