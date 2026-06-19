#!/usr/bin/env python3
"""Importa leads del CSV al CRM Odoo via XML-RPC (marketing_crm_integration)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import xmlrpc.client
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "leads_prospeccion.csv"
STAGE_NAME = "Nuevo - Marketing"
SOURCE_MAP = {
    "scraper_panama": "scraper_panama",
    "linkedin": "linkedin",
    "guia_fe": "guia_fe",
}

load_dotenv(BASE_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Falta variable de entorno: {name}")
    return value


def connect_odoo():
    url = require_env("ODOO_URL").rstrip("/")
    db = require_env("ODOO_DB")
    user = require_env("ODOO_USER")
    password = require_env("ODOO_PASSWORD")

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise SystemExit("No se pudo autenticar en Odoo. Revisa credenciales.")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return db, uid, password, models


def search_id(models, db, uid, password, model, domain, limit=1):
    ids = models.execute_kw(db, uid, password, model, "search", [domain], {"limit": limit})
    return ids[0] if ids else None


def lead_exists(models, db, uid, password, name: str, url: str) -> bool:
    domain = ["|", "|", ("name", "=", name), ("x_url_web", "=", url), ("description", "ilike", url)]
    return bool(search_id(models, db, uid, password, "crm.lead", domain))


def resolve_stage_id(models, db, uid, password):
    return search_id(models, db, uid, password, "crm.stage", [("name", "=", STAGE_NAME)])


def resolve_source_id(models, db, uid, password, origen: str):
    source_name = SOURCE_MAP.get(origen, origen)
    return search_id(models, db, uid, password, "utm.source", [("name", "=", source_name)])


def resolve_tag_ids(models, db, uid, password, origen: str):
    tag_name = SOURCE_MAP.get(origen, origen)
    tag_id = search_id(models, db, uid, password, "crm.tag", [("name", "=", tag_name)])
    return [tag_id] if tag_id else []


def infer_sector(row: dict) -> str:
    sector = str(row.get("sector_busqueda", "")).strip()
    if sector:
        return sector
    stack = str(row.get("stack_detectado", "")).strip()
    return stack or "general"


def import_leads() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"No existe {CSV_PATH}. Ejecuta primero scraper_panama.py")

    db, uid, password, models = connect_odoo()
    stage_id = resolve_stage_id(models, db, uid, password)
    df = pd.read_csv(CSV_PATH)
    created = 0
    skipped = 0

    for row in df.to_dict(orient="records"):
        name = str(row.get("titulo", "")).strip() or "Prospecto Panama"
        url = str(row.get("url", "")).strip()
        origen = str(row.get("origen", "scraper_panama")).strip()

        if lead_exists(models, db, uid, password, name, url):
            skipped += 1
            continue

        description = (
            f"URL: {url}\n"
            f"Sector busqueda: {row.get('sector_busqueda', '')}\n"
            f"Resumen: {row.get('resumen', '')}\n"
            f"Stack detectado: {row.get('stack_detectado', '')}\n"
            f"Origen: {origen}"
        )

        values = {
            "name": name,
            "description": description,
            "type": "opportunity",
            "x_url_web": url,
            "x_sector": infer_sector(row),
        }

        source_id = resolve_source_id(models, db, uid, password, origen)
        if source_id:
            values["source_id"] = source_id

        tag_ids = resolve_tag_ids(models, db, uid, password, origen)
        if tag_ids:
            values["tag_ids"] = [(6, 0, tag_ids)]

        if stage_id:
            values["stage_id"] = stage_id

        models.execute_kw(db, uid, password, "crm.lead", "create", [values])
        created += 1

    print(f"Odoo sync completado. Creados: {created}, omitidos: {skipped}")


if __name__ == "__main__":
    try:
        import_leads()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
