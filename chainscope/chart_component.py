"""Full-screen Chart.js market chart with live Binance updates."""

import json
import re

import streamlit as st

from chainscope import ui


def render_modern_chart(
    symbol: str = "BTCUSDT",
    height: int = 600,
    coins: list[dict[str, str]] | None = None,
    selected_coin_id: str | None = None,
    allow_coin_selection: bool = True,
    is_dark_mode: bool = False,
) -> None:
    """Render a market chart with indicators, a live price line, and countdown."""
    base_asset = re.sub(r"(USDT|IDR)$", "", symbol.strip().upper())
    if not re.fullmatch(r"[A-Z0-9]{2,20}", base_asset):
        raise ValueError("Simbol koin tidak valid.")
    if height <= 0:
        raise ValueError("Tinggi chart harus lebih besar dari nol.")

    coin_options = []
    for coin in coins or []:
        coin_id = coin.get("id")
        coin_symbol = coin.get("symbol")
        coin_name = coin.get("name")
        if not all(isinstance(value, str) and value.strip()
                   for value in (coin_id, coin_symbol, coin_name)):
            continue
        image = coin.get("image", "")
        coin_options.append({
            "id": coin_id.strip(),
            "symbol": coin_symbol.strip().upper(),
            "name": coin_name.strip(),
            "image": image.strip() if isinstance(image, str) else "",
        })
    if not coin_options:
        coin_options = [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "image": ""},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "image": ""},
            {"id": "solana", "symbol": "SOL", "name": "Solana", "image": ""},
            {"id": "binancecoin", "symbol": "BNB", "name": "BNB", "image": ""},
            {"id": "ripple", "symbol": "XRP", "name": "XRP", "image": ""},
            {"id": "cardano", "symbol": "ADA", "name": "Cardano", "image": ""},
            {"id": "dogecoin", "symbol": "DOGE", "name": "Dogecoin", "image": ""},
        ]
    initial_coin_id = selected_coin_id or ""
    coin_options_json = json.dumps(coin_options, ensure_ascii=True).replace("</", "<\\/")
    initial_coin_id_json = json.dumps(initial_coin_id, ensure_ascii=True).replace("</", "<\\/")

    html_code = """
    <!doctype html>
    <html lang="id">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="https://cdn.jsdelivr.net/npm/chart.js@latest/dist/chart.umd.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial@0.2.1/dist/chartjs-chart-financial.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@latest/dist/chartjs-plugin-zoom.min.js"></script>
      <style>
        * { box-sizing: border-box; }
        html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
        body { color: var(--cs-primary-text); background: var(--cs-main-background); font: 13px Arial, sans-serif; }
        .terminal { display: flex; flex-direction: column; width: 100%;
          height: 100vh; height: 100dvh; min-height: 0; padding: 4px 8px;
          background: var(--cs-main-background); overflow: hidden; }
        .toolbar { flex: 0 0 auto; display: flex; min-width: 0; }
        .toolbar-row { display: flex; align-items: center; justify-content: space-between;
          gap: 8px; width: 100%; min-width: 0; min-height: 32px; white-space: nowrap; }
        .asset-line, .controls {
          display: flex; align-items: center; min-width: 0; flex-wrap: nowrap; }
        .asset-line { flex: 0 1 auto; gap: 8px; white-space: nowrap; }
        .pair-button { display: inline-flex; align-items: center; gap: 7px;
          min-height: 27px; padding: 3px 7px; border: 1px solid var(--cs-border);
          border-radius: 8px; color: var(--cs-primary-text); background: var(--cs-input-background);
          font-size: 11px; font-weight: 600; white-space: nowrap; }
        .pair-button:hover { color: var(--cs-primary-text); background: var(--cs-main-background); }
        .pair-chevron { width: 13px; height: 13px; color: var(--cs-secondary-text); }
        .price { color: var(--cs-secondary-text); font-size: 10px; white-space: nowrap; }
        .price strong { color: var(--cs-primary-text); font-size: 12px; }
        .change { margin-left: 4px; color: var(--cs-positive-text); }
        .change.negative { color: var(--cs-negative-text); }
        .controls { flex: 1 1 auto; justify-content: flex-end; gap: 8px;
          flex-wrap: wrap; overflow: visible; }
        .source-dot { width: 7px; height: 7px; flex: 0 0 7px;
          border-radius: 50%; background: var(--cs-positive); box-shadow: 0 0 0 2px rgba(22,163,74,.12); }
        .source-dot.indodax { background: var(--cs-negative); box-shadow: 0 0 0 2px rgba(220,38,38,.12); }
        .source-dot.coingecko { background: var(--cs-accent); box-shadow: 0 0 0 2px rgba(124,58,237,.12); }
        .group { display: flex; align-items: center; flex: 0 1 auto; flex-wrap: wrap; gap: 1px;
          min-width: 0; padding: 1px; border-radius: 5px; background: transparent; }
        button { min-height: 21px; padding: 3px 5px; border: 0; border-radius: 4px;
          color: var(--cs-secondary-text); background: transparent; cursor: pointer; font: inherit; }
        button:hover { color: var(--cs-accent); }
        button.active { color: #fff; background: var(--cs-accent); }
        .reset { display: inline-flex; flex: 0 0 auto; align-items: center;
          justify-content: center; width: 24px; min-width: 24px; padding: 2px;
          border: 0; background: transparent; }
        .indicator-dropdown { position: relative; flex: 0 0 auto; }
        .indicator-trigger { display: inline-flex; align-items: center; gap: 5px;
          min-height: 23px; padding: 3px 6px; border: 0;
          border-radius: 5px; color: var(--cs-secondary-text); background: transparent; font-size: 10px; }
        .indicator-trigger:hover { background: var(--cs-main-background); }
        .indicator-trigger svg { width: 12px; height: 12px; }
        .indicator-menu { position: absolute; z-index: 15; left: 0; top: calc(100% + 5px);
          display: none; min-width: 140px; padding: 6px;
          border: 1px solid var(--cs-border); border-radius: 8px; background: var(--cs-input-background);
          box-shadow: 0 8px 24px rgba(31,41,55,.14); }
        .indicator-menu.open { display: flex; flex-direction: column; gap: 2px; }
        .indicator-menu label { display: flex; align-items: center; gap: 7px;
          min-height: 25px; padding: 3px 6px; border-radius: 5px;
          color: var(--cs-primary-text); font-size: 10px; cursor: pointer; }
        .indicator-menu label:hover { background: var(--cs-main-background); }
        input { margin: 0; accent-color: var(--cs-accent); }
        .charts { display: flex; flex: 1 1 0; flex-direction: column;
          width: 100%; max-width: 100%; min-height: 0; overflow: hidden; padding-top: 3px; }
        .main-panel { position: relative; flex: 7 1 0; width: 100%;
          max-width: 100%; min-height: 0; }
        .indicator-panel { position: relative; flex: 3 1 0; width: 100%;
          max-width: 100%; min-height: 0;
          border-top: 1px solid var(--cs-border); padding-top: 4px; }
        canvas { display: block; width: 100% !important; max-width: 100%;
          height: 100% !important; }
        .panel-label { position: absolute; z-index: 1; top: 5px; left: 7px;
          color: var(--cs-secondary-text); font-size: 10px; pointer-events: none; }
        .panel-select { position: absolute; z-index: 2; top: 4px; right: 4px;
          padding: 3px 6px; border: 1px solid var(--cs-border); border-radius: 4px;
          color: var(--cs-primary-text); background: var(--cs-input-background); font: inherit; font-size: 11px; }
        __THEME_STYLE__
        .candle-timer { flex: 0 0 auto; min-width: 34px; padding: 2px 3px;
          border: 0; color: var(--cs-secondary-text); background: transparent;
          font: 10px ui-monospace, Consolas, monospace; pointer-events: none; }
        .coin-modal { position: fixed; z-index: 20; inset: 0; display: none;
          align-items: center; justify-content: center; padding: 16px;
          background: rgba(25,20,40,.38); }
        .coin-modal.open { display: flex; }
        .modal-card { display: flex; flex-direction: column; width: min(390px, 100%);
          max-height: min(480px, 80vh); overflow: hidden; border: 1px solid var(--cs-border);
          border-radius: 16px; background: var(--cs-content-background); box-shadow: 0 16px 48px rgba(15,23,42,.14); }
        .modal-head { display: flex; align-items: center; justify-content: space-between;
          padding: 14px 16px 10px; color: var(--cs-primary-text); font-size: 14px; font-weight: 600; }
        .modal-close { width: 26px; min-height: 26px; padding: 0; color: var(--cs-secondary-text);
          font-size: 18px; }
        .coin-search-wrap { position: relative; margin: 0 14px 10px; }
        .search-icon { position: absolute; top: 50%; left: 10px; width: 15px; height: 15px;
          color: var(--cs-secondary-text); transform: translateY(-50%); pointer-events: none; }
        .coin-search { width: 100%; margin: 0; padding: 9px 10px 9px 33px;
          border: 1px solid var(--cs-border); border-radius: 8px; outline: none;
          color: var(--cs-primary-text); background: var(--cs-input-background); font: inherit; font-size: 12px; }
        .coin-search:focus { border-color: var(--cs-accent); }
        .coin-list { overflow-y: auto; padding: 0 8px 8px; }
        .coin-option { display: flex; align-items: center; width: 100%; gap: 9px;
          padding: 9px 10px; border-radius: 8px; text-align: left; }
        .coin-option:hover { color: var(--cs-primary-text); background: var(--cs-main-background); }
        .coin-logo { width: 24px; height: 24px; flex: 0 0 24px;
          border-radius: 50%; object-fit: contain; background: var(--cs-border); }
        .coin-name { display: flex; flex-direction: column; gap: 2px; }
        .coin-name strong { color: var(--cs-primary-text); font-size: 12px; font-weight: 600; }
        .coin-name span { color: var(--cs-secondary-text); font-size: 11px; }
        .empty-results { padding: 18px 10px; color: var(--cs-secondary-text); text-align: center;
          font-size: 12px; }
        .error { display: none; flex: 0 0 auto; padding: 5px 8px; color: var(--cs-negative);
          background: var(--cs-content-background); font-size: 11px; }
        @media (max-width: 620px) {
          .terminal { padding: 3px 4px; }
          .toolbar-row { flex-wrap: wrap; gap: 4px; min-height: 28px; }
          .asset-line { flex: 1 1 100%; gap: 2px; }
          .source-dot { width: 6px; height: 6px; flex-basis: 6px; }
          .pair-button { flex: 0 0 auto; min-height: 23px; gap: 3px; padding: 2px 4px; font-size: 8px; }
          .pair-chevron { width: 10px; height: 10px; }
          .price { display: flex; flex: 0 1 auto; align-items: center; gap: 2px;
            max-width: 70px; min-width: 0; overflow: hidden; font-size: 8px; }
          .price strong { max-width: 42px; min-width: 0; overflow: hidden;
            font-size: 9px; text-overflow: ellipsis; }
          .change { flex: 0 0 auto; margin-left: 0; font-size: 8px; }
          .controls { flex: 1 1 100%; width: 100%; gap: 4px;
            justify-content: flex-start; }
          .indicator-dropdown { flex: 0 0 auto; }
          .indicator-trigger { min-height: 19px; gap: 1px; padding: 2px; font-size: 7px; }
          .indicator-trigger svg { width: 9px; height: 9px; }
          .group { gap: 0; }
          #typeGroup { flex: 0 1 auto; }
          #timeframeGroup { flex: 1 1 auto; justify-content: flex-start; }
          #typeGroup button, #timeframeGroup button {
            min-width: 0; padding: 2px 2px; font-size: 7px; }
          .candle-timer { min-width: 27px; padding: 1px; font-size: 8px; }
          .reset { width: 18px; min-width: 18px; padding: 1px; }
          .reset svg { width: 11px; height: 11px; }
        }
        @media (max-width: 380px) {
          .toolbar-row { gap: 2px; }
          .asset-line { gap: 1px; }
          .pair-button { gap: 2px; padding: 2px 3px; font-size: 7px; }
          .price { max-width: 56px; gap: 1px; font-size: 7px; }
          .price strong { max-width: 34px; font-size: 8px; }
          .change { font-size: 7px; }
          .controls { gap: 1px; }
          .indicator-trigger { font-size: 6px; }
          #typeGroup button, #timeframeGroup button { padding: 2px 1px; font-size: 6px; }
          .candle-timer { min-width: 25px; font-size: 7px; }
          .reset { width: 16px; min-width: 16px; }
        }
      </style>
    </head>
    <body>
      <main class="terminal">
        <header class="toolbar">
          <div class="toolbar-row">
            <div class="asset-line">
              <span class="source-dot" id="sourceBadge" role="img"
                aria-label="Sumber harga Binance" title="Sumber harga Binance"></span>
              <button class="pair-button" id="pairButton" type="button"
                aria-haspopup="dialog" aria-controls="coinModal">
                <span id="pairLabel">__SYMBOL__/USDT</span>
                <svg class="pair-chevron" viewBox="0 0 16 16" fill="none"
                  aria-hidden="true">
                  <path d="m4 6 4 4 4-4" stroke="currentColor" stroke-width="1.5"
                    stroke-linecap="round" stroke-linejoin="round"></path>
                </svg>
              </button>
              <span class="price">
                <strong id="currentPrice">--</strong>
                <span class="change" id="priceChange">--</span>
              </span>
            </div>
            <div class="controls">
              <div class="indicator-dropdown">
                <button class="indicator-trigger" id="indicatorTrigger" type="button"
                  aria-expanded="false" aria-controls="indicatorMenu">
                  Indikator
                  <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <path d="m4 6 4 4 4-4" stroke="currentColor" stroke-width="1.5"
                      stroke-linecap="round" stroke-linejoin="round"></path>
                  </svg>
                </button>
                <div class="indicator-menu" id="indicatorMenu" aria-label="Indikator">
                  <label><input id="chkMA9" type="checkbox"> MA 9</label>
                  <label><input id="chkMA20" type="checkbox"> MA 20</label>
                  <label><input id="chkMA50" type="checkbox"> MA 50</label>
                  <label><input id="chkBB" type="checkbox"> Bollinger Bands</label>
                  <label><input id="chkRSI" type="checkbox" checked> RSI</label>
                  <label><input id="chkMFI" type="checkbox"> MFI</label>
                </div>
              </div>
              <div class="group" id="typeGroup" aria-label="Tipe chart">
                <button data-type="area" class="active">Area</button>
                <button data-type="line">Line</button>
                <button data-type="candlestick">Candle</button>
              </div>
              <div class="group" id="timeframeGroup" aria-label="Timeframe">
                <button data-tf="1m">1m</button>
                <button data-tf="5m">5m</button>
                <button data-tf="15m">15m</button>
                <button data-tf="1h" class="active">1h</button>
                <button data-tf="4h">4h</button>
                <button data-tf="1d">1d</button>
              </div>
              <span class="candle-timer" id="candleTimer" aria-live="off">--:--</span>
              <button class="reset" id="resetZoom" type="button" title="Reset zoom"
                aria-label="Reset zoom">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round"
                  stroke-linejoin="round" aria-hidden="true">
                  <path d="M3 12a9 9 0 1 0 2.64-6.36L3 8"></path>
                  <path d="M3 3v5h5"></path>
                </svg>
              </button>
            </div>
          </div>
        </header>
        <div class="error" id="errorMsg" role="status"></div>
        <section class="charts">
          <div class="main-panel">
            <canvas id="mainChart"></canvas>
          </div>
          <div class="indicator-panel">
            <span class="panel-label" id="panelLabel">RSI (14)</span>
            <select class="panel-select" id="panelMode" aria-label="Panel indikator">
              <option value="rsi">RSI</option>
              <option value="mfi">MFI</option>
              <option value="volume">Volume</option>
            </select>
            <canvas id="indicatorChart"></canvas>
          </div>
        </section>
      </main>
      <div class="coin-modal" id="coinModal" role="dialog" aria-modal="true"
        aria-labelledby="modalTitle">
        <section class="modal-card">
          <div class="modal-head">
            <span id="modalTitle">Pilih koin</span>
            <button class="modal-close" id="closeCoinModal" type="button"
              aria-label="Tutup">×</button>
          </div>
          <div class="coin-search-wrap">
            <svg class="search-icon" viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="8.8" cy="8.8" r="5.8" stroke="currentColor" stroke-width="1.5"></circle>
              <path d="m13.2 13.2 4 4" stroke="currentColor" stroke-width="1.5"
                stroke-linecap="round"></path>
            </svg>
            <input class="coin-search" id="coinSearch" type="search"
              placeholder="Cari simbol atau nama koin..." aria-label="Cari koin"
              autocomplete="off" spellcheck="false">
          </div>
          <div class="coin-list" id="coinList" role="listbox"></div>
        </section>
      </div>
      <script>
        "use strict";
        const IS_DARK_MODE = __IS_DARK_MODE__;
        const INITIAL_SYMBOL = "__SYMBOL__";
        const INITIAL_COIN_ID = __INITIAL_COIN_ID__;
        const coins = __COINS_JSON__;
        const state = {
          symbol: INITIAL_SYMBOL, type: "area", timeframe: "1h",
          source: "binance", mode: "rsi",
          mainChart: null, indicatorChart: null, candles: [], overlays: {},
          socket: null, reconnectTimer: null, countdownTimer: null,
          syncingPan: false, coinId: INITIAL_COIN_ID, loadRequestId: 0
        };
        const colors = __CHART_COLORS__;
        const frameSettings = {
          "1m": { binance: "1m", indodax: "1", seconds: 60 },
          "5m": { binance: "5m", indodax: "5", seconds: 300 },
          "15m": { binance: "15m", indodax: "15", seconds: 900 },
          "1h": { binance: "1h", indodax: "60", seconds: 3600 },
          "4h": { binance: "4h", indodax: "240", seconds: 14400 },
          "1d": { binance: "1d", indodax: "D", seconds: 86400 }
        };
        const mainCanvas = document.getElementById("mainChart");
        const indicatorCanvas = document.getElementById("indicatorChart");
        const sourceBadge = document.getElementById("sourceBadge");
        const errorEl = document.getElementById("errorMsg");
        const indicatorInputs = {
          ma9: document.getElementById("chkMA9"),
          ma20: document.getElementById("chkMA20"),
          ma50: document.getElementById("chkMA50"),
          bb: document.getElementById("chkBB"),
          rsi: document.getElementById("chkRSI"),
          mfi: document.getElementById("chkMFI")
        };
        const coinModal = document.getElementById("coinModal");
        const coinSearch = document.getElementById("coinSearch");
        const coinList = document.getElementById("coinList");
        const indicatorMenu = document.getElementById("indicatorMenu");
        const indicatorTrigger = document.getElementById("indicatorTrigger");
        const logoRequests = new Map();
        let logoObserver = null;

        function setSourceStatus(source) {
          const usingIndodax = source === "indodax";
          sourceBadge.classList.toggle("indodax", usingIndodax);
          sourceBadge.classList.toggle("coingecko", source === "coingecko");
          const label = usingIndodax ? "Sumber harga Indodax"
            : source === "coingecko" ? "Sumber harga CoinGecko"
            : "Sumber harga Binance";
          sourceBadge.setAttribute("aria-label", label);
          sourceBadge.title = label;
        }

        indicatorTrigger.addEventListener("click", () => {
          const isOpen = indicatorMenu.classList.toggle("open");
          indicatorTrigger.setAttribute("aria-expanded", String(isOpen));
        });
        document.addEventListener("click", (event) => {
          if (event.target.closest(".indicator-dropdown")) return;
          indicatorMenu.classList.remove("open");
          indicatorTrigger.setAttribute("aria-expanded", "false");
        });
        document.addEventListener("keydown", (event) => {
          if (event.key !== "Escape") return;
          indicatorMenu.classList.remove("open");
          indicatorTrigger.setAttribute("aria-expanded", "false");
        });

        async function hydrateCoinLogo(coin, image) {
          if (coin.image || !coin.id) return;
          if (!logoRequests.has(coin.id)) {
            const request = fetch(
              "https://api.coingecko.com/api/v3/coins/" + encodeURIComponent(coin.id)
              + "?localization=false&tickers=false&market_data=false&community_data=false"
              + "&developer_data=false&sparkline=false"
            ).then((response) => {
              if (!response.ok) throw new Error("CoinGecko HTTP " + response.status);
              return response.json();
            }).then((details) => details.image && (details.image.small || details.image.thumb));
            logoRequests.set(coin.id, request);
          }
          try {
            const imageUrl = await logoRequests.get(coin.id);
            if (imageUrl && image.isConnected) {
              image.src = imageUrl;
              image.hidden = false;
            } else if (image.isConnected) {
              image.hidden = true;
            }
          } catch (error) {
            console.warn("Logo CoinGecko tidak tersedia untuk " + coin.id + ":", error);
            if (image.isConnected) image.hidden = true;
          }
        }

        if ("IntersectionObserver" in window) {
          logoObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
              if (!entry.isIntersecting) return;
              logoObserver.unobserve(entry.target);
              hydrateCoinLogo(
                coins.find((coin) => coin.id === entry.target.dataset.coinId),
                entry.target
              );
            });
          }, { root: coinList, rootMargin: "80px" });
        }

        function renderCoinList(query = "") {
          const normalizedQuery = query.trim().toLowerCase();
          const matches = coins.filter((coin) =>
            coin.symbol.toLowerCase().includes(normalizedQuery)
            || coin.name.toLowerCase().includes(normalizedQuery)
          );
          coinList.replaceChildren();
          if (!matches.length) {
            const empty = document.createElement("div");
            empty.className = "empty-results";
            empty.textContent = "Koin tidak ditemukan";
            coinList.appendChild(empty);
            return;
          }
          const visibleCoins = matches.slice(0, 100);
          visibleCoins.forEach((coin) => {
            const option = document.createElement("button");
            option.type = "button";
            option.className = "coin-option";
            option.setAttribute("role", "option");
            option.setAttribute("aria-selected", String(coin.symbol === state.symbol));
            const name = document.createElement("span");
            name.className = "coin-name";
            const image = document.createElement("img");
            image.className = "coin-logo";
            image.width = 24;
            image.height = 24;
            image.alt = "";
            image.loading = "lazy";
            image.hidden = false;
            image.dataset.coinId = coin.id;
            image.addEventListener("error", () => { image.hidden = true; });
            if (coin.image) image.src = coin.image;
            const symbol = document.createElement("strong");
            symbol.textContent = coin.symbol;
            const fullName = document.createElement("span");
            fullName.textContent = coin.name;
            name.append(symbol, fullName);
            option.append(image, name);
            option.addEventListener("click", () => selectCoin(coin));
            coinList.appendChild(option);
            if (!coin.image && logoObserver) logoObserver.observe(image);
          });
          if (matches.length > visibleCoins.length) {
            const more = document.createElement("div");
            more.className = "empty-results";
            more.textContent = "Menampilkan 100 dari " + matches.length
              + " koin. Persempit pencarian untuk hasil lainnya.";
            coinList.appendChild(more);
          }
        }

        function closeCoinModal() {
          coinModal.classList.remove("open");
          document.getElementById("pairButton").focus();
        }

        function selectCoin(coin) {
          closeCoinModal();
          if (coin.symbol === state.symbol && coin.id === state.coinId) return;
          state.coinId = coin.id;
          state.symbol = coin.symbol;
          document.getElementById("pairLabel").textContent = coin.symbol + "/"
            + (state.source === "indodax" ? "IDR"
              : state.source === "coingecko" ? "USD" : "USDT");
          loadData();
        }

        const livePriceLine = {
          id: "livePriceLine",
          afterDatasetsDraw(chart) {
            const last = state.candles[state.candles.length - 1];
            const area = chart.chartArea;
            const scale = chart.scales.y;
            if (!last || !area || !scale) return;
            const y = scale.getPixelForValue(last.c);
            if (!Number.isFinite(y) || y < area.top || y > area.bottom) return;
            const color = last.c >= last.o ? colors.priceUp : colors.priceDown;
            const { ctx } = chart;
            const label = priceFormat(last.c);
            const boxWidth = 86;
            const boxHeight = 19;
            const boxX = Math.min(area.right + 3, chart.width - boxWidth - 1);
            const boxY = Math.max(area.top, Math.min(area.bottom - boxHeight, y - boxHeight / 2));
            ctx.save();
            ctx.beginPath();
            ctx.setLineDash([5, 4]);
            ctx.strokeStyle = color;
            ctx.lineWidth = 1;
            ctx.moveTo(area.left, y);
            ctx.lineTo(area.right + 3, y);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.fillStyle = color;
            ctx.fillRect(boxX, boxY, boxWidth, boxHeight);
            ctx.fillStyle = "#fff";
            ctx.font = "10px Arial, sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(label, boxX + boxWidth / 2, boxY + boxHeight / 2, boxWidth - 6);
            ctx.restore();
          }
        };

        function priceFormat(value) {
          const currency = state.source === "indodax" ? "IDR" : "USD";
          return new Intl.NumberFormat("id-ID", {
            style: "currency", currency,
            maximumFractionDigits: currency === "USD" ? 4 : 0
          }).format(value);
        }

        function movingAverage(values, period) {
          const output = values.map(() => null);
          let sum = 0;
          for (let i = 0; i < values.length; i += 1) {
            sum += values[i];
            if (i >= period) sum -= values[i - period];
            if (i >= period - 1) output[i] = sum / period;
          }
          return output;
        }

        function bollingerBands(values, period = 20, deviations = 2) {
          const middle = movingAverage(values, period);
          const upper = values.map(() => null);
          const lower = values.map(() => null);
          for (let i = period - 1; i < values.length; i += 1) {
            let variance = 0;
            for (let j = i - period + 1; j <= i; j += 1) {
              variance += (values[j] - middle[i]) ** 2;
            }
            const deviation = Math.sqrt(variance / period);
            upper[i] = middle[i] + deviations * deviation;
            lower[i] = middle[i] - deviations * deviation;
          }
          return { middle, upper, lower };
        }

        function relativeStrengthIndex(values, period = 14) {
          const output = values.map(() => null);
          if (values.length <= period) return output;
          let gain = 0;
          let loss = 0;
          for (let i = 1; i <= period; i += 1) {
            const change = values[i] - values[i - 1];
            gain += Math.max(change, 0);
            loss += Math.max(-change, 0);
          }
          let averageGain = gain / period;
          let averageLoss = loss / period;
          output[period] = averageLoss === 0 ? 100
            : 100 - 100 / (1 + averageGain / averageLoss);
          for (let i = period + 1; i < values.length; i += 1) {
            const change = values[i] - values[i - 1];
            averageGain = (averageGain * (period - 1) + Math.max(change, 0)) / period;
            averageLoss = (averageLoss * (period - 1) + Math.max(-change, 0)) / period;
            output[i] = averageLoss === 0 ? 100
              : 100 - 100 / (1 + averageGain / averageLoss);
          }
          return output;
        }

        function moneyFlowIndex(candles, period = 14) {
          const output = candles.map(() => null);
          if (candles.length <= period) return output;
          const positive = candles.map(() => 0);
          const negative = candles.map(() => 0);
          for (let i = 1; i < candles.length; i += 1) {
            const typical = (candles[i].h + candles[i].l + candles[i].c) / 3;
            const prior = (candles[i - 1].h + candles[i - 1].l + candles[i - 1].c) / 3;
            const flow = typical * candles[i].v;
            if (typical > prior) positive[i] = flow;
            else if (typical < prior) negative[i] = flow;
          }
          for (let i = period; i < candles.length; i += 1) {
            let positiveSum = 0;
            let negativeSum = 0;
            for (let j = i - period + 1; j <= i; j += 1) {
              positiveSum += positive[j];
              negativeSum += negative[j];
            }
            output[i] = negativeSum === 0 ? 100
              : 100 - 100 / (1 + positiveSum / negativeSum);
          }
          return output;
        }

        function normalizeIndodax(payload) {
          let rows;
          if (Array.isArray(payload)) {
            rows = payload;
          } else if (payload && Array.isArray(payload.t)) {
            rows = payload.t.map((time, index) => ({
              Time: time, Open: payload.o[index], High: payload.h[index],
              Low: payload.l[index], Close: payload.c[index],
              Volume: payload.v ? payload.v[index] : 0
            }));
          } else {
            throw new Error("Format data Indodax tidak dikenal.");
          }
          return rows.map((row) => {
            let timestamp = Number(row.Time ?? row.time ?? row.t);
            const open = Number(row.Open ?? row.open ?? row.o);
            const high = Number(row.High ?? row.high ?? row.h);
            const low = Number(row.Low ?? row.low ?? row.l);
            const close = Number(row.Close ?? row.close ?? row.c);
            const volume = Number(row.Volume ?? row.volume ?? row.v ?? 0);
            if (![timestamp, open, high, low, close, volume].every(Number.isFinite)) return null;
            if (timestamp < 1e12) timestamp *= 1000;
            return { t: timestamp, o: open, h: high, l: low, c: close, v: volume };
          }).filter(Boolean).map((candle, index, candles) => ({
            ...candle,
            x: index,
            closeAt: candle.t + frameSettings[state.timeframe].seconds * 1000
          }));
        }

        function normalizeCoinGecko(payload) {
          if (!payload || !Array.isArray(payload.prices) || !payload.prices.length) {
            throw new Error("Data harga CoinGecko kosong atau tidak valid.");
          }
          const interval = frameSettings[state.timeframe].seconds * 1000;
          const candlesByTime = new Map();
          payload.prices.forEach((point, index) => {
            const timestamp = Number(point && point[0]);
            const price = Number(point && point[1]);
            if (!Number.isFinite(timestamp) || !Number.isFinite(price) || price <= 0) return;
            const bucket = Math.floor(timestamp / interval) * interval;
            const volumePoint = payload.total_volumes && payload.total_volumes[index];
            const volume = Number(volumePoint && volumePoint[1]);
            const candle = candlesByTime.get(bucket);
            if (candle) {
              candle.h = Math.max(candle.h, price);
              candle.l = Math.min(candle.l, price);
              candle.c = price;
              if (Number.isFinite(volume) && volume >= 0) candle.v = volume;
            } else {
              candlesByTime.set(bucket, {
                t: bucket, o: price, h: price, l: price, c: price,
                v: Number.isFinite(volume) && volume >= 0 ? volume : 0,
                closeAt: bucket + interval
              });
            }
          });
          const candles = Array.from(candlesByTime.values());
          if (!candles.length) {
            throw new Error("Data harga CoinGecko kosong atau tidak valid.");
          }
          return candles.map((candle, index) => ({ ...candle, x: index }));
        }

        async function fetchBinance() {
          const settings = frameSettings[state.timeframe];
          const url = "https://api.binance.com/api/v3/klines?symbol="
            + encodeURIComponent(state.symbol + "USDT") + "&interval="
            + encodeURIComponent(settings.binance) + "&limit=300";
          const response = await fetch(url);
          if (!response.ok) throw new Error("Binance HTTP " + response.status);
          const rows = await response.json();
          const candles = rows.map((row, index) => ({
            x: index, t: Number(row[0]), o: Number(row[1]),
            h: Number(row[2]), l: Number(row[3]), c: Number(row[4]),
            v: Number(row[5]), closeAt: Number(row[6]) + 1
          }));
          if (!candles.length || candles.some((item) =>
            ![item.t, item.o, item.h, item.l, item.c, item.v, item.closeAt].every(Number.isFinite))) {
            throw new Error("Data Binance kosong atau tidak valid.");
          }
          return candles;
        }

        async function fetchIndodax() {
          const settings = frameSettings[state.timeframe];
          const to = Math.floor(Date.now() / 1000);
          const from = to - settings.seconds * 300;
          const url = "https://indodax.com/tradingview/history_v2?symbol="
            + encodeURIComponent(state.symbol.toLowerCase() + "idr") + "&tf="
            + encodeURIComponent(settings.indodax) + "&from=" + from + "&to=" + to;
          const response = await fetch(url);
          if (!response.ok) throw new Error("Indodax HTTP " + response.status);
          const candles = normalizeIndodax(await response.json());
          if (!candles.length) throw new Error("Data Indodax kosong atau tidak valid.");
          return candles;
        }

        async function fetchCoinGecko() {
          if (!state.coinId) throw new Error("ID koin CoinGecko tidak tersedia.");
          const url = "https://api.coingecko.com/api/v3/coins/"
            + encodeURIComponent(state.coinId)
            + "/market_chart?vs_currency=usd&days=7";
          const response = await fetch(url);
          if (!response.ok) throw new Error("CoinGecko HTTP " + response.status);
          const candles = normalizeCoinGecko(await response.json());
          if (!candles.length) throw new Error("Data CoinGecko kosong atau tidak valid.");
          return candles;
        }

        function pointSeries(values) {
          return values.map((value, index) => ({ x: index, y: value }));
        }

        function makeMainDatasets() {
          const candles = state.candles;
          const closes = candles.map((item) => item.c);
          const datasets = [];
          const bands = bollingerBands(closes);
          state.overlays.bbLower = indicatorInputs.bb.checked ? bands.lower : null;
          state.overlays.bbUpper = indicatorInputs.bb.checked ? bands.upper : null;

          if (state.type === "candlestick") {
            datasets.push({
              type: "candlestick", label: state.symbol + " OHLC", data: candles,
              color: { up: colors.green, down: colors.red, unchanged: colors.muted },
              backgroundColors: { up: colors.green, down: colors.red, unchanged: colors.muted },
              borderColors: { up: colors.green, down: colors.red, unchanged: colors.muted }
            });
          } else {
            datasets.push({
              type: "line", label: state.symbol + " price",
              data: pointSeries(closes),
              borderColor: colors.purple,
              backgroundColor: state.type === "area" ? colors.purpleFill : "transparent",
              borderWidth: 2, pointRadius: 0, fill: state.type === "area", tension: 0
            });
          }

          if (indicatorInputs.bb.checked) {
            datasets.push({
              type: "line", label: "BB Lower", data: pointSeries(bands.lower),
              borderColor: "rgba(107,114,128,.55)", borderWidth: 1,
              pointRadius: 0, fill: false, spanGaps: false
            });
            datasets.push({
              type: "line", label: "BB Middle (MA 20)", data: pointSeries(bands.middle),
              borderColor: "rgba(107,114,128,.8)", borderWidth: 1,
              pointRadius: 0, fill: false, spanGaps: false
            });
            datasets.push({
              type: "line", label: "BB Upper", data: pointSeries(bands.upper),
              borderColor: "rgba(107,114,128,.55)", borderWidth: 1,
              backgroundColor: "rgba(107,114,128,.10)",
              pointRadius: 0, fill: "-2", spanGaps: false
            });
          }

          for (const [key, period, color, label] of [
            ["ma9", 9, colors.yellow, "MA 9"],
            ["ma20", 20, colors.blue, "MA 20"],
            ["ma50", 50, colors.violet, "MA 50"]
          ]) {
            if (indicatorInputs[key].checked) {
              datasets.push({
                type: "line", label,
                data: pointSeries(movingAverage(closes, period)),
                borderColor: color, borderWidth: 1.5, pointRadius: 0,
                fill: false, spanGaps: false, tension: 0
              });
            }
          }
          return datasets;
        }

        function syncTimeRange(sourceChart) {
          if (state.syncingPan) return;
          const otherChart = sourceChart === state.mainChart
            ? state.indicatorChart : state.mainChart;
          if (!otherChart || !sourceChart.scales.x || !otherChart.scales.x) return;
          const { min, max } = sourceChart.scales.x;
          state.syncingPan = true;
          otherChart.options.scales.x.min = min;
          otherChart.options.scales.x.max = max;
          otherChart.update("none");
          state.syncingPan = false;
        }

        function zoomOptions() {
          return {
            limits: { x: { min: "original", max: "original", minRange: 5 } },
            pan: {
              enabled: true, mode: "x",
              onPan: ({ chart }) => syncTimeRange(chart),
              onPanComplete: ({ chart }) => syncTimeRange(chart)
            },
            zoom: {
              mode: "x", wheel: { enabled: true }, pinch: { enabled: true },
              drag: { enabled: true, threshold: 8 },
              onZoom: ({ chart }) => syncTimeRange(chart),
              onZoomComplete: ({ chart }) => syncTimeRange(chart)
            }
          };
        }

        function renderMainChart() {
          if (state.mainChart) state.mainChart.destroy();
          const candles = state.candles;
          state.mainChart = new Chart(mainCanvas, {
            type: state.type === "candlestick" ? "candlestick" : "line",
            data: { datasets: makeMainDatasets() },
            plugins: [livePriceLine],
            options: {
              responsive: true, maintainAspectRatio: false, animation: false,
              parsing: false, interaction: { mode: "index", intersect: false },
              plugins: {
                legend: { display: false },
                tooltip: {
                  backgroundColor: colors.tooltipBackground,
                  titleColor: colors.tooltipText,
                  bodyColor: colors.tooltipText,
                  borderColor: colors.grid,
                  borderWidth: 1,
                  callbacks: {
                    title(items) {
                      return items.length
                        ? new Date(candles[items[0].dataIndex].t).toLocaleString()
                        : "";
                    },
                    label(context) {
                      if (context.dataset.type === "candlestick") {
                        const candle = context.raw;
                        return [
                          "Open " + priceFormat(candle.o),
                          "High " + priceFormat(candle.h),
                          "Low " + priceFormat(candle.l),
                          "Close " + priceFormat(candle.c)
                        ];
                      }
                      return context.dataset.label + ": " + priceFormat(context.parsed.y);
                    }
                  }
                },
                zoom: zoomOptions()
              },
              scales: {
                x: { type: "linear", min: 0, max: Math.max(1, candles.length - 1),
                  grid: { display: false },
                  ticks: { color: colors.muted, maxTicksLimit: 8, maxRotation: 0,
                    callback(value) {
                      const candle = candles[Math.round(value)];
                      if (!candle) return "";
                      return new Date(candle.t).toLocaleString([], {
                        month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit"
                      });
                    } } },
                y: { position: "right", grid: { color: colors.grid },
                  ticks: { color: colors.muted, callback: (value) => priceFormat(value) } }
              }
            }
          });
        }

        function makeIndicatorDatasets() {
          const labels = state.candles.map((item) => item.x);
          if (state.mode === "rsi") {
            return [
              { type: "line", label: "RSI (14)",
                data: pointSeries(relativeStrengthIndex(state.candles.map((item) => item.c))),
                borderColor: colors.muted, borderWidth: 1.5, pointRadius: 0, fill: false },
              { type: "line", label: "Overbought",
                data: labels.map((x) => ({ x, y: 70 })),
                borderColor: colors.redLine, borderDash: [4, 4],
                borderWidth: 1, pointRadius: 0 },
              { type: "line", label: "Oversold",
                data: labels.map((x) => ({ x, y: 30 })),
                borderColor: colors.greenLine, borderDash: [4, 4],
                borderWidth: 1, pointRadius: 0 }
            ];
          }
          if (state.mode === "mfi") {
            return [
              { type: "line", label: "MFI (14)",
                data: pointSeries(moneyFlowIndex(state.candles)),
                borderColor: colors.violet, borderWidth: 1.5, pointRadius: 0, fill: false },
              { type: "line", label: "Overbought",
                data: labels.map((x) => ({ x, y: 80 })),
                borderColor: colors.redLine, borderDash: [4, 4],
                borderWidth: 1, pointRadius: 0 },
              { type: "line", label: "Oversold",
                data: labels.map((x) => ({ x, y: 20 })),
                borderColor: colors.greenLine, borderDash: [4, 4],
                borderWidth: 1, pointRadius: 0 }
            ];
          }
          return [{
            type: "bar", label: "Volume",
            data: state.candles.map((item) => ({ x: item.x, y: item.v })),
            backgroundColor: state.candles.map((item) =>
              item.c >= item.o ? colors.greenFill : colors.redFill),
            borderSkipped: false, barPercentage: .9, categoryPercentage: 1
          }];
        }

        function renderIndicatorChart() {
          if (state.indicatorChart) state.indicatorChart.destroy();
          const bounded = state.mode === "rsi" || state.mode === "mfi";
          document.getElementById("panelLabel").textContent =
            state.mode === "rsi" ? "RSI (14)" : state.mode === "mfi" ? "MFI (14)" : "Volume";
          state.indicatorChart = new Chart(indicatorCanvas, {
            type: state.mode === "volume" ? "bar" : "line",
            data: { datasets: makeIndicatorDatasets() },
            options: {
              responsive: true, maintainAspectRatio: false, animation: false,
              parsing: false, interaction: { mode: "index", intersect: false },
              plugins: {
                legend: { display: false },
                tooltip: {
                  enabled: true,
                  backgroundColor: colors.tooltipBackground,
                  titleColor: colors.tooltipText,
                  bodyColor: colors.tooltipText,
                  borderColor: colors.grid,
                  borderWidth: 1
                },
                zoom: zoomOptions()
              },
              scales: {
                x: { type: "linear", min: 0,
                  max: Math.max(1, state.candles.length - 1),
                  grid: { display: false }, ticks: { display: false } },
                y: bounded
                  ? { min: 0, max: 100, position: "right", grid: { color: colors.grid },
                    ticks: { stepSize: 20, color: colors.muted, font: { size: 9 } } }
                  : { beginAtZero: true, position: "right", grid: { color: colors.grid },
                    ticks: { maxTicksLimit: 4, color: colors.muted, font: { size: 9 } } }
              }
            }
          });
        }

        function updateCharts() {
          if (!state.mainChart || !state.indicatorChart) return;
          const xScale = state.mainChart.scales.x;
          const currentMin = xScale.min;
          const currentMax = xScale.max;
          const latestIndex = state.candles.length - 1;
          const followingLatest = currentMax >= latestIndex - 1;
          const visibleSpan = currentMax - currentMin;
          state.mainChart.data.datasets = makeMainDatasets();
          if (followingLatest) {
            state.mainChart.options.scales.x.max = latestIndex;
            state.mainChart.options.scales.x.min = Math.max(0, latestIndex - visibleSpan);
          }
          state.indicatorChart.data.datasets = makeIndicatorDatasets();
          state.mainChart.update("none");
          state.indicatorChart.options.scales.x.min = state.mainChart.scales.x.min;
          state.indicatorChart.options.scales.x.max = state.mainChart.scales.x.max;
          state.indicatorChart.update("none");
          updateHeader();
        }

        function syncPriceHeader() {
          const latest = state.candles[state.candles.length - 1];
          if (!latest) return;
          document.getElementById("currentPrice").textContent = priceFormat(latest.c);
          const first = state.candles[0].c;
          const change = first === 0 ? 0 : (latest.c - first) / first * 100;
          const changeEl = document.getElementById("priceChange");
          changeEl.textContent = (change >= 0 ? "+" : "") + change.toFixed(2) + "%";
          changeEl.classList.toggle("negative", change < 0);
        }

        function updateHeader() {
          syncPriceHeader();
        }

        function formatCountdown(milliseconds) {
          const seconds = Math.max(0, Math.ceil(milliseconds / 1000));
          const hours = Math.floor(seconds / 3600);
          const minutes = Math.floor((seconds % 3600) / 60);
          const remainder = seconds % 60;
          return hours > 0
            ? [hours, minutes, remainder].map((value) => String(value).padStart(2, "0")).join(":")
            : [minutes, remainder].map((value) => String(value).padStart(2, "0")).join(":");
        }

        function updateCountdown() {
          const latest = state.candles[state.candles.length - 1];
          document.getElementById("candleTimer").textContent = latest
            ? formatCountdown(latest.closeAt - Date.now())
            : "--:--";
        }

        function stopBinanceSocket() {
          if (state.reconnectTimer) clearTimeout(state.reconnectTimer);
          state.reconnectTimer = null;
          if (state.socket) {
            state.socket.onclose = null;
            state.socket.close();
            state.socket = null;
          }
        }

        function connectBinanceSocket() {
          stopBinanceSocket();
          if (state.source !== "binance" || !("WebSocket" in window)) return;
          const interval = frameSettings[state.timeframe].binance;
          const stream = state.symbol.toLowerCase() + "@kline_" + interval;
          const socket = new WebSocket("wss://stream.binance.com:9443/ws/" + stream);
          state.socket = socket;
          socket.onmessage = (event) => {
            try {
              const payload = JSON.parse(event.data);
              const kline = payload.k;
              if (!kline || !state.candles.length) return;
              const candleTime = Number(kline.t);
              const latest = state.candles[state.candles.length - 1];
              const next = {
                x: latest.x, t: candleTime,
                o: Number(kline.o), h: Number(kline.h), l: Number(kline.l),
                c: Number(kline.c), v: Number(kline.v), closeAt: Number(kline.T) + 1
              };
              if (![next.t, next.o, next.h, next.l, next.c, next.v, next.closeAt]
                .every(Number.isFinite)) return;
              if (latest.t === candleTime) {
                state.candles[state.candles.length - 1] = next;
              } else if (candleTime > latest.t) {
                next.x = latest.x + 1;
                state.candles.push(next);
                if (state.candles.length > 300) {
                  state.candles.shift();
                  state.candles.forEach((candle, index) => { candle.x = index; });
                }
              } else {
                return;
              }
              updateCharts();
              updateCountdown();
            } catch (error) {
              console.error("Gagal memproses update Binance WebSocket:", error);
            }
          };
          socket.onclose = () => {
            if (state.socket !== socket || state.source !== "binance") return;
            state.reconnectTimer = setTimeout(connectBinanceSocket, 3000);
          };
          socket.onerror = () => socket.close();
        }

        async function loadData() {
          const requestId = ++state.loadRequestId;
          stopBinanceSocket();
          state.candles = [];
          if (state.mainChart) {
            state.mainChart.destroy();
            state.mainChart = null;
          }
          if (state.indicatorChart) {
            state.indicatorChart.destroy();
            state.indicatorChart = null;
          }
          document.getElementById("currentPrice").textContent = "--";
          document.getElementById("priceChange").textContent = "--";
          document.getElementById("candleTimer").textContent = "--:--";
          errorEl.style.display = "none";
          state.source = "binance";
          setSourceStatus("binance");
          try {
            state.candles = await fetchBinance();
          } catch (binanceError) {
            if (requestId !== state.loadRequestId) return;
            console.warn("Data Binance tidak tersedia; mencoba Indodax:", binanceError);
            state.source = "indodax";
            setSourceStatus("indodax");
            try {
              state.candles = await fetchIndodax();
              document.getElementById("pairLabel").textContent = state.symbol + "/IDR";
            } catch (indodaxError) {
              if (requestId !== state.loadRequestId) return;
              console.warn("Data Indodax tidak tersedia; mencoba CoinGecko:", indodaxError);
              state.source = "coingecko";
              setSourceStatus("coingecko");
              try {
                state.candles = await fetchCoinGecko();
              } catch (coinGeckoError) {
                if (requestId !== state.loadRequestId) return;
                console.error("Data chart tidak tersedia dari Binance, Indodax, maupun CoinGecko:",
                  { binanceError, indodaxError, coinGeckoError });
                state.candles = [];
                errorEl.textContent = "Data pair tidak tersedia di Binance, Indodax, atau CoinGecko untuk "
                  + state.symbol + ".";
                errorEl.style.display = "block";
                return;
              }
            }
          }
          if (requestId !== state.loadRequestId) return;
          document.getElementById("pairLabel").textContent = state.symbol + "/"
            + (state.source === "indodax" ? "IDR" : state.source === "coingecko" ? "USD" : "USDT");
          renderMainChart();
          renderIndicatorChart();
          updateHeader();
          updateCountdown();
          if (state.countdownTimer) clearInterval(state.countdownTimer);
          state.countdownTimer = setInterval(updateCountdown, 250);
          if (state.source === "binance") connectBinanceSocket();
        }

        document.querySelectorAll("#typeGroup button").forEach((button) => {
          button.addEventListener("click", () => {
            document.querySelectorAll("#typeGroup button")
              .forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            state.type = button.dataset.type;
            if (state.candles.length) renderMainChart();
          });
        });
        document.querySelectorAll("#timeframeGroup button").forEach((button) => {
          button.addEventListener("click", () => {
            document.querySelectorAll("#timeframeGroup button")
              .forEach((item) => item.classList.remove("active"));
            button.classList.add("active");
            state.timeframe = button.dataset.tf;
            loadData();
          });
        });
        Object.entries(indicatorInputs).forEach(([name, input]) => {
          input.addEventListener("change", () => {
            if (name === "rsi" || name === "mfi") {
              if (input.checked) {
                const other = name === "rsi" ? indicatorInputs.mfi : indicatorInputs.rsi;
                other.checked = false;
                state.mode = name;
                document.getElementById("panelMode").value = name;
              } else if (state.mode === name) {
                state.mode = "volume";
                document.getElementById("panelMode").value = "volume";
              }
              if (!indicatorInputs.rsi.checked && !indicatorInputs.mfi.checked) {
                state.mode = "volume";
                document.getElementById("panelMode").value = "volume";
              }
              if (state.candles.length) renderIndicatorChart();
              return;
            }
            if (state.candles.length) renderMainChart();
          });
        });
        document.getElementById("panelMode").addEventListener("change", (event) => {
          state.mode = event.target.value;
          indicatorInputs.rsi.checked = state.mode === "rsi";
          indicatorInputs.mfi.checked = state.mode === "mfi";
          if (state.candles.length) renderIndicatorChart();
        });
        document.getElementById("pairButton").addEventListener("click", () => {
          coinModal.classList.add("open");
          coinSearch.value = "";
          renderCoinList();
          coinSearch.focus();
        });
        coinSearch.addEventListener("input", () => renderCoinList(coinSearch.value));
        document.getElementById("closeCoinModal")
          .addEventListener("click", closeCoinModal);
        coinModal.addEventListener("click", (event) => {
          if (event.target === coinModal) closeCoinModal();
        });
        document.addEventListener("keydown", (event) => {
          if (event.key === "Escape" && coinModal.classList.contains("open")) {
            closeCoinModal();
          }
        });
        document.getElementById("resetZoom").addEventListener("click", () => {
          if (state.mainChart) state.mainChart.resetZoom();
          if (state.indicatorChart) state.indicatorChart.resetZoom();
        });
        const initialCoin = coins.find((coin) => coin.id === INITIAL_COIN_ID)
          || coins.find((coin) => coin.symbol === state.symbol);
        if (initialCoin) state.coinId = initialCoin.id;
        renderCoinList();
        loadData();
      </script>
    </body>
    </html>
    """.replace("__SYMBOL__", base_asset)
    html_code = html_code.replace("__COINS_JSON__", coin_options_json)
    html_code = html_code.replace("__INITIAL_COIN_ID__", initial_coin_id_json)
    html_code = html_code.replace("__IS_DARK_MODE__", json.dumps(is_dark_mode))
    palette = ui.get_theme_palette(is_dark_mode)
    chart_colors = {
        "purple": palette["accent"],
        "purpleFill": palette["accent_fill"],
        "green": palette["positive"],
        "red": palette["negative"],
        "yellow": palette["warning"],
        "blue": palette["info"],
        "violet": palette["accent"],
        "grid": palette.get("chart_grid", palette["border"]),
        "muted": palette["secondary_text"],
        "tooltipBackground": palette["input_background"],
        "tooltipText": palette["primary_text"],
        "priceUp": palette["positive"],
        "priceDown": palette["negative"],
        "greenFill": palette["positive_fill"],
        "redFill": palette["negative_fill"],
        "greenLine": palette["positive_line"],
        "redLine": palette["negative_line"],
    }
    chart_colors_json = json.dumps(chart_colors, ensure_ascii=True).replace(
        "</", "<\\/"
    )
    theme_style = f"""
        :root {{
          color-scheme: {"dark" if is_dark_mode else "light"};
          --cs-main-background: {palette.get("main_background_gradient", palette["main_background"])};
          --cs-plot-area-background: {palette.get("chart_area_background", palette["content_background"])};
          --cs-content-background: {palette["content_background"]};
          --cs-primary-text: {palette["primary_text"]};
          --cs-secondary-text: {palette["secondary_text"]};
          --cs-border: {palette["border"]};
          --cs-accent: {palette["accent"]};
          --cs-input-background: {palette["input_background"]};
          --cs-positive: {palette["positive"]};
          --cs-positive-text: {palette["positive_text"]};
          --cs-negative: {palette["negative"]};
          --cs-negative-text: {palette["negative_text"]};
        }}
        body, .terminal {{ color: var(--cs-primary-text); background: var(--cs-main-background); }}
        .pair-button, .indicator-trigger, .panel-select, .coin-search,
        .modal-card, .indicator-menu {{
          color: var(--cs-primary-text); background: var(--cs-input-background);
          border-color: var(--cs-border);
        }}
        .pair-button, .indicator-trigger {{ border: 1px solid var(--cs-border); }}
        .price, .panel-label, .candle-timer, .coin-name span,
        .pair-chevron, .search-icon, .empty-results {{ color: var(--cs-secondary-text); }}
        .price strong, .modal-head, .coin-name strong {{ color: var(--cs-primary-text); }}
        .indicator-menu label {{ color: var(--cs-primary-text); }}
        .indicator-panel {{ border-top-color: var(--cs-border); }}
        .coin-option:hover, .pair-button:hover, .indicator-trigger:hover,
        .indicator-menu label:hover {{ color: var(--cs-primary-text); background: var(--cs-main-background); }}
        .coin-logo {{ background: var(--cs-border); }}
        .coin-search:focus {{ border-color: var(--cs-accent); }}
        .change {{ color: var(--cs-positive); }}
        .change.negative {{ color: var(--cs-negative); }}
        .source-dot {{ background: var(--cs-positive); }}
        .source-dot.indodax {{ background: var(--cs-negative); }}
        .source-dot.coingecko {{ background: var(--cs-accent); }}
        input {{ color: var(--cs-primary-text); accent-color: var(--cs-accent); }}
        .error {{ color: var(--cs-negative); background: var(--cs-content-background); }}
        .modal-close {{ color: var(--cs-secondary-text); }}
        """
    if is_dark_mode:
        theme_style += """
        .charts { background: var(--cs-plot-area-background); }
        """
    if not allow_coin_selection:
        theme_style += ".pair-button, .coin-modal { display: none !important; }"
    html_code = html_code.replace("__CHART_COLORS__", chart_colors_json)
    html_code = html_code.replace("__THEME_STYLE__", theme_style)

    st.iframe(
        html_code,
        height=height,
        alt="Interactive cryptocurrency market chart",
    )
