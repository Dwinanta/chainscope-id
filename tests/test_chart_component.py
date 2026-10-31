import pytest

from chainscope import chart_component


def test_render_modern_chart_includes_supported_features(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        chart_component.components,
        "html",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    chart_component.render_modern_chart("ETH", height=640)

    html = rendered["html"]
    assert rendered["options"] == {"height": 640, "scrolling": False}
    assert "ETH/USDT" in html
    assert "https://api.binance.com/api/v3/klines" in html
    assert "https://indodax.com/tradingview/history_v2" in html
    assert 'data-type="candlestick"' in html
    assert "chart.js@latest" in html
    assert "chartjs-chart-financial@0.2.1" in html
    assert "chartjs-plugin-zoom@latest" in html
    assert 'id="pairButton"' in html
    assert "border: 1px solid #e5e7eb" in html
    assert "border-radius: 8px" in html
    assert "color: #1f2937" in html
    assert "background: #f8f5ff" in html
    assert "border-radius: 16px" in html
    assert "class=\"search-icon\"" in html
    assert "coin-option:hover { color: #1f2937; background: #f8f5ff; }" in html
    assert 'id="coinMark"' not in html
    assert 'id="coinModal"' in html
    assert 'id="coinSearch"' in html
    assert 'id="coinList"' in html
    assert '"symbol": "ETH"' in html
    assert 'state.symbol = coin.symbol' in html
    assert 'coinSearch.addEventListener("input"' in html
    assert 'coinModal.classList.add("open")' in html
    assert 'className = "coin-logo"' in html
    assert 'width = 24' in html
    assert "hydrateCoinLogo" in html
    assert 'state.symbol.toLowerCase() + "@kline_"' in html
    assert 'height: 100vh' in html
    assert 'overflow: hidden' in html
    assert 'id="candleTimer"' in html
    assert html.index('id="pairButton"') < html.index('id="candleTimer"')
    assert html.count('class="toolbar-row"') == 1
    assert html.index('id="sourceBadge"') < html.index('id="pairButton"')
    assert html.index('id="pairButton"') < html.index('id="currentPrice"')
    assert html.index('id="priceChange"') < html.index('id="indicatorTrigger"')
    assert html.index('id="indicatorTrigger"') < html.index('id="typeGroup"')
    assert html.index('id="typeGroup"') < html.index('id="timeframeGroup"')
    assert html.index('id="timeframeGroup"') < html.index('id="candleTimer"')
    assert html.index('id="timeframeGroup"') < html.index('id="resetZoom"')
    assert html.index('id="chkMA9"') < html.index('id="typeGroup"')
    assert 'id="chkMA9"' in html
    assert 'id="chkMA20"' in html
    assert 'id="chkMA50"' in html
    assert 'id="chkBB"' in html
    assert 'id="chkRSI"' in html
    assert 'id="chkMFI"' in html
    assert 'id="indicatorTrigger"' in html
    assert 'id="indicatorMenu"' in html
    assert 'aria-expanded="false"' in html
    assert ".indicator-menu { position: absolute; z-index: 15; left: 0; top: calc(100% + 5px);" in html
    assert 'class="source-dot" id="sourceBadge"' in html
    assert 'sourceBadge.textContent = "Indodax (tanpa WebSocket)"' not in html
    assert 'id="panelMode"' in html
    assert 'id="indicatorChart"' in html
    assert "bollingerBands" in html
    assert "moneyFlowIndex" in html
    assert 'label: "BB Middle (MA 20)"' in html
    assert "rgba(107,114,128,.10)" in html
    assert "color: { up: colors.green, down: colors.red" in html
    assert 'wheel: { enabled: true }' in html
    assert "enabled: true, mode: \"x\"" in html
    assert 'title="Reset zoom"' in html
    assert 'height: 100vh' in html
    assert 'flex: 7 1 0' in html
    assert 'flex: 3 1 0' in html
    assert 'legend: { display: false }' in html
    assert 'overflow: hidden' in html
    assert "relativeStrengthIndex" in html
    assert "livePriceLine" in html
    assert "wss://stream.binance.com:9443/ws/" in html
    assert "onPan: ({ chart }) => syncTimeRange(chart)" in html
    assert "onZoom: ({ chart }) => syncTimeRange(chart)" in html
    assert "syncTimeRange" in html
    assert "formatCountdown" in html
    assert "closeAt - Date.now()" in html
    assert html.count("animation: false") == 2
    assert 'streamlit' not in html


def test_render_modern_chart_rejects_invalid_symbol(monkeypatch):
    monkeypatch.setattr(
        chart_component.components,
        "html",
        lambda *_args, **_kwargs: pytest.fail("Invalid symbols must not render HTML"),
    )

    with pytest.raises(ValueError, match="Simbol koin tidak valid"):
        chart_component.render_modern_chart("BTC</script>")


def test_render_modern_chart_defaults_to_btcusdt(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        chart_component.components,
        "html",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    chart_component.render_modern_chart()

    assert "BTC/USDT" in rendered["html"]
    assert 'const INITIAL_SYMBOL = "BTC"' in rendered["html"]
    assert rendered["options"] == {"height": 600, "scrolling": False}


def test_render_modern_chart_embeds_coin_ids_and_logos(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        chart_component.components,
        "html",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    chart_component.render_modern_chart(
        coins=[{
            "id": "ethereum",
            "symbol": "eth",
            "name": "Ethereum",
            "image": "https://assets.coingecko.com/coins/images/279/small/ethereum.png",
        }],
        selected_coin_id="ethereum",
    )

    assert '"id": "ethereum"' in rendered["html"]
    assert '"image": "https://assets.coingecko.com/coins/images/279/small/ethereum.png"' in rendered["html"]
    assert 'const INITIAL_COIN_ID = "ethereum"' in rendered["html"]


def test_render_modern_chart_escapes_coin_data_for_script_context(monkeypatch):
    rendered = {}
    monkeypatch.setattr(
        chart_component.components,
        "html",
        lambda html, **kwargs: rendered.update(html=html, options=kwargs),
    )

    chart_component.render_modern_chart(
        coins=[{
            "id": "safe",
            "symbol": "safe",
            "name": "</script><script>alert(1)</script>",
        }]
    )

    assert "</script><script>alert(1)</script>" not in rendered["html"]
    assert r"<\/script><script>alert(1)<\/script>" in rendered["html"]
