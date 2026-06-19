#!/usr/bin/env python3
"""Busca empresas en Panama por sector y exporta prospectos a CSV."""

from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
import requests
from ddgs import DDGS

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_CSV = BASE_DIR / "leads_prospeccion.csv"

SEARCH_QUERIES = [
    "distribuidora empresa Panama sitio web",
    "logistica transporte empresa Panama",
    "academia capacitacion Panama",
    "retail comercio Panama empresa",
    "facturacion electronica Odoo Panama empresa",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-PA,es;q=0.9",
}

SKIP_DOMAINS = (
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "wikipedia.org",
    "google.com",
    "duckduckgo.com",
    "reddit.com",
    "support.google.com",
)


def domain_allowed(url: str) -> bool:
    host = url.lower()
    return not any(blocked in host for blocked in SKIP_DOMAINS)


def search_web(query: str, max_results: int = 8) -> list[dict[str, str]]:
    results = DDGS().text(query, region="pa-es", max_results=max_results)
    leads: list[dict[str, str]] = []
    for item in results:
        url = (item.get("href") or "").strip().rstrip("/")
        title = (item.get("title") or "").strip()
        if not url or not title or not domain_allowed(url):
            continue
        leads.append(
            {
                "titulo": title,
                "url": url,
                "sector_busqueda": query,
                "resumen": (item.get("body") or "").strip(),
                "pais": "Panama",
                "origen": "scraper_panama",
            }
        )
    return leads


def detect_stack(url: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
    except requests.RequestException:
        return "no_accesible"

    html = response.text.lower()
    signals: list[str] = []
    if "wp-content" in html or "wordpress" in html:
        signals.append("wordpress")
    if "odoo" in html:
        signals.append("odoo")
    if re.search(r"joomla|drupal|magento", html):
        signals.append("cms_legacy")
    if "factura" in html or "facturacion electronica" in html:
        signals.append("menciona_fe")
    return ",".join(signals) if signals else "sin_senal"


def main() -> None:
    all_leads: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    print("Iniciando rastreo de prospectos en Panama...")
    for query in SEARCH_QUERIES:
        print(f"  -> Buscando: {query}")
        try:
            batch = search_web(query)
        except Exception as exc:  # noqa: BLE001 - CLI script
            print(f"    ! Error de busqueda: {exc}")
            continue

        for lead in batch:
            if lead["url"] in seen_urls:
                continue
            seen_urls.add(lead["url"])
            lead["stack_detectado"] = detect_stack(lead["url"])
            all_leads.append(lead)
            print(f"    + {lead['titulo'][:70]}")

        time.sleep(1)

    if not all_leads:
        print("No se encontraron leads. Reintenta mas tarde o ajusta las consultas.")
        return

    df = pd.DataFrame(all_leads)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"\nListo: {len(df)} prospectos guardados en {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
