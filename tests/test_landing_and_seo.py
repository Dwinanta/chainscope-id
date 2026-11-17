import os
from pathlib import Path
import pytest
import streamlit as st

from chainscope import landing_page


def test_robots_txt_exists_and_protects_private_routes():
    robots_path = Path("robots.txt")
    assert robots_path.exists(), "robots.txt must exist in project root"
    content = robots_path.read_text(encoding="utf-8")
    assert "User-agent: *" in content
    assert "Disallow: /admin" in content
    assert "Disallow: /app" in content
    assert "Sitemap: https://chainscope.id/sitemap.xml" in content


def test_sitemap_xml_exists_and_contains_valid_urls():
    sitemap_path = Path("sitemap.xml")
    assert sitemap_path.exists(), "sitemap.xml must exist in project root"
    content = sitemap_path.read_text(encoding="utf-8")
    assert "<?xml version=" in content
    assert "https://chainscope.id/" in content
    assert "#market-intelligence" in content
    assert "#ecosystem" in content


def test_render_seo_headers_public(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: rendered.append(html))

    landing_page.render_seo_headers(is_authenticated=False)

    html = "".join(rendered)
    assert "title>ChainScope ID | Platform Intelijen Keuangan" in html
    assert 'rel="canonical" href="https://chainscope.id"' in html
    assert 'property="og:title"' in html
    assert 'name="twitter:card"' in html
    assert "SoftwareApplication" in html
    assert "Dwinanta Capital" in html
    assert "FAQPage" in html


def test_render_seo_headers_authenticated_has_noindex(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: rendered.append(html))

    landing_page.render_seo_headers(is_authenticated=True)

    html = "".join(rendered)
    assert 'meta name="robots" content="noindex, nofollow, noarchive, nosnippet"' in html
    assert "SoftwareApplication" not in html


def test_render_institutional_footer_includes_5_columns_and_ecosystem(monkeypatch):
    rendered = []
    monkeypatch.setattr(st, "markdown", lambda html, **kwargs: rendered.append(html))

    landing_page.render_institutional_footer(dark_mode=True, is_authenticated=True)

    html = "".join(rendered)
    assert "PRODUK" in html
    assert "EKOSISTEM" in html
    assert "SUMBER DAYA" in html
    assert "LEGAL" in html
    assert "Dwinanta Capital" in html
    assert "DX Luxury" in html
    assert "PENGUNGKAPAN RISIKO INVESTASI" in html
