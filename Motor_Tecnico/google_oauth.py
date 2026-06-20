#!/usr/bin/env python3
"""OAuth Google — Business Profile + YouTube (token compartido)."""

from __future__ import annotations

import os
import secrets
import urllib.parse
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, session
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("FLASK_SECRET") or "easytech-google-oauth-2026"
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://n8n.etsrv.site/google/callback")
SCOPES = os.getenv(
    "GOOGLE_SCOPES",
    "https://www.googleapis.com/auth/business.manage "
    "https://www.googleapis.com/auth/youtube "
    "https://www.googleapis.com/auth/youtube.upload",
)
_used_codes: set[str] = set()


def update_env(key: str, value: str) -> None:
    lines: list[str] = []
    found = False
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def access_token_from_refresh(refresh_token: str) -> str:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def discover_business_location(access_token: str) -> tuple[str | None, str | None]:
    """Devuelve (account_name, location_name) para APIs v1/v4."""
    headers = {"Authorization": f"Bearer {access_token}"}
    acc_resp = requests.get(
        "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
        headers=headers,
        timeout=30,
    )
    if not acc_resp.ok:
        return None, None
    accounts = acc_resp.json().get("accounts", [])
    if not accounts:
        return None, None
    account_name = accounts[0].get("name")  # accounts/123
    if not account_name:
        return None, None

    loc_resp = requests.get(
        f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations",
        headers=headers,
        params={"readMask": "name,title"},
        timeout=30,
    )
    if not loc_resp.ok:
        return account_name, None
    locations = loc_resp.json().get("locations", [])
    if not locations:
        return account_name, None
    return account_name, locations[0].get("name")


@app.get("/google/")
def google_home():
    err = request.args.get("error", "")
    refresh = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
    account = os.getenv("GOOGLE_BUSINESS_ACCOUNT_ID", "").strip()
    location = os.getenv("GOOGLE_BUSINESS_LOCATION_ID", "").strip()
    yt = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Google EasyTech</title>
<style>body{{font-family:Inter,sans-serif;max-width:680px;margin:40px auto;padding:0 20px;background:#3D3832;color:#F0EBE3}}
.btn{{display:block;background:#DD9750;color:#1A1310;padding:14px 24px;text-decoration:none;border-radius:10px;font-weight:600;margin:16px 0;text-align:center}}
.box{{background:#4A443D;border:1px solid #5E5850;padding:12px;border-radius:10px;margin:12px 0}}
.err{{background:#B85C4A33;border:1px solid #B85C4A;padding:12px;border-radius:10px}}
code{{background:#35302B;padding:2px 6px;border-radius:4px}}</style></head>
<body>
<h1>Conectar Google</h1>
<p>Business Profile + YouTube (un solo OAuth).</p>
{"<p class='err'>" + err + "</p>" if err else ""}
{"<div class='box'>Conectado.<br>Cuenta: " + account + "<br>Ubicacion: " + location + ("<br>YouTube: " + yt if yt else "") + "</div>" if refresh else ""}
<div class="box"><strong>Requisitos:</strong><br>
1. Proyecto en <a href="https://console.cloud.google.com/" style="color:#E6A766">Google Cloud Console</a><br>
2. APIs: Business Profile, YouTube Data API v3<br>
3. OAuth redirect: <code>{REDIRECT_URI}</code><br>
4. Variables: <code>GOOGLE_CLIENT_ID</code>, <code>GOOGLE_CLIENT_SECRET</code></div>
<a class="btn" href="/google/go">Autorizar Google</a>
<p><a href="https://n8n.etsrv.site/accio/dashboard/" style="color:#E6A766">Dashboard Accio</a></p>
</body></html>"""


@app.get("/google/go")
def google_go():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        return redirect("/google/?error=Falta+GOOGLE_CLIENT_ID+en+.env")
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session.modified = True
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


@app.get("/google/callback")
def google_callback():
    if request.args.get("error"):
        desc = request.args.get("error_description") or request.args.get("error")
        return redirect("/google/?error=" + urllib.parse.quote(desc))

    code = request.args.get("code")
    if not code:
        return redirect("/google/?error=Sin+codigo+de+Google")
    if code in _used_codes:
        return redirect("/google/?error=Codigo+ya+usado.+Reintenta+desde+/google/")
    _used_codes.add(code)

    expected = session.get("oauth_state")
    if expected and request.args.get("state") != expected:
        return redirect("/google/?error=Sesion+expirada")

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return redirect("/google/?error=Faltan+GOOGLE_CLIENT_ID+o+SECRET")

    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    if not token_resp.ok:
        return redirect("/google/?error=" + urllib.parse.quote(token_resp.text[:180]))

    data = token_resp.json()
    refresh = data.get("refresh_token")
    if refresh:
        update_env("GOOGLE_OAUTH_REFRESH_TOKEN", refresh)

    access = data.get("access_token", "")
    account_name, location_name = discover_business_location(access) if access else (None, None)
    if account_name:
        update_env("GOOGLE_BUSINESS_ACCOUNT_ID", account_name)
    if location_name:
        update_env("GOOGLE_BUSINESS_LOCATION_ID", location_name)

    yt_channel = None
    if access:
        yt_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "id,snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access}"},
            timeout=30,
        )
        if yt_resp.ok:
            items = yt_resp.json().get("items", [])
            if items:
                yt_channel = items[0].get("id")
                update_env("YOUTUBE_CHANNEL_ID", yt_channel)

    return f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>Google conectado</h1>
<p>Refresh token guardado en <code>.env</code>.</p>
<p>Cuenta GBP: <strong>{account_name or '—'}</strong></p>
<p>Ubicacion: <strong>{location_name or '—'}</strong></p>
<p>YouTube channel: <strong>{yt_channel or '—'}</strong></p>
<p><a href="/google/">Volver</a> · <a href="https://n8n.etsrv.site/accio/dashboard/">Dashboard</a></p>
</body></html>"""


@app.get("/google/status")
def google_status():
    return {
        "ok": True,
        "google": bool(os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()),
        "business_account": os.getenv("GOOGLE_BUSINESS_ACCOUNT_ID", ""),
        "business_location": os.getenv("GOOGLE_BUSINESS_LOCATION_ID", ""),
        "youtube": bool(os.getenv("YOUTUBE_CHANNEL_ID", "").strip()),
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("GOOGLE_OAUTH_PORT", "8094")))
