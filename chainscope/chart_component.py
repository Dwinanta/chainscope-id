"""Komponen Chart Chart.js (Auto-Switch Binance/Indodax)."""
import streamlit.components.v1 as components

def render_modern_chart(symbol="BTCUSDT", height=650):
    # Base asset (BTC, ETH, dll)
    base_asset = symbol.replace("USDT", "")
    
    html_code = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom"></script>
        <script src="https://cdn.jsdelivr.net/npm/luxon@3.4.4"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon"></script>
        <style>
            :root {{
                --primary: #7c3aed;
                --primary-light: #ede9fe;
                --bg-soft: #f8f5ff;
                --card-white: #ffffff;
                --border-soft: #e5e7eb;
                --text-dark: #1f2937;
                --text-muted: #6b7280;
                --green: #10b981;
                --red: #ef4444;
                --radius: 16px;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: 'Inter', sans-serif; background-color: var(--bg-soft); color: var(--text-dark); display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; padding: 10px; }}
            .chart-card {{ background-color: var(--card-white); border: 1px solid var(--primary-light); border-radius: var(--radius); width: 100%; height: 100%; padding: 20px; display: flex; flex-direction: column; gap: 15px; position: relative; }}
            .header {{ display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; }}
            .asset-title {{ display: flex; align-items: center; gap: 12px; }}
            .asset-title h1 {{ font-size: 1.4rem; font-weight: 700; margin: 0; text-transform: uppercase; }}
            .pair-badge {{ background-color: var(--primary-light); color: var(--primary); padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; font-weight: 600; }}
            .price-row {{ display: flex; align-items: center; gap: 12px; margin-top: 5px; }}
            .current-price {{ font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; }}
            .change-badge {{ font-size: 0.85rem; font-weight: 600; padding: 4px 8px; border-radius: 6px; background-color: #ecfdf5; color: var(--green); }}
            .change-badge.negative {{ background-color: #fef2f2; color: var(--red); }}
            .live-indicator {{ display: flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: 600; color: var(--text-muted); background: #f3f4f6; padding: 4px 10px; border-radius: 20px; }}
            .live-dot {{ width: 8px; height: 8px; background-color: var(--green); border-radius: 50%; animation: blink 1.5s infinite; }}
            @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
            .source-badge {{ font-size: 0.7rem; font-weight: 700; padding: 4px 8px; border-radius: 4px; background: #fef3c7; color: #d97706; margin-left: 10px; display: none; }}
            
            .controls {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }}
            .btn-group {{ display: flex; background-color: var(--primary-light); padding: 4px; border-radius: 10px; gap: 2px; }}
            .btn-group button {{ background: transparent; border: none; padding: 6px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 500; color: var(--primary); cursor: pointer; transition: all 0.2s; font-family: inherit; }}
            .btn-group button:hover {{ background-color: rgba(255,255,255,0.5); }}
            .btn-group button.active {{ background-color: var(--card-white); color: var(--primary); font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .reset-btn {{ background: transparent; border: 1px solid var(--border-soft); border-radius: 8px; padding: 6px; cursor: pointer; color: var(--text-muted); }}
            .reset-btn:hover {{ color: var(--primary); border-color: var(--primary); background-color: var(--primary-light); }}
            
            .indicators {{ display: flex; gap: 15px; font-size: 0.85rem; color: var(--text-muted); margin-top: -5px; }}
            .indicators label {{ display: flex; align-items: center; gap: 5px; cursor: pointer; }}

            .chart-wrapper {{ position: relative; flex-grow: 1; width: 100%; min-height: 0; }}
            .error-msg {{ display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: var(--red); background: #fef2f2; padding: 20px; border-radius: 12px; border: 1px solid #fecaca; z-index: 10; }}
        </style>
    </head>
    <body>
        <div class="chart-card">
            <div id="errorMsg" class="error-msg"><b>Gagal memuat data.</b><br>Pastikan koneksi internet stabil.</div>
            
            <div class="header">
                <div class="asset-info">
                    <div class="asset-title">
                        <h1 id="assetName">{base_asset}</h1>
                        <span class="pair-badge" id="pairLabel">{base_asset} / USDT</span>
                        <span id="sourceBadge" class="source-badge">Indodax Fallback</span>
                    </div>
                    <div class="price-row">
                        <span class="current-price" id="currentPrice">$0.00</span>
                        <span class="change-badge" id="priceChange">--%</span>
                    </div>
                </div>
                <div class="live-indicator"><div class="live-dot"></div> Live</div>
            </div>

            <div class="controls">
                <div class="btn-group" id="typeGroup">
                    <button data-type="area" class="active">Area</button>
                    <button data-type="line">Line</button>
                    <button data-type="candlestick">Candle</button>
                </div>
                <div class="btn-group" id="timeframeGroup">
                    <button data-tf="1m" data-idx="1">1m</button>
                    <button data-tf="5m" data-idx="5">5m</button>
                    <button data-tf="15m" data-idx="15">15m</button>
                    <button data-tf="1h" data-idx="60" class="active">1h</button>
                    <button data-tf="4h" data-idx="240">4h</button>
                    <button data-tf="1d" data-idx="D">1d</button>
                </div>
                <button class="reset-btn" id="resetZoom" title="Reset Zoom">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                </button>
            </div>

            <div class="indicators">
                <label><input type="checkbox" id="chkMA20"> MA 20</label>
                <label><input type="checkbox" id="chkMA50"> MA 50</label>
                <label><input type="checkbox" id="chkRSI"> RSI</label>
            </div>

            <div class="chart-wrapper"><canvas id="chartCanvas"></canvas></div>
        </div>

        <script>
            // State Utama
            const state = {{ 
                symbol: '{base_asset}', 
                type: 'area', 
                timeframe: '1h',
                indodaxTf: '60',
                source: 'binance', // 'binance' atau 'indodax'
                chartInstance: null, 
                rawData: [] 
            }};
            
            const priceEl = document.getElementById('currentPrice');
            const changeEl = document.getElementById('priceChange');
            const canvas = document.getElementById('chartCanvas');
            const errorMsg = document.getElementById('errorMsg');
            const pairLabel = document.getElementById('pairLabel');
            const sourceBadge = document.getElementById('sourceBadge');
            
            const COLORS = {{ purple: '#7c3aed', purpleFill: 'rgba(124, 58, 237, 0.15)', green: '#10b981', red: '#ef4444', grid: '#f3f4f6', text: '#6b7280', ma20: '#2962FF', ma50: '#FFB300', rsi: '#171827' }};

            // Format Angka
            function formatMoney(num) {{
                if (state.source === 'binance') return '$' + num.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
                else return 'Rp' + num.toLocaleString('id-ID', {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }});
            }}

            // Indikator
            function calcSMA(data, period) {{
                let sma = [];
                for (let i = 0; i < data.length; i++) {{
                    if (i < period - 1) {{ sma.push(null); continue; }}
                    let sum = 0; for (let j = 0; j < period; j++) sum += data[i - j];
                    sma.push(sum / period);
                }}
                return sma;
            }}

            function calcRSI(data, period = 14) {{
                let rsi = [], gains = 0, losses = 0;
                for (let i = 1; i < data.length; i++) {{
                    let diff = data[i] - data[i - 1];
                    if (diff >= 0) gains += diff; else losses -= diff;
                    if (i >= period) {{
                        let rs = gains / (losses || 1);
                        rsi.push(100 - (100 / (1 + rs)));
                        gains = 0; losses = 0;
                    }} else {{ rsi.push(null); }}
                }}
                return [null, ...rsi];
            }}

            // ==========================================
            // LOGIKA AUTO-SWITCH (BINANCE -> INDODAX)
            // ==========================================
            async function fetchKlines() {{
                errorMsg.style.display = 'none';
                
                try {{
                    // 1. Coba Binance
                    if (state.source === 'binance') {{
                        const url = `https://api.binance.com/api/v3/klines?symbol=${{state.symbol}}USDT&interval=${{state.timeframe}}&limit=200`;
                        const response = await fetch(url);
                        if (!response.ok) throw new Error("Binance Blocked");
                        
                        const data = await response.json();
                        state.rawData = data.map(d => ({{ x: d[0], o: parseFloat(d[1]), h: parseFloat(d[2]), l: parseFloat(d[3]), c: parseFloat(d[4]) }}));
                        
                        sourceBadge.style.display = 'none';
                        pairLabel.textContent = `${{state.symbol}} / USDT`;
                        document.getElementById('assetName').textContent = state.symbol;
                        
                    }} else {{
                        throw new Error("Force Indodax");
                    }}
                }} catch (error) {{
                    // 2. Jika Binance Gagal, Switch ke Indodax
                    console.warn("Binance gagal, beralih ke Indodax...");
                    state.source = 'indodax';
                    sourceBadge.style.display = 'inline-block';
                    pairLabel.textContent = `${{state.symbol}} / IDR`;
                    
                    try {{
                        // Ambil TF Indodax yang sesuai
                        const tfMap = {{ '1m': '1', '5m': '5', '15m': '15', '1h': '60', '4h': '240', '1d': 'D' }};
                        state.indodaxTf = tfMap[state.timeframe] || '60';
                        
                        const url = `https://indodax.com/tradingview/history_v2?symbol=${{state.symbol.toLowerCase()}}idr&tf=${{state.indodaxTf}}&from=${{Math.floor(Date.now() / 1000) - 86400 * 7}}&to=${{Math.floor(Date.now() / 1000)}}`;
                        const response = await fetch(url);
                        if (!response.ok) throw new Error("Indodax Failed");
                        
                        const data = await response.json();
                        state.rawData = data.map(d => ({{ x: d.Time * 1000, o: parseFloat(d.Open), h: parseFloat(d.High), l: parseFloat(d.Low), c: parseFloat(d.Close) }}));
                    }} catch (err) {{
                        errorMsg.style.display = 'block';
                        return;
                    }}
                }}

                if (state.rawData.length === 0) {{
                    errorMsg.style.display = 'block';
                    return;
                }}

                // Render
                const labels = state.rawData.map(d => d.x);
                const closePrices = state.rawData.map(d => d.c);
                renderChart(labels, closePrices, state.rawData);
                
                // Hitung 24h Change
                const firstPrice = state.rawData[0].c;
                const lastPrice = state.rawData[state.rawData.length - 1].c;
                const changePercent = ((lastPrice - firstPrice) / firstPrice) * 100;
                updateHeader(lastPrice, changePercent);
            }}

            function updateHeader(lastPrice, changePercent = null) {{
                priceEl.textContent = formatMoney(lastPrice);
                if (changePercent !== null && !isNaN(changePercent)) {{
                    const isPos = changePercent >= 0;
                    changeEl.textContent = `${{isPos ? '+' : ''}}${{changePercent.toFixed(2)}}%`;
                    changeEl.className = `change-badge ${{isPos ? '' : 'negative'}}`;
                }} else {{
                    changeEl.textContent = `--%`;
                }}
            }}

            function renderChart(labels, dataPoints, ohlcData) {{
                if (state.chartInstance) state.chartInstance.destroy();
                const ctx = canvas.getContext('2d');
                let datasets = [];
                
                if (state.type === 'candlestick') {{
                    datasets.push({{ label: 'Price', data: ohlcData, color: {{ up: COLORS.green, down: COLORS.red, unchanged: COLORS.text }}, yAxisID: 'y' }});
                }} else {{
                    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                    gradient.addColorStop(0, COLORS.purpleFill); gradient.addColorStop(1, 'rgba(124, 58, 237, 0)');
                    datasets.push({{ label: 'Price', data: dataPoints, borderColor: COLORS.purple, borderWidth: 2, backgroundColor: state.type === 'area' ? gradient : 'transparent', fill: state.type === 'area', pointRadius: 0, yAxisID: 'y' }});
                }}

                if (document.getElementById('chkMA20').checked) datasets.push({{ label: 'MA 20', data: calcSMA(dataPoints, 20), borderColor: COLORS.ma20, borderWidth: 1.5, pointRadius: 0, fill: false, yAxisID: 'y' }});
                if (document.getElementById('chkMA50').checked) datasets.push({{ label: 'MA 50', data: calcSMA(dataPoints, 50), borderColor: COLORS.ma50, borderWidth: 1.5, pointRadius: 0, fill: false, yAxisID: 'y' }});
                if (document.getElementById('chkRSI').checked) datasets.push({{ label: 'RSI', data: calcRSI(dataPoints), borderColor: COLORS.rsi, borderWidth: 1.5, pointRadius: 0, fill: false, yAxisID: 'y_rsi' }});

                let scales = {{
                    x: {{ type: 'time', grid: {{ display: false }}, ticks: {{ color: COLORS.text }} }},
                    y: {{ position: 'right', grid: {{ color: COLORS.grid }}, ticks: {{ color: COLORS.text, callback: function(value) {{ return formatMoney(value); }} }} }}
                }};
                
                if (document.getElementById('chkRSI').checked) {{
                    scales.y_rsi = {{ position: 'left', min: 0, max: 100, grid: {{ display: false }}, ticks: {{ color: COLORS.text }}, title: {{ display: true, text: 'RSI', color: COLORS.text }} }};
                }}

                state.chartInstance = new Chart(ctx, {{
                    type: state.type === 'candlestick' ? 'candlestick' : 'line',
                    data: {{ labels: labels, datasets: datasets }},
                    options: {{
                        responsive: true, maintainAspectRatio: false, interaction: {{ mode: 'index', intersect: false }},
                        plugins: {{
                            legend: {{ display: true, position: 'top', align: 'end', labels: {{ boxWidth: 10, usePointStyle: true }} }},
                            tooltip: {{ callbacks: {{ label: function(c) {{ 
                                if(c.dataset.yAxisID === 'y_rsi') return `RSI: ${{c.raw ? c.raw.toFixed(2) : '-'}}`;
                                let val = c.raw.c || c.raw; 
                                return formatMoney(parseFloat(val)); 
                            }} }} }},
                            zoom: {{ pan: {{ enabled: true, mode: 'x' }}, zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, mode: 'x' }} }}
                        }},
                        scales: scales
                    }}
                }});
            }}

            document.querySelectorAll('.indicators input').forEach(chk => {{
                chk.addEventListener('change', () => {{
                    const labels = state.rawData.map(d => d.x);
                    const closePrices = state.rawData.map(d => d.c);
                    renderChart(labels, closePrices, state.rawData);
                }});
            }});

            document.getElementById('typeGroup').addEventListener('click', (e) => {{
                if (e.target.tagName === 'BUTTON') {{
                    document.querySelectorAll('#typeGroup button').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active'); state.type = e.target.dataset.type; fetchKlines();
                }}
            }});
            document.getElementById('timeframeGroup').addEventListener('click', (e) => {{
                if (e.target.tagName === 'BUTTON') {{
                    document.querySelectorAll('#timeframeGroup button').forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active'); state.timeframe = e.target.dataset.tf; fetchKlines();
                }}
            }});
            document.getElementById('resetZoom').addEventListener('click', () => {{ if (state.chartInstance) state.chartInstance.resetZoom(); }});
            canvas.addEventListener('dblclick', () => {{ if (state.chartInstance) state.chartInstance.resetZoom(); }});

            fetchKlines();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=False)