## Fitur saat ini

- Dashboard pasar crypto dengan data CoinGecko, pencarian, grafik, ringkasan
  market cap/volume, dan gainers/losers.
- Analisis teknikal dengan candlestick, MA20/MA50, Bollinger Bands, RSI,
  volume, dan beberapa timeframe.
- Trading Journal Supabase dengan transaksi manual, import CSV, dan tag strategi.
- Portfolio aktif yang dihitung dari transaksi jurnal, ditambah alokasi dan P/L
  terbuka per strategi.
- Performance Coach yang menghitung hasil historis dari transaksi jurnal.
- Risk Center untuk eksposur FIFO, konsentrasi, kalkulator position sizing,
  volatilitas dan korelasi historis.
- AI Research untuk data pasar crypto, indikator historis, headline, perbandingan
  aset, dan laporan. Interpretasi Gemini opsional; data jurnal/portofolio tidak
  dikirim ke model.
- Perbandingan aset, watchlist, converter, berita crypto, laporan PDF, dan
  Personal Wallet lokal (storage terpisah per akun di browser, tidak disinkronkan
  ke cloud).
- CSV download untuk jurnal, hasil portofolio terealisasi, dan watchlist.
- Tema terang/gelap serta autentikasi Supabase.

Alert terjadwal dijalankan melalui GitHub Actions setiap 15 menit. Konfigurasikan
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, dan `TELEGRAM_BOT_TOKEN` sebagai
GitHub Actions secrets; `COINGECKO_API_KEY` bersifat opsional. Jangan commit
secret ke repository. Untuk tombol pesan uji di aplikasi, `TELEGRAM_BOT_TOKEN`
juga perlu tersedia sebagai Streamlit server secret. Pengguna mengatur Telegram
chat ID dari halaman Price Alerts.

Fitur research dan market saat ini berfokus pada crypto; saham/forex dan
fundamental berbasis laporan keuangan belum terhubung. Batasan, migrasi yang
masih memerlukan persetujuan, serta hasil verifikasi dirangkum dalam
[Feature Gap Report](./FEATURE_GAP_REPORT.md) dan
[Development Progress](./DEVELOPMENT_PROGRESS.md).