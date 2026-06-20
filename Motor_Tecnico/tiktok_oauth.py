#!/usr/bin/env python3
"""OAuth TikTok for Business — Content Posting API."""

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
app.secret_key = os.getenv("FLASK_SECRET") or "easytech-tiktok-oauth-2026"
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "https://n8n.etsrv.site/tiktok/callback")
SCOPES = os.getenv("TIKTOK_SCOPES", "user.info.basic,video.publish,video.upload")
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


@app.get("/tiktok/")
def tiktok_home():
    err = request.args.get("error", "")
    token = os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>TikTok EasyTech</title>
<style>body{{font-family:Inter,sans-serif;max-width:680px;margin:40px auto;padding:0 20px;background:#3D3832;color:#F0EBE3}}
.btn{{display:block;background:#DD9750;color:#1A1310;padding:14px 24px;text-decoration:none;border-radius:10px;font-weight:600;margin:16px 0;text-align:center}}
.box{{background:#4A443D;border:1px solid #5E5850;padding:12px;border-radius:10px;margin:12px 0}}
.err{{background:#B85C4A33;border:1px solid #B85C4A;padding:12px;border-radius:10px}}
code{{background:#35302B;padding:2px 6px;border-radius:4px}}</style></head>
<body>
<h1>Conectar TikTok</h1>
<p>Requiere app en <a href="https://developers.tiktok.com/" style="color:#E6A766">TikTok for Developers</a> con Content Posting API aprobada.</p>
{"<p class='err'>" + err + "</p>" if err else ""}
{"<div class='box'>Token guardado en .env</div>" if token else ""}
<div class="box">
Redirect URI: <code>{REDIRECT_URI}</code><br>
Variables: <code>TIKTOK_CLIENT_KEY</code>, <code>TIKTOK_CLIENT_SECRET</code>
</div>
<a class="btn" href="/tiktok/go">Autorizar TikTok</a>
<p><a href="https://n8n.etsrv.site/accio/dashboard/" style="color:#E6A766">Dashboard Accio</a></p>
</body></html>"""


@app.get("/tiktok/go")
def tiktok_go():
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    if not client_key:
        return redirect("/tiktok/?error=Falta+TIKTOK_CLIENT_KEY+en+.env")
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session.modified = True
    params = urllib.parse.urlencode(
        {
            "client_key": client_key,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "response_type": "code",
            "state": state,
        }
    )
    return redirect(f"https://www.tiktok.com/v2/auth/authorize/?{params}")


@app.get("/tiktok/callback")
def tiktok_callback():
    if request.args.get("error"):
        desc = request.args.get("error_description") or request.args.get("error")
        return redirect("/tiktok/?error=" + urllib.parse.quote(desc))

    code = request.args.get("code")
    if not code:
        return redirect("/tiktok/?error=Sin+codigo")
    if code in _used_codes:
        return redirect("/tiktok/?error=Codigo+ya+usado")
    _used_codes.add(code)

    expected = session.get("oauth_state")
    if expected and request.args.get("state") != expected:
        return redirect("/tiktok/?error=Sesion+expirada")

    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "").strip()
    if not client_key or not client_secret:
        return redirect("/tiktok/?error=Faltan+credenciales+TikTok")

    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    if not resp.ok:
        return redirect("/tiktok/?error=" + urllib.parse.quote(resp.text[:180]))

    data = resp.json()
    token_data = data.get("data") or data
    access = token_data.get("access_token") or token_data.get("access_token", "")
    if access:
        update_env("TIKTOK_ACCESS_TOKEN", access)
    refresh = token_data.get("refresh_token")
    if refresh:
        update_env("TIKTOK_REFRESH_TOKEN", refresh)

    return """<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>TikTok conectado</h1>
<p>Token guardado. Publisher en Fase D.8b cuando la app tenga Content Posting aprobado.</p>
<p><a href="/tiktok/">Volver</a> · <a href="https://n8n.etsrv.site/accio/dashboard/">Dashboard</a></p>
</body></html>"""


@app.get("/tiktok/status")
def tiktok_status():
    return {
        "ok": True,
        "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN", "").strip()),
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("TIKTOK_OAUTH_PORT", "8095")))
