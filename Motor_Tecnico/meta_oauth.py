#!/usr/bin/env python3
"""OAuth Meta (Facebook + Instagram) -> guarda tokens en .env."""

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
GRAPH = "https://graph.facebook.com/v21.0"

load_dotenv(ENV_PATH)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("FLASK_SECRET") or "easytech-meta-oauth-fixed-secret-2026"
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

REDIRECT_URI = os.getenv("META_REDIRECT_URI", "https://n8n.etsrv.site/meta/callback")
SCOPES = os.getenv(
    "META_SCOPES",
    "pages_manage_posts,pages_read_engagement,pages_show_list,"
    "instagram_basic,instagram_content_publish,business_management",
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


def exchange_long_lived(short_token: str, app_id: str, app_secret: str) -> str:
    resp = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def resolve_page_and_ig(user_token: str, preferred_page_id: str = "") -> tuple[str, str, str | None]:
    resp = requests.get(
        f"{GRAPH}/me/accounts",
        params={
            "fields": "id,name,access_token,instagram_business_account",
            "access_token": user_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])
    if not pages:
        raise RuntimeError("No hay paginas de Facebook vinculadas a esta cuenta.")

    page = pages[0]
    if preferred_page_id:
        for candidate in pages:
            if str(candidate.get("id")) == preferred_page_id:
                page = candidate
                break

    page_id = str(page["id"])
    page_token = page["access_token"]
    ig_account = page.get("instagram_business_account") or {}
    ig_user_id = str(ig_account["id"]) if ig_account.get("id") else None
    return page_id, page_token, ig_user_id


@app.get("/meta/")
def meta_home():
    err = request.args.get("error", "")
    configured = bool(os.getenv("META_PAGE_ACCESS_TOKEN", "").strip())
    ig = os.getenv("META_IG_USER_ID", "").strip()
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>Meta EasyTech</title>
<style>body{{font-family:sans-serif;max-width:680px;margin:40px auto;padding:0 20px}}
.btn{{display:block;background:#1877f2;color:#fff;padding:14px 24px;text-decoration:none;border-radius:8px;font-weight:bold;margin:16px 0;text-align:center}}
.err{{background:#fee2e2;padding:12px;border-radius:8px;color:#991b1b}}
.box{{background:#f0fdf4;border:1px solid #86efac;padding:12px;border-radius:8px;margin:12px 0}}
.muted{{color:#64748b;font-size:.875rem}}</style></head>
<body>
<h1>Conectar Facebook + Instagram</h1>
{"<p class='err'>" + err + "</p>" if err else ""}
{"<div class='box'>Token guardado. Page ID: " + os.getenv("META_PAGE_ID","") + (" · IG: " + ig if ig else " · IG: no vinculado") + "</div>" if configured else ""}
<div class="box"><strong>Requisitos:</strong><br>
1. App en <a href="https://developers.facebook.com/apps/">Meta Developers</a><br>
2. Pagina de Facebook EasyTech<br>
3. Cuenta Instagram Business vinculada a la pagina<br>
4. Redirect URI: <code>{REDIRECT_URI}</code></div>
<a class="btn" href="/meta/go">Autorizar Meta (Facebook + Instagram)</a>
<p class="muted">Scopes: pages_manage_posts, instagram_content_publish, etc.</p>
<p><a href="https://n8n.etsrv.site/accio/dashboard/">Dashboard Accio</a></p>
</body></html>"""


@app.get("/meta/go")
def meta_go():
    app_id = os.getenv("META_APP_ID", "").strip()
    if not app_id:
        return redirect("/meta/?error=Falta+META_APP_ID+en+.env")
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session.modified = True
    params = urllib.parse.urlencode(
        {
            "client_id": app_id,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": SCOPES,
            "response_type": "code",
        }
    )
    return redirect(f"https://www.facebook.com/v21.0/dialog/oauth?{params}")


@app.get("/meta/callback")
def meta_callback():
    if request.args.get("error"):
        desc = request.args.get("error_description") or request.args.get("error")
        return redirect("/meta/?error=" + urllib.parse.quote(desc))

    code = request.args.get("code")
    if not code:
        return redirect("/meta/?error=Sin+codigo+de+Meta")

    if code in _used_codes:
        return redirect("/meta/?error=Codigo+ya+usado.+Abre+/meta/go+de+nuevo")
    _used_codes.add(code)

    expected = session.get("oauth_state")
    if expected and request.args.get("state") != expected:
        return redirect("/meta/?error=Sesion+expirada.+Reintenta+desde+/meta/")

    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        return redirect("/meta/?error=Faltan+META_APP_ID+o+META_APP_SECRET")

    token_resp = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
        timeout=30,
    )
    if not token_resp.ok:
        return redirect("/meta/?error=" + urllib.parse.quote(token_resp.text[:180]))

    short_token = token_resp.json()["access_token"]
    long_token = exchange_long_lived(short_token, app_id, app_secret)
    update_env("META_USER_ACCESS_TOKEN", long_token)

    preferred = os.getenv("META_PAGE_ID", "").strip()
    try:
        page_id, page_token, ig_user_id = resolve_page_and_ig(long_token, preferred)
    except RuntimeError as exc:
        return redirect("/meta/?error=" + urllib.parse.quote(str(exc)))

    update_env("META_PAGE_ID", page_id)
    update_env("META_PAGE_ACCESS_TOKEN", page_token)
    if ig_user_id:
        update_env("META_IG_USER_ID", ig_user_id)

    ig_msg = f"Instagram Business ID: {ig_user_id}" if ig_user_id else "Instagram no vinculado a la pagina."
    return f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>Meta conectado</h1>
<p>Facebook Page ID: <strong>{page_id}</strong></p>
<p>{ig_msg}</p>
<p>Tokens guardados en <code>.env</code>.</p>
<p><a href="/meta/">Volver</a> · <a href="https://n8n.etsrv.site/accio/dashboard/">Dashboard</a></p>
</body></html>"""


@app.get("/meta/status")
def meta_status():
    return {
        "ok": True,
        "facebook": bool(os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()),
        "instagram": bool(os.getenv("META_IG_USER_ID", "").strip()),
        "page_id": os.getenv("META_PAGE_ID", ""),
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("META_OAUTH_PORT", "8093")))
