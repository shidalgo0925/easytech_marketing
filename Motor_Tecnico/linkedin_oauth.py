#!/usr/bin/env python3
"""OAuth LinkedIn -> guarda token -> publica post pendiente."""

from __future__ import annotations

import os
import secrets
import subprocess
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
app.secret_key = os.getenv("FLASK_SECRET") or "easytech-linkedin-oauth-fixed-secret-2026"
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

REDIRECT_URI = os.getenv(
    "LINKEDIN_REDIRECT_URI", "https://n8n.etsrv.site/linkedin/callback"
)
_used_codes: set[str] = set()
SCOPES = os.getenv("LINKEDIN_SCOPES", "w_member_social")


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


def token_valid(access_token: str) -> bool:
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": "202506",
        },
        timeout=20,
    )
    return r.status_code not in (401, 403) or "REVOKED" not in r.text


def resolve_author_urn(access_token: str) -> str | None:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202506",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    for url in (
        "https://api.linkedin.com/v2/userinfo",
        "https://api.linkedin.com/rest/me",
        "https://api.linkedin.com/v2/me",
    ):
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.ok:
                data = r.json()
                pid = data.get("sub") or data.get("id")
                if pid:
                    return f"urn:li:person:{pid}"
        except requests.RequestException:
            pass
    existing = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    return existing or None


def run_publisher() -> tuple[bool, str]:
    pub = subprocess.run(
        [
            str(BASE_DIR / "venv/bin/python3"),
            str(BASE_DIR / "Motor_Tecnico/linkedin_publisher.py"),
            "--force",
        ],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR),
    )
    out = (pub.stdout or "") + (pub.stderr or "")
    ok = pub.returncode == 0 and "Publicado" in out
    return ok, out


def oauth_redirect(scopes: str):
    cid = session.get("client_id") or os.getenv("LINKEDIN_CLIENT_ID", "").strip()
    secret = session.get("client_secret") or os.getenv("LINKEDIN_CLIENT_SECRET", "").strip()
    if not cid or not secret:
        return redirect("/linkedin/?error=Faltan+credenciales")
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    session.modified = True
    params = urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": cid,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": scopes,
        }
    )
    return redirect(f"https://www.linkedin.com/oauth/v2/authorization?{params}")


def result_page(ok: bool, out: str) -> str:
    if "REVOKED_ACCESS_TOKEN" in out:
        return redirect("/linkedin/?error=Token+revocado.+Autoriza+de+nuevo+con+/linkedin/go")
    title = "Publicado en LinkedIn" if ok else "Error al publicar"
    return f"""<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>{title}</h1>
<pre style="background:#f4f4f4;padding:16px;white-space:pre-wrap">{out}</pre>
<p><a href="https://www.linkedin.com/in/easytech-services-209b45373">Ver perfil</a></p>
<p><a href="/linkedin/go">Re-autorizar</a></p>
</body></html>"""


@app.get("/linkedin/")
def linkedin_home():
    err = request.args.get("error", "")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><title>LinkedIn EasyTech</title>
<style>body{{font-family:sans-serif;max-width:640px;margin:40px auto;padding:0 20px}}
.btn{{display:block;background:#0a66c2;color:#fff;padding:14px 24px;text-decoration:none;border-radius:8px;font-weight:bold;margin:16px 0;text-align:center}}
.err{{background:#fee2e2;padding:12px;border-radius:8px;color:#991b1b}}
.box{{background:#f0fdf4;border:1px solid #86efac;padding:12px;border-radius:8px;margin:12px 0}}</style></head>
<body>
<h1>Publicar Post #1 en LinkedIn</h1>
{"<p class='err'>" + err + "</p>" if err else ""}
<div class="box"><strong>Paso 1 (obligatorio):</strong> En LinkedIn Developers → Products → activa<br>
<strong>Sign In with LinkedIn using OpenID Connect</strong></div>
<a class="btn" href="/linkedin/go-openid">Paso 2: Autorizar y publicar</a>
<p><small>Solo funciona despues del Paso 1. Si Sign In no esta activo, dara error openid.</small></p>
<p><a href="/linkedin/go">Alternativa sin OpenID (solo Share on LinkedIn)</a></p>
</body></html>"""


@app.get("/linkedin/go")
def linkedin_go():
    session["client_id"] = os.getenv("LINKEDIN_CLIENT_ID", "").strip()
    session["client_secret"] = os.getenv("LINKEDIN_CLIENT_SECRET", "").strip()
    session.modified = True
    return oauth_redirect(SCOPES)


@app.get("/linkedin/go-openid")
def linkedin_go_openid():
    session["client_id"] = os.getenv("LINKEDIN_CLIENT_ID", "").strip()
    session["client_secret"] = os.getenv("LINKEDIN_CLIENT_SECRET", "").strip()
    session.modified = True
    return oauth_redirect("w_member_social openid profile")


@app.get("/linkedin/callback")
def linkedin_callback():
    if request.args.get("error"):
        desc = request.args.get("error_description") or request.args.get("error")
        return redirect("/linkedin/?error=" + urllib.parse.quote(desc))

    code = request.args.get("code")
    if not code:
        return redirect("/linkedin/?error=Sin+codigo+de+LinkedIn")

    if code in _used_codes:
        return redirect("/linkedin/?error=Espera+5+segundos+y+usa+/linkedin/go-openid+de+nuevo")
    _used_codes.add(code)

    expected = session.get("oauth_state")
    if expected and request.args.get("state") != expected:
        return redirect("/linkedin/?error=Sesion+expirada.+Reintenta+desde+/linkedin/")

    cid = session.get("client_id") or os.getenv("LINKEDIN_CLIENT_ID")
    secret = session.get("client_secret") or os.getenv("LINKEDIN_CLIENT_SECRET")
    token_resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": cid,
            "client_secret": secret,
        },
        timeout=30,
    )
    if not token_resp.ok:
        return redirect("/linkedin/?error=" + urllib.parse.quote(token_resp.text[:180]))

    access_token = token_resp.json()["access_token"]
    update_env("LINKEDIN_ACCESS_TOKEN", access_token)

    author_urn = resolve_author_urn(access_token)
    if not author_urn:
        return """<!DOCTYPE html><html><body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>Token OK — activa Sign In</h1>
<p>Activa <strong>Sign In with LinkedIn using OpenID Connect</strong> en Products y abre:</p>
<p><a href="/linkedin/go-openid">/linkedin/go-openid</a></p>
<p>No uses el numero de la URL del perfil — no es el Person ID real.</p>
</body></html>"""

    update_env("LINKEDIN_AUTHOR_URN", author_urn)
    ok, out = run_publisher()
    return result_page(ok, out)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8091)
