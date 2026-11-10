"""Streamlit interactive client component for non-custodial browser wallet connectivity (EIP-1193 & Solana)."""

import json
import streamlit as st
from chainscope import ui


def render_web3_connector(
    dark_mode: bool = False,
    current_account: str | None = None,
    current_chain_id: str | None = "1",
) -> None:
    """Render the non-custodial Web3 wallet connector component."""
    palette = ui.get_theme_palette(dark_mode)
    
    html_markup = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          margin: 0;
          padding: 16px;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background: transparent;
          color: {palette["primary_text"]};
        }}
        .wallet-card {{
          background: {palette["card_surface"]};
          border: 1px solid {palette["card_border"]};
          border-radius: 16px;
          padding: 20px;
          box-shadow: {palette["card_shadow"]};
        }}
        .header {{
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }}
        .title {{
          font-weight: 700;
          font-size: 1.1rem;
          color: {palette["primary_text"]};
        }}
        .btn {{
          padding: 10px 18px;
          border-radius: 10px;
          font-weight: 600;
          font-size: 0.9rem;
          cursor: pointer;
          border: none;
          transition: all 0.2s;
        }}
        .btn-connect {{
          background: {palette.get("accent", "#7C3AED")};
          color: white;
        }}
        .btn-connect:hover {{
          opacity: 0.9;
        }}
        .btn-disconnect {{
          background: rgba(244, 63, 94, 0.15);
          color: #F43F5E;
          border: 1px solid rgba(244, 63, 94, 0.3);
        }}
        .status-badge {{
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.75rem;
          font-weight: 600;
        }}
        .status-connected {{
          background: rgba(16, 185, 129, 0.15);
          color: #10B981;
        }}
        .status-disconnected {{
          background: rgba(161, 161, 170, 0.15);
          color: {palette["secondary_text"]};
        }}
        .info-row {{
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid {palette["card_border"]};
          font-size: 0.85rem;
        }}
      </style>
    </head>
    <body>
      <div class="wallet-card">
        <div class="header">
          <div>
            <div class="title">Web3 Wallet Connection (Non-Custodial)</div>
            <div style="font-size:0.8rem; color:{palette['secondary_text']}; margin-top:2px;">
              MetaMask, Trust Wallet, Rabby, Coinbase Wallet & Solana
            </div>
          </div>
          <span id="statusBadge" class="status-badge status-disconnected">
            ● Belum Terhubung
          </span>
        </div>
        
        <div id="accountDetails" style="margin-bottom: 16px;">
          <div class="info-row">
            <span style="color:{palette['secondary_text']};">Provider Browser</span>
            <span id="detectedProvider" style="font-weight:600;">Mengecek wallet...</span>
          </div>
          <div class="info-row">
            <span style="color:{palette['secondary_text']};">Alamat Terkoneksi</span>
            <span id="walletAddress" style="font-family:monospace; font-weight:600;">—</span>
          </div>
          <div class="info-row">
            <span style="color:{palette['secondary_text']};">Jaringan (Chain ID)</span>
            <span id="networkName" style="font-weight:600;">—</span>
          </div>
        </div>

        <div style="display:flex; gap:10px;">
          <button id="btnConnect" class="btn btn-connect" onclick="connectWallet()">
            Hubungkan Wallet Browser
          </button>
          <button id="btnDisconnect" class="btn btn-disconnect" style="display:none;" onclick="disconnectWallet()">
            Putuskan Koneksi
          </button>
        </div>
      </div>

      <script>
        const statusBadge = document.getElementById('statusBadge');
        const detectedProvider = document.getElementById('detectedProvider');
        const walletAddress = document.getElementById('walletAddress');
        const networkName = document.getElementById('networkName');
        const btnConnect = document.getElementById('btnConnect');
        const btnDisconnect = document.getElementById('btnDisconnect');

        function checkProviders() {{
          if (window.ethereum) {{
            detectedProvider.innerText = 'EVM Provider Aktif (' + (window.ethereum.isMetaMask ? 'MetaMask' : 'EIP-1193') + ')';
          }} else if (window.solana) {{
            detectedProvider.innerText = 'Solana Provider Aktif (Phantom)';
          }} else {{
            detectedProvider.innerText = 'Tidak terdeteksi (Gunakan browser dengan ekstensi Web3)';
          }}
        }}

        async function connectWallet() {{
          if (window.ethereum) {{
            try {{
              const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
              const chainId = await window.ethereum.request({{ method: 'eth_chainId' }});
              const addr = accounts[0];
              updateUI(addr, parseInt(chainId, 16));
            }} catch (err) {{
              alert('Koneksi ditolak oleh pengguna: ' + err.message);
            }}
          }} else if (window.solana) {{
            try {{
              const resp = await window.solana.connect();
              updateUI(resp.publicKey.toString(), 'Solana');
            }} catch (err) {{
              alert('Koneksi Solana ditolak: ' + err.message);
            }}
          }} else {{
            alert('Tidak ditemukan wallet browser (seperti MetaMask, Trust Wallet, atau Phantom). Silakan instal ekstensi browser atau gunakan aplikasi mobile Web3.');
          }}
        }}

        function updateUI(account, network) {{
          walletAddress.innerText = account;
          networkName.innerText = network;
          statusBadge.className = 'status-badge status-connected';
          statusBadge.innerText = '● Terhubung';
          btnConnect.style.display = 'none';
          btnDisconnect.style.display = 'inline-block';
        }}

        function disconnectWallet() {{
          walletAddress.innerText = '—';
          networkName.innerText = '—';
          statusBadge.className = 'status-badge status-disconnected';
          statusBadge.innerText = '● Belum Terhubung';
          btnConnect.style.display = 'inline-block';
          btnDisconnect.style.display = 'none';
        }}

        checkProviders();
      </script>
    </body>
    </html>
    """
    st.components.v1.html(html_markup, height=230)
