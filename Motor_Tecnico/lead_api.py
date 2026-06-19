#!/usr/bin/env python3
"""API ligera: formulario guia FE -> crm.lead en Odoo."""

from __future__ import annotations

import os
import xmlrpc.client
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
STAGE_NAME = "Nuevo - Marketing"


def odoo_client():
    url = os.environ["ODOO_URL"].rstrip("/")
    db = os.environ["ODOO_DB"]
    user = os.environ["ODOO_USER"]
    password = os.environ["ODOO_PASSWORD"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise RuntimeError("Auth Odoo fallida")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return db, uid, password, models


def search_id(models, db, uid, password, model, domain):
    ids = models.execute_kw(db, uid, password, model, "search", [domain], {"limit": 1})
    return ids[0] if ids else None


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/lead")
def create_lead():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or data.get("nombre") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or data.get("telefono") or data.get("whatsapp") or "").strip()
    company = (data.get("company") or data.get("empresa") or "").strip()

    if not name or not email:
        return jsonify({"ok": False, "error": "Nombre y email son obligatorios"}), 400

    lead_name = company or name
    description = (
        f"Lead magnet: Guia Facturacion Electronica Panama\n"
        f"Nombre: {name}\n"
        f"Email: {email}\n"
        f"Telefono/WhatsApp: {phone}\n"
        f"Empresa: {company}\n"
        f"Origen: guia_fe"
    )

    db, uid, password, models = odoo_client()

    if search_id(models, db, uid, password, "crm.lead", [("email_from", "=", email)]):
        return jsonify({"ok": True, "message": "Ya registrado", "duplicate": True})

    values = {
        "name": lead_name,
        "contact_name": name,
        "email_from": email,
        "phone": phone,
        "description": description,
        "type": "opportunity",
        "x_sector": "facturacion_electronica",
    }

    source_id = search_id(models, db, uid, password, "utm.source", [("name", "=", "guia_fe")])
    if source_id:
        values["source_id"] = source_id

    tag_id = search_id(models, db, uid, password, "crm.tag", [("name", "=", "guia_fe")])
    if tag_id:
        values["tag_ids"] = [(6, 0, [tag_id])]

    stage_id = search_id(models, db, uid, password, "crm.stage", [("name", "=", STAGE_NAME)])
    if stage_id:
        values["stage_id"] = stage_id

    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [values])
    return jsonify({"ok": True, "lead_id": lead_id})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
