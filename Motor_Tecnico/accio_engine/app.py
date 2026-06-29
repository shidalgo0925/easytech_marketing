#!/usr/bin/env python3
"""Accio Marketing Engine — API REST orquestador multi-tenant."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, redirect, request, send_from_directory, session
from werkzeug.middleware.proxy_fix import ProxyFix

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
EMACCION_LANDING_DIR = STATIC_DIR / "emaccion"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.accio_engine import audit_service, auth_service, dashboard_data, executor, files_api, knowledge_api, marketing_app, queue_store, rbac, settings_center, tenant_profile, tenant_provisioning, tenant_secrets  # noqa: E402
from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_api import register_marketing_plan_api  # noqa: E402
from Motor_Tecnico.accio_engine.memory_api import register_memory_api  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_api import register_company_brain_api  # noqa: E402
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, TenantNotFoundError, list_tenants, resolve_tenant  # noqa: E402

ACCIO_ENV = load_accio_env(BASE_DIR)

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
_api_key = os.getenv("ACCIO_API_KEY", "").strip()
app.secret_key = os.getenv("ACCIO_SESSION_SECRET", hashlib.sha256(_api_key.encode() or b"accio").hexdigest())
# Tras Cloudflare el origen puede ser HTTP; Secure=false evita que el navegador ignore la cookie.
app.config["SESSION_COOKIE_SECURE"] = os.getenv("ACCIO_SESSION_SECURE", "false").lower() in ("1", "true", "yes")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 14

DASHBOARD_ASSETS = {
    "accio-design.css",
    "accio-logomark.svg",
    "em-logomark.svg",
    "em-accion-app-icon.svg",
    "em-accion-app-icon-1024.png",
    "accio-wordmark.svg",
    "accio-logo-horizontal.svg",
    "accio-og.svg",
    "palette-preview.html",
    "login.html",
    "empresas.html",
    "plan_slice.css",
    "plan_slice.js",
}

CRITICAL_CSS = """
body{margin:0;font-family:system-ui,sans-serif;background:#eef6f0;color:#1a4a2e;min-height:100vh}
.hidden{display:none!important}
"""


def _external_base() -> str:
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    if proto not in ("http", "https"):
        proto = "https"
    host = request.headers.get("X-Forwarded-Host", request.host)
    return f"{proto}://{host}"


def _static_asset_url(name: str) -> str:
    path = STATIC_DIR / name
    ver = int(path.stat().st_mtime) if path.is_file() else 1
    return f"{_external_base()}/accio/static/{name}?v={ver}"


def _valid_api_key(token: str, tenant_id: str = DEFAULT_TENANT) -> bool:
    if not token:
        return False
    if _api_key and token == _api_key:
        return True
    tenant_key = tenant_secrets.get_secret(tenant_id, "platform", "accio_api_key")
    return bool(tenant_key and token == tenant_key)


def _session_role(tenant_id: str) -> str:
    if session.get("auth_method") == "api_key":
        return "admin"
    if session.get("global_role") == "super_admin":
        return "super_admin"
    user_id = session.get("user_id")
    if user_id:
        role = auth_service.get_tenant_role(user_id, tenant_id, session.get("global_role"))
        if role:
            return role
    role = session.get("role")
    if role and session.get("tenant_id") == tenant_id:
        return role
    return "viewer"


def _user_can_access_tenant(tenant_id: str) -> bool:
    if not session.get("accio_auth"):
        return False
    if session.get("auth_method") == "api_key":
        return True
    return auth_service.can_access_tenant(
        session.get("user_id", ""),
        tenant_id,
        session.get("global_role"),
    )


def _is_platform_admin() -> bool:
    return session.get("global_role") == "super_admin"


def _platform_admin_required():
    if session.get("auth_method") == "api_key":
        return None
    if _is_platform_admin():
        return None
    return jsonify({"ok": False, "error": "Requiere super administrador de plataforma"}), 403


def _tenant_target_access_required(target_id: str):
    if not _user_can_access_tenant(target_id):
        return jsonify({"ok": False, "error": "Sin acceso a este tenant"}), 403
    return None


def _allowed_tenant_rows() -> list[dict[str, str]]:
    if session.get("auth_method") == "api_key":
        return [{"id": t.tenant_id, "name": t.display_name} for t in list_tenants()]
    allowed = set(auth_service.allowed_tenants(session.get("user_id", ""), session.get("global_role")))
    return [
        {"id": t.tenant_id, "name": t.display_name}
        for t in list_tenants()
        if t.tenant_id in allowed
    ]


def _sync_session_tenant(tenant_id: str) -> None:
    if session.get("auth_method") != "user":
        session["tenant_id"] = tenant_id
        return
    role = auth_service.get_tenant_role(session.get("user_id", ""), tenant_id, session.get("global_role"))
    if role:
        session["tenant_id"] = tenant_id
        session["role"] = role


def _check_request_permission(tenant_id: str) -> tuple[bool, str | None]:
    perm = rbac.permission_for_request(request.method, request.path, tenant_id)
    if not perm:
        return True, None
    role = _session_role(tenant_id)
    if rbac.has_permission(role, perm, tenant_id):
        return True, None
    return False, perm


def require_api_key(_func=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            tenant_id = kwargs.get("tenant_id") or request.headers.get("X-Accio-Tenant", DEFAULT_TENANT)
            if session.get("accio_auth"):
                if not _user_can_access_tenant(tenant_id):
                    return jsonify({"ok": False, "error": "Sin acceso a este tenant"}), 403
                allowed, perm = _check_request_permission(tenant_id)
                if not allowed:
                    return jsonify({"ok": False, "error": f"Permiso denegado: {perm}"}), 403
                return view(*args, **kwargs)
            if not _api_key and not tenant_secrets.get_secret(tenant_id, "platform", "accio_api_key"):
                return jsonify({"ok": False, "error": "ACCIO_API_KEY no configurada"}), 503
            auth = request.headers.get("Authorization", "")
            token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else request.headers.get("X-Accio-Key", "")
            if not _valid_api_key(token, tenant_id):
                return jsonify({"ok": False, "error": "No autorizado"}), 401
            # Bearer API key (cron, Accio Work): permisos de automatización
            return view(*args, **kwargs)

        return wrapped

    if _func is not None:
        return decorator(_func)
    return decorator


def _tenant_or_404(tenant_id: str):
    try:
        return resolve_tenant(tenant_id), None
    except TenantNotFoundError as exc:
        return None, str(exc)


def _requested_app_id(tenant_id: str) -> str:
    body = request.get_json(silent=True) if request.method in ("POST", "PATCH", "PUT") else {}
    if body is None:
        body = {}
    raw = (
        request.args.get("app_id")
        or request.headers.get("X-Accio-App")
        or (body.get("app_id") if isinstance(body, dict) else None)
        or ""
    )
    raw = str(raw).strip()
    if not raw:
        return marketing_app.default_app_id(tenant_id)
    try:
        return marketing_app.normalize_app_id(raw)
    except marketing_app.AppNotFoundError:
        return marketing_app.default_app_id(tenant_id)


def _serve_dashboard_asset(asset: str):
    if asset not in DASHBOARD_ASSETS:
        return jsonify({"ok": False, "error": "Asset no permitido"}), 404
    if asset.endswith(".svg"):
        mimetype = "image/svg+xml"
    elif asset.endswith(".png"):
        mimetype = "image/png"
    elif asset.endswith(".html"):
        mimetype = "text/html"
    else:
        mimetype = "text/css"
    resp = send_from_directory(app.static_folder, asset, mimetype=mimetype)
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.get("/accio/static/<asset>")
def static_assets(asset: str):
    # Ignorar query string cache-bust (?v=...)
    name = asset.split("?")[0]
    return _serve_dashboard_asset(name)


@app.get("/accio/health")
def health():
    return jsonify({"ok": True, "service": "accio_engine", "multi_tenant": True, "env": ACCIO_ENV})


@app.get("/accio/tenants")
@require_api_key
def tenants_list():
    allowed_ids = {row["id"] for row in _allowed_tenant_rows()}
    return jsonify(
        {
            "ok": True,
            "tenants": [
                {"tenant_id": t.tenant_id, "display_name": t.display_name, "crm_target": t.crm_target}
                for t in list_tenants()
                if t.tenant_id in allowed_ids
            ],
        }
    )


@app.post("/accio/auth/login")
def auth_login():
    body = request.get_json(silent=True) or {}
    tenant_id = (body.get("tenant_id") or DEFAULT_TENANT).strip().lower()
    token = (body.get("api_key") or "").strip()
    email = (body.get("email") or body.get("username") or body.get("user") or "").strip()
    password = body.get("password") or ""

    if token:
        if not _valid_api_key(token, tenant_id):
            return jsonify({"ok": False, "error": "API key inválida"}), 401
        session["accio_auth"] = True
        session["tenant_id"] = tenant_id
        session["auth_method"] = "api_key"
        session["user_id"] = "api_key"
        session["role"] = "admin"
        session["user_name"] = "API Key"
        return jsonify({"ok": True, "tenant_id": tenant_id, "role": "admin", "auth_method": "api_key"})

    user = auth_service.authenticate(email, password, tenant_id)
    if not user:
        audit_service.log_event(tenant_id, "login_failed", actor=email, category="auth", success=False)
        return jsonify({"ok": False, "error": "Usuario o contraseña incorrectos"}), 401
    _establish_user_session(user, tenant_id)
    audit_service.log_event(
        tenant_id,
        "login",
        actor=user["email"],
        category="auth",
        detail={"role": user["role"]},
    )
    return jsonify(
        {
            "ok": True,
            "tenant_id": tenant_id,
            "role": user["role"],
            "user_id": user["user_id"],
            "name": user["name"],
            "auth_method": "user",
        }
    )


@app.get("/accio/auth/status")
def auth_status():
    tenant_id = (
        (request.args.get("tenant_id") or "").strip().lower()
        or session.get("tenant_id")
        or DEFAULT_TENANT
    )
    role = _session_role(tenant_id) if session.get("accio_auth") else None
    if session.get("accio_auth") and role:
        session["tenant_id"] = tenant_id
        session["role"] = role
    return jsonify(
        {
            "ok": True,
            "authenticated": bool(session.get("accio_auth")),
            "tenant_id": tenant_id,
            "role": role or session.get("role"),
            "user_id": session.get("user_id"),
            "name": session.get("user_name"),
            "auth_method": session.get("auth_method"),
            "permissions": sorted(auth_service.role_permissions(role or session.get("role", "viewer"))),
            "global_role": session.get("global_role"),
        }
    )


def _company_rows_for_session() -> list[dict[str, str]]:
    rows = _allowed_tenant_rows()
    reg = {t.tenant_id: t for t in list_tenants()}
    out: list[dict[str, str]] = []
    for row in rows:
        tid = row["id"]
        tenant = reg.get(tid)
        crm = tenant.crm_target if tenant else ""
        crm_labels = {"odoo": "Odoo", "en1": "EN1", "hubspot": "HubSpot", "zoho": "Zoho", "api": "API"}
        out.append(
            {
                "id": tid,
                "name": row["name"],
                "subdomain": tenant.subdomain if tenant else "",
                "crm_target": crm,
                "crm_label": crm_labels.get(crm, crm.upper() if crm else ""),
            }
        )
    return out


def _enter_empresa_session(tenant_id: str) -> str | None:
    """Fija tenant activo en sesión. Devuelve mensaje de error o None si OK."""
    if not _user_can_access_tenant(tenant_id):
        return "Sin acceso a este tenant"
    role = _session_role(tenant_id)
    session["tenant_id"] = tenant_id
    session["role"] = role
    _sync_session_tenant(tenant_id)
    return None


def _tenant_home_url(tenant_id: str) -> str:
    """Home post-login: módulo Plan (Inicio unificado)."""
    return f"/accio/plan/{tenant_id.strip().lower()}/"


def _tenant_dashboard_url(tenant_id: str) -> str:
    """Vista operativa legacy (Resumen, conectores, configuración avanzada)."""
    return f"/accio/dashboard/{tenant_id.strip().lower()}/"


def _redirect_for_next_or_home(nxt: str | None) -> Response | None:
    """Respeta ?next= si apunta a dashboard o plan de un tenant permitido."""
    nxt = (nxt or "").strip()
    for prefix in ("/accio/dashboard/", "/accio/plan/"):
        if not nxt.startswith(prefix):
            continue
        parts = [p for p in nxt.rstrip("/").split("/") if p]
        if len(parts) < 3:
            continue
        tid = parts[2].lower()
        if not _user_can_access_tenant(tid):
            continue
        err = _enter_empresa_session(tid)
        if err:
            continue
        return redirect(nxt, code=302)
    return None


def _redirect_after_login(user: dict | None = None) -> Response:
    hit = _redirect_for_next_or_home(request.args.get("next"))
    if hit:
        return hit
    companies = _company_rows_for_session()
    if len(companies) == 1:
        err = _enter_empresa_session(companies[0]["id"])
        if err:
            return _render_login_platform(error=err)
        return redirect(_tenant_home_url(companies[0]["id"]), code=302)
    preferred = next((c for c in companies if c["id"] == DEFAULT_TENANT), None)
    if preferred:
        err = _enter_empresa_session(preferred["id"])
        if not err:
            return redirect(_tenant_home_url(preferred["id"]), code=302)
    return redirect("/accio/empresas/", code=302)


@app.get("/accio/auth/empresas")
def auth_empresas_list():
    if not session.get("accio_auth"):
        return jsonify({"ok": False, "authenticated": False}), 401
    return jsonify(
        {
            "ok": True,
            "authenticated": True,
            "name": session.get("user_name"),
            "global_role": session.get("global_role"),
            "companies": _company_rows_for_session(),
        }
    )


@app.post("/accio/auth/empresas/<tenant_id>/entrar")
def auth_empresas_enter(tenant_id: str):
    if not session.get("accio_auth"):
        return jsonify({"ok": False, "error": "No autenticado"}), 401
    err = _enter_empresa_session(tenant_id)
    if err:
        return jsonify({"ok": False, "error": err}), 403
    return jsonify({"ok": True, "redirect": _tenant_home_url(tenant_id)})


@app.post("/accio/auth/logout")
def auth_logout():
    session.clear()
    return jsonify({"ok": True, "redirect": "/accio/producto/"})


def _establish_user_session(user: dict, tenant_id: str) -> None:
    session.permanent = True
    session["accio_auth"] = True
    session["tenant_id"] = tenant_id
    session["auth_method"] = "user"
    session["user_id"] = user["user_id"]
    session["role"] = user["role"]
    session["global_role"] = user.get("global_role")
    session["user_name"] = user["name"]


def _render_login_platform(*, error: str | None = None) -> Response:
    html_path = Path(app.static_folder) / "login.html"
    html = html_path.read_text(encoding="utf-8")
    css_url = _static_asset_url("accio-design.css")
    icon_url = _static_asset_url("em-logomark.svg")
    html = html.replace('href="/accio/static/em-logomark.svg"', f'href="{icon_url}"', 1)
    html = html.replace('href="/accio/static/accio-design.css"', f'href="{css_url}"', 1)
    inject = (
        '<script>window.__ACCIO_PLATFORM_LOGIN__=true;'
        'window.__ACCIO_TENANT_NAME__="Plataforma EMAccion";</script>'
    )
    html = html.replace("</head>", inject + "\n</head>", 1)
    if error:
        safe_err = error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = html.replace(
            '<p class="login-error hidden" id="loginError" role="alert"></p>',
            f'<p class="login-error" id="loginError" role="alert">{safe_err}</p>',
        )
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


def _render_empresas_page() -> Response:
    html_path = Path(app.static_folder) / "empresas.html"
    html = html_path.read_text(encoding="utf-8")
    css_url = _static_asset_url("accio-design.css")
    icon_url = _static_asset_url("em-logomark.svg")
    html = html.replace('href="/accio/static/em-logomark.svg"', f'href="{icon_url}"', 1)
    html = html.replace('href="/accio/static/accio-design.css"', f'href="{css_url}"', 1)
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


def _render_login(tenant_id: str, *, error: str | None = None) -> Response:
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    html_path = Path(app.static_folder) / "login.html"
    html = html_path.read_text(encoding="utf-8")
    css_url = _static_asset_url("accio-design.css")
    icon_url = _static_asset_url("em-logomark.svg")
    html = html.replace('href="/accio/static/em-logomark.svg"', f'href="{icon_url}"', 1)
    html = html.replace('href="/accio/static/accio-design.css"', f'href="{css_url}"', 1)
    branding = tenant_profile.branding_css(tenant_id)
    redirect_to = request.args.get("next") or _tenant_home_url(tenant_id)
    inject = (
        f"<style>{branding}</style>"
        f'<script>window.__ACCIO_TENANT__={json.dumps(tenant_id)};'
        f"window.__ACCIO_TENANT_NAME__={json.dumps(tenant.display_name)};"
        f"window.__ACCIO_REDIRECT__={json.dumps(redirect_to)};</script>"
    )
    html = html.replace("</head>", inject + "\n</head>", 1)
    if error:
        safe_err = error.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = html.replace(
            '<p class="login-error hidden" id="loginError" role="alert"></p>',
            f'<p class="login-error" id="loginError" role="alert">{safe_err}</p>',
        )
    return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store, no-cache, must-revalidate"})


def _dashboard_login_url(tenant_id: str = "") -> str:
    return "/accio/login/"


def _render_dashboard(tenant_id: str) -> Response:
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    html_path = Path(app.static_folder) / "dashboard.html"
    html = html_path.read_text(encoding="utf-8")
    tenants_js = json.dumps(_allowed_tenant_rows(), ensure_ascii=False)
    css_url = _static_asset_url("accio-design.css")
    icon_url = _static_asset_url("em-logomark.svg")
    html = html.replace('href="/accio/static/em-logomark.svg"', f'href="{icon_url}"', 1)
    html = html.replace('href="/accio/static/accio-design.css"', f'href="{css_url}"', 1)
    branding = tenant_profile.branding_css(tenant_id)
    session_role = _session_role(tenant_id) if session.get("accio_auth") else None
    global_role = session.get("global_role")
    from Motor_Tecnico.accio_engine import auth_service as _auth

    perms = sorted(_auth.role_permissions(session_role or "viewer"))
    inject = (
        f"<style>{CRITICAL_CSS}{branding}</style>"
        f'<script>window.__ACCIO_TENANT__={json.dumps(tenant_id)};'
        f"window.__ACCIO_TENANTS__={tenants_js};window.__ACCIO_ENV__={json.dumps(ACCIO_ENV)};"
        f"window.__ACCIO_EMPRESA_NAME__={json.dumps(tenant.display_name)};"
        f"window.__ACCIO_SESSION_ROLE__={json.dumps(session_role)};"
        f"window.__ACCIO_GLOBAL_ROLE__={json.dumps(global_role)};"
        f"window.__ACCIO_PERMISSIONS__={json.dumps(perms)};</script>"
    )
    html = html.replace("</head>", inject + "\n</head>", 1)
    html = html.replace(
        "<title>EMAccion — Command Center</title>",
        f"<title>{tenant.display_name} — EMAccion</title>",
    )
    return Response(
        html,
        mimetype="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )


def _render_plan_slice(tenant_id: str) -> Response:
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    html_path = Path(app.static_folder) / "plan_slice.html"
    html = html_path.read_text(encoding="utf-8")
    css_design = _static_asset_url("accio-design.css")
    css_slice = _static_asset_url("plan_slice.css")
    js_slice = _static_asset_url("plan_slice.js")
    profile = tenant_profile.load_profile(tenant_id)
    branding_data = profile.get("branding") or tenant_profile.DEFAULT_BRANDING
    logo_url = branding_data.get("logo_url") or _static_asset_url("em-logomark.svg").split("?")[0]
    if logo_url.startswith("/accio/static/"):
        icon_url = _static_asset_url(logo_url.split("/")[-1])
    else:
        icon_url = logo_url
    html = html.replace('href="/accio/static/em-logomark.svg"', f'href="{icon_url}"', 1)
    html = html.replace('href="/accio/static/accio-design.css"', f'href="{css_design}"', 1)
    html = html.replace('href="/accio/static/plan_slice.css"', f'href="{css_slice}"', 1)
    html = html.replace('src="/accio/static/plan_slice.js"', f'src="{js_slice}"', 1)
    branding = tenant_profile.branding_css(tenant_id)
    tenants_js = json.dumps(_allowed_tenant_rows(), ensure_ascii=False)
    user_name = session.get("user_name") or session.get("user_id") or "Administrador"
    app_id = _requested_app_id(tenant_id)
    session_role = _session_role(tenant_id) if session.get("accio_auth") else None
    branding_js = json.dumps(
        {
            "logo_url": branding_data.get("logo_url", "/accio/static/em-logomark.svg"),
            "primary_color": branding_data.get("primary_color"),
            "accent_color": branding_data.get("accent_color"),
            "display_name": tenant.display_name,
        },
        ensure_ascii=False,
    )
    inject = (
        f"<style>{CRITICAL_CSS}{branding}</style>"
        f"<script>window.__ACCIO_TENANT__={json.dumps(tenant_id)};"
        f"window.__ACCIO_TENANTS__={tenants_js};"
        f"window.__ACCIO_EMPRESA_NAME__={json.dumps(tenant.display_name)};"
        f"window.__ACCIO_USER_NAME__={json.dumps(str(user_name))};"
        f"window.__ACCIO_APP__={json.dumps(app_id)};"
        f"window.__ACCIO_BRANDING__={branding_js};"
        f"window.__ACCIO_SESSION_ROLE__={json.dumps(session_role)};</script>"
    )
    html = html.replace("</head>", inject + "\n</head>", 1)
    html = html.replace(
        "<title>EM+Acción — Plan de Marketing</title>",
        f"<title>{tenant.display_name} — EM+Acción</title>",
    )
    return Response(
        html,
        mimetype="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )


@app.get("/accio/login")
def login_redirect_root():
    if session.get("accio_auth"):
        return redirect("/accio/empresas/", code=302)
    return redirect("/accio/login/", code=302)


@app.route("/accio/login/", methods=["GET", "POST"], strict_slashes=False)
def login_page_platform():
    if request.method == "POST":
        login = (request.form.get("username") or request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        if not login or not password:
            return _render_login_platform(error="Usuario y contraseña son obligatorios.")
        user = auth_service.authenticate_user(login, password)
        if not user:
            return _render_login_platform(error="Usuario o contraseña incorrectos.")
        session.permanent = True
        session["accio_auth"] = True
        session["auth_method"] = "user"
        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]
        session["global_role"] = user.get("global_role")
        audit_service.log_event(
            DEFAULT_TENANT,
            "login",
            actor=user["email"],
            category="auth",
            detail={"method": "platform"},
        )
        return _redirect_after_login(user)
    if session.get("accio_auth"):
        return redirect("/accio/empresas/", code=302)
    return _render_login_platform()


@app.get("/accio/empresas/")
@app.get("/accio/empresas")
@app.get("/accio/tenants/")
@app.get("/accio/tenants")
def empresas_page():
    if not session.get("accio_auth"):
        return redirect("/accio/login/", code=302)
    companies = _company_rows_for_session()
    if len(companies) == 1:
        err = _enter_empresa_session(companies[0]["id"])
        if not err:
            return redirect(_tenant_home_url(companies[0]["id"]), code=302)
    return _render_empresas_page()


@app.route("/accio/login/<tenant_id>/", methods=["GET", "POST"], strict_slashes=False)
def login_page(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    if request.method == "POST":
        login = (request.form.get("username") or request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        if not login or not password:
            return _render_login(tenant_id, error="Usuario y contraseña son obligatorios.")
        user = auth_service.authenticate(login, password, tenant_id)
        if not user:
            audit_service.log_event(tenant_id, "login_failed", actor=login, category="auth", success=False)
            return _render_login(tenant_id, error="Usuario o contraseña incorrectos.")
        _establish_user_session(user, tenant_id)
        audit_service.log_event(
            tenant_id,
            "login",
            actor=user["email"],
            category="auth",
            detail={"role": user["role"], "method": "form"},
        )
        nxt = request.args.get("next") or _tenant_home_url(tenant_id)
        resp = redirect(nxt, code=302)
        resp.headers["Cache-Control"] = "no-store"
        return resp
    if session.get("accio_auth") and _user_can_access_tenant(tenant_id):
        nxt = request.args.get("next") or _tenant_home_url(tenant_id)
        return redirect(nxt, code=302)
    return _render_login(tenant_id)


@app.get("/accio/dashboard")
def dashboard_redirect_root():
    if session.get("accio_auth"):
        tid = session.get("tenant_id")
        if tid and _user_can_access_tenant(tid):
            return redirect(_tenant_home_url(tid), code=302)
        allowed = _allowed_tenant_rows()
        if allowed:
            pick = next((row for row in allowed if row["id"] == DEFAULT_TENANT), allowed[0])
            err = _enter_empresa_session(pick["id"])
            if not err:
                return redirect(_tenant_home_url(pick["id"]), code=302)
        return redirect("/accio/empresas/", code=302)
    return redirect("/accio/login/", code=302)


@app.get("/accio/dashboard/")
def dashboard_redirect_default():
    return dashboard_redirect_root()


@app.get("/accio/dashboard/<tenant_id>/", strict_slashes=False)
def dashboard_page(tenant_id: str):
    if tenant_id in DASHBOARD_ASSETS:
        return _serve_dashboard_asset(tenant_id)
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    if not session.get("accio_auth"):
        return redirect(_dashboard_login_url(tenant_id), code=302)
    if not _user_can_access_tenant(tenant_id):
        allowed = _allowed_tenant_rows()
        if allowed:
            pick = next((row for row in allowed if row["id"] == DEFAULT_TENANT), allowed[0])
            return redirect(_tenant_home_url(pick["id"]), code=302)
        return jsonify({"ok": False, "error": "Sin acceso a ningún tenant"}), 403
    err = _enter_empresa_session(tenant_id)
    if err:
        return jsonify({"ok": False, "error": err}), 403
    if request.args.get("vista") != "operaciones" and not request.args.get("tab"):
        return redirect(_tenant_home_url(tenant_id), code=302)
    return _render_dashboard(tenant_id)


@app.get("/accio/plan")
@app.get("/accio/plan/")
def plan_redirect_root():
    if not session.get("accio_auth"):
        return redirect("/accio/login/", code=302)
    tid = session.get("tenant_id")
    if tid and _user_can_access_tenant(tid):
        return redirect(_tenant_home_url(tid), code=302)
    allowed = _allowed_tenant_rows()
    if allowed:
        pick = next((row for row in allowed if row["id"] == DEFAULT_TENANT), allowed[0])
        err = _enter_empresa_session(pick["id"])
        if not err:
            return redirect(_tenant_home_url(pick["id"]), code=302)
    return redirect("/accio/empresas/", code=302)


@app.get("/accio/plan/<tenant_id>/", strict_slashes=False)
def plan_slice_page(tenant_id: str):
    if not session.get("accio_auth"):
        return redirect(_dashboard_login_url(tenant_id), code=302)
    if not _user_can_access_tenant(tenant_id):
        return jsonify({"ok": False, "error": "Sin acceso a este tenant"}), 403
    err = _enter_empresa_session(tenant_id)
    if err:
        return jsonify({"ok": False, "error": err}), 403
    return _render_plan_slice(tenant_id)


@app.get("/accio/dashboard/<path:asset>")
def dashboard_assets_legacy(asset: str):
    """Compatibilidad: assets bajo /accio/dashboard/ sin confundir con tenants."""
    name = asset.rstrip("/").split("/")[-1]
    if name in DASHBOARD_ASSETS:
        return _serve_dashboard_asset(name)
    return jsonify({"ok": False, "error": "Asset no permitido"}), 404


@app.get("/accio/privacidad")
def privacy_redirect():
    return redirect("/accio/privacidad/", code=302)


@app.get("/accio/privacidad/")
def privacy_page():
    return send_from_directory(app.static_folder, "privacidad.html", mimetype="text/html")


def _emaccion_landing_file(filename: str):
    base = EMACCION_LANDING_DIR.resolve()
    path = (EMACCION_LANDING_DIR / filename).resolve()
    if not str(path).startswith(str(base)) or not path.is_file():
        return None
    return path


@app.get("/accio/producto")
def emaccion_product_redirect():
    return redirect("/accio/producto/", code=302)


@app.get("/accio/producto/")
def emaccion_product_landing():
    index = _emaccion_landing_file("index.html")
    if index is None:
        return jsonify({"ok": False, "error": "Landing EM+Acción no configurada"}), 404
    return send_from_directory(EMACCION_LANDING_DIR, "index.html", mimetype="text/html")


@app.get("/accio/producto/<path:filename>")
def emaccion_product_static(filename: str):
    if filename in ("", "index.html"):
        return redirect("/accio/producto/", code=302)
    path = _emaccion_landing_file(filename)
    if path is None:
        return jsonify({"ok": False, "error": "Recurso no encontrado"}), 404
    mimetype = None
    if filename.endswith(".css"):
        mimetype = "text/css"
    elif filename.endswith(".js"):
        mimetype = "application/javascript"
    elif filename.endswith(".svg"):
        mimetype = "image/svg+xml"
    elif filename.endswith(".png"):
        mimetype = "image/png"
    elif filename.endswith(".webp"):
        mimetype = "image/webp"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        mimetype = "image/jpeg"
    elif filename.endswith(".html"):
        mimetype = "text/html"
    return send_from_directory(EMACCION_LANDING_DIR, filename, mimetype=mimetype)


@app.post("/accio/producto/lead")
def emaccion_product_lead():
    import xmlrpc.client

    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    company = (data.get("company") or "").strip()
    intent = (data.get("intent") or "demo").strip()
    message = (data.get("message") or "").strip()

    if not name or not email:
        return jsonify({"ok": False, "error": "Nombre y email son obligatorios"}), 400

    intent_labels = {
        "demo": "Solicitar demostración",
        "reunion": "Agendar reunión",
        "cotizacion": "Solicitar cotización",
        "prueba": "Iniciar prueba",
    }
    intent_label = intent_labels.get(intent, intent)
    lead_name = company or name
    description = (
        f"Lead EM+Acción landing\n"
        f"Interés: {intent_label}\n"
        f"Nombre: {name}\n"
        f"Email: {email}\n"
        f"Teléfono: {phone}\n"
        f"Empresa: {company}\n"
        f"Mensaje: {message}\n"
        f"Origen: emaccion_producto"
    )

    try:
        url = os.getenv("ODOO_URL", "").rstrip("/")
        db = os.getenv("ODOO_DB", "")
        user = os.getenv("ODOO_USER", "")
        password = os.getenv("ODOO_PASSWORD", "")
        if not all([url, db, user, password]):
            return jsonify({"ok": False, "error": "CRM no configurado en el servidor"}), 503

        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, user, password, {})
        if not uid:
            return jsonify({"ok": False, "error": "Error de autenticación CRM"}), 503
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

        existing = models.execute_kw(
            db, uid, password, "crm.lead", "search", [[("email_from", "=", email)]], {"limit": 1}
        )
        if existing:
            return jsonify({"ok": True, "message": "Ya tenemos su solicitud registrada. Le contactaremos pronto.", "duplicate": True})

        values = {
            "name": lead_name,
            "contact_name": name,
            "email_from": email,
            "phone": phone,
            "description": description,
            "type": "opportunity",
        }
        source_id = models.execute_kw(
            db, uid, password, "utm.source", "search", [[("name", "=", "emaccion_producto")]], {"limit": 1}
        )
        if source_id:
            values["source_id"] = source_id[0]
        stage_id = models.execute_kw(
            db, uid, password, "crm.stage", "search", [[("name", "=", "Nuevo - Marketing")]], {"limit": 1}
        )
        if stage_id:
            values["stage_id"] = stage_id[0]

        lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [values])
        try:
            from Motor_Tecnico.accio_engine import leads_store, metrics_store

            local = leads_store.record_lead(
                "easytech",
                app_id="default",
                campaign_id="",
                source="emaccion_producto",
                medium="landing",
                channel="web",
                landing_url=request.referrer or "https://emaccion.etsrv.site/accio/producto/",
                utm={},
                status="new",
                crm_destination="odoo",
                crm_lead_id=lead_id,
                contact={"name": name, "email": email, "phone": phone, "company": company},
                meta={"intent": intent, "intent_label": intent_label},
            )
            metrics_store.record_event(
                "easytech",
                "lead_created",
                app_id="default",
                channel="web",
                lead_id=local["id"],
                meta={"crm_lead_id": lead_id, "source": "emaccion_producto"},
            )
        except Exception:
            pass
        return jsonify({"ok": True, "lead_id": lead_id, "message": "Solicitud recibida. Le contactaremos pronto."})
    except Exception as exc:
        return jsonify({"ok": False, "error": f"No se pudo registrar la solicitud: {exc}"}), 500


@app.get("/accio/<tenant_id>/legal/")
@app.get("/accio/<tenant_id>/legal/<doc>")
def tenant_legal_page(tenant_id: str, doc: str = ""):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    legal_dir = tenant.root / "legal"
    if not legal_dir.is_dir():
        return jsonify({"ok": False, "error": "Documentos legales no configurados para este tenant"}), 404
    name = (doc or "index").strip("/").split("/")[-1]
    if name.endswith(".css"):
        safe = Path(name).name
    elif name.endswith(".html"):
        safe = Path(name).name
    else:
        safe = f"{name}.html"
    if safe != name and not name.endswith(".css"):
        safe = Path(safe).name
    path = legal_dir / safe
    if not path.is_file():
        return jsonify({"ok": False, "error": f"Documento legal no encontrado: {name}"}), 404
    mime = "text/css" if safe.endswith(".css") else "text/html"
    return send_from_directory(legal_dir, safe, mimetype=mime)


@app.get("/accio/<tenant_id>/legal/compliance.json")
def tenant_legal_compliance(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    path = tenant.root / "legal" / "compliance.json"
    if not path.is_file():
        return jsonify({"ok": False, "error": "compliance.json no configurado"}), 404
    return jsonify({"ok": True, **json.loads(path.read_text(encoding="utf-8"))})


# --- Settings Fase N ---


@app.get("/accio/<tenant_id>/assets/<path:filename>")
def tenant_assets(tenant_id: str, filename: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    assets_dir = tenant.root / "assets"
    if not assets_dir.is_dir():
        return jsonify({"ok": False, "error": "Sin assets"}), 404
    safe = Path(filename).name
    if safe != filename:
        return jsonify({"ok": False, "error": "Ruta inválida"}), 400
    return send_from_directory(assets_dir, safe)


@app.post("/accio/<tenant_id>/settings/logo")
@require_api_key
def settings_logo_upload(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    file = request.files.get("logo")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Falta archivo logo"}), 400
    try:
        url = settings_center.save_tenant_logo(tenant_id, file)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "logo_url": url, "profile": tenant_profile.load_profile(tenant_id)})


@app.get("/accio/<tenant_id>/settings/tenant")
@require_api_key
def settings_tenant_get(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify({"ok": True, "profile": tenant_profile.load_profile(tenant_id)})


@app.post("/accio/<tenant_id>/settings/tenant")
@require_api_key
def settings_tenant_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    payload = body.get("profile", body)
    try:
        saved = tenant_profile.save_profile(tenant_id, payload)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "profile": saved})


@app.get("/accio/<tenant_id>/settings")
@require_api_key
def settings_get(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify({"ok": True, **tenant_secrets.get_settings_view(tenant_id)})


@app.get("/accio/<tenant_id>/settings/center")
@require_api_key
def settings_center_get(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    allowed_ids = None
    if session.get("auth_method") == "user" and session.get("global_role") != "super_admin":
        allowed_ids = {row["id"] for row in _allowed_tenant_rows()}
    return jsonify(
        {
            "ok": True,
            **settings_center.get_center_view(tenant_id, allowed_company_ids=allowed_ids),
        }
    )


@app.post("/accio/<tenant_id>/settings/empresa")
@require_api_key
def settings_empresa_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    return jsonify({"ok": True, **settings_center.save_empresa(tenant_id, body)})


@app.get("/accio/<tenant_id>/settings/empresas")
@require_api_key
def settings_empresas_list(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    companies = tenant_provisioning.list_companies(include_disabled=True)
    if session.get("auth_method") == "user" and not _is_platform_admin():
        allowed = {row["id"] for row in _allowed_tenant_rows()}
        companies = [c for c in companies if c.get("tenant_id") in allowed]
    return jsonify(
        {
            "ok": True,
            "companies": companies,
            "selected_tenant_id": tenant_id,
        }
    )


@app.get("/accio/<tenant_id>/settings/empresas/<target_id>")
@require_api_key
def settings_empresas_get(tenant_id: str, target_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    denied = _tenant_target_access_required(target_id)
    if denied:
        return denied
    try:
        company = tenant_provisioning.get_company(target_id)
    except TenantNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    return jsonify({"ok": True, "company": company})


@app.post("/accio/<tenant_id>/settings/empresas")
@require_api_key
def settings_empresas_create(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    denied = _platform_admin_required()
    if denied:
        return denied
    body = request.get_json(silent=True) or {}
    try:
        company = tenant_provisioning.create_company(body)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    user_id = session.get("user_id")
    if user_id and session.get("auth_method") == "user":
        auth_service.assign_user_tenant(user_id, company["tenant_id"], "tenant_admin")
    audit_service.log_event(
        tenant_id,
        "company_created",
        actor=session.get("user_name") or user_id or "api",
        category="empresas",
        detail={"target_tenant_id": company["tenant_id"]},
    )
    return jsonify({"ok": True, "company": company})


@app.post("/accio/<tenant_id>/settings/empresas/<target_id>")
@require_api_key
def settings_empresas_update(tenant_id: str, target_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    denied = _tenant_target_access_required(target_id)
    if denied:
        return denied
    body = request.get_json(silent=True) or {}
    if session.get("auth_method") == "user" and not _is_platform_admin():
        body = {k: v for k, v in body.items() if k != "status"}
    try:
        company = tenant_provisioning.update_company(target_id, body)
    except TenantNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    audit_service.log_event(
        tenant_id,
        "company_updated",
        actor=session.get("user_name") or session.get("user_id") or "api",
        category="empresas",
        detail={"target_tenant_id": target_id},
    )
    return jsonify({"ok": True, "company": company})


@app.post("/accio/<tenant_id>/settings/empresas/<target_id>/disable")
@require_api_key
def settings_empresas_disable(tenant_id: str, target_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    denied = _platform_admin_required()
    if denied:
        return denied
    try:
        result = tenant_provisioning.disable_company(target_id)
    except (TenantNotFoundError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    audit_service.log_event(
        tenant_id,
        "company_disabled",
        actor=session.get("user_name") or session.get("user_id") or "api",
        category="empresas",
        detail={"target_tenant_id": target_id},
    )
    return jsonify({"ok": True, **result})


@app.post("/accio/<tenant_id>/settings/empresas/<target_id>/enable")
@require_api_key
def settings_empresas_enable(tenant_id: str, target_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    denied = _platform_admin_required()
    if denied:
        return denied
    try:
        result = tenant_provisioning.enable_company(target_id)
    except TenantNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    audit_service.log_event(
        tenant_id,
        "company_enabled",
        actor=session.get("user_name") or session.get("user_id") or "api",
        category="empresas",
        detail={"target_tenant_id": target_id},
    )
    return jsonify({"ok": True, **result})


@app.post("/accio/<tenant_id>/settings/productos")
@require_api_key
def settings_productos_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    try:
        data = settings_center.save_products(tenant_id, body)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "productos": data})


@app.post("/accio/<tenant_id>/settings/publicacion")
@require_api_key
def settings_publicacion_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    data = settings_center.save_publication(tenant_id, body)
    return jsonify({"ok": True, "publicacion": data})


@app.post("/accio/<tenant_id>/settings/landings")
@require_api_key
def settings_landings_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    data = settings_center.save_landings(tenant_id, body)
    return jsonify({"ok": True, "landing": data})


@app.post("/accio/<tenant_id>/settings/variables")
@require_api_key
def settings_variables_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    data = settings_center.save_variables(tenant_id, body)
    return jsonify({"ok": True, "variables": data})


@app.post("/accio/<tenant_id>/settings/ia")
@require_api_key
def settings_ia_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    data = settings_center.save_ai_config(tenant_id, body)
    return jsonify({"ok": True, "ia": data})


@app.post("/accio/<tenant_id>/settings/usuarios")
@require_api_key
def settings_usuarios_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    try:
        data = settings_center.save_users(
            tenant_id,
            body,
            actor_is_platform=_is_platform_admin(),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "usuarios": data})


@app.get("/accio/<tenant_id>/settings/logs")
@require_api_key
def settings_logs_get(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    log_name = request.args.get("log", "accio_tick")
    lines = min(int(request.args.get("lines", 80)), 300)
    return jsonify(settings_center.read_logs(log_name, lines))


@app.post("/accio/<tenant_id>/settings/backup")
@require_api_key
def settings_backup_run(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify(settings_center.run_backup())


@app.post("/accio/<tenant_id>/settings/connectors")
@require_api_key
def settings_connectors_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    section = body.get("section", "linkedin")
    payload = body.get("values") or body
    view = tenant_secrets.save_settings_section(tenant_id, "connectors", payload)
    return jsonify({"ok": True, **view})


@app.post("/accio/<tenant_id>/settings/crm")
@require_api_key
def settings_crm_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    payload = body.get("values") or body
    view = tenant_secrets.save_settings_section(tenant_id, "crm", payload)
    return jsonify({"ok": True, **view})


@app.post("/accio/<tenant_id>/settings/platform")
@require_api_key
def settings_platform_save(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    payload = body.get("values") or body
    view = tenant_secrets.save_settings_section(tenant_id, "platform", payload)
    return jsonify({"ok": True, **view})


@app.post("/accio/<tenant_id>/settings/connectors/<connector_id>/test")
@require_api_key
def settings_test_connector(tenant_id: str, connector_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    result = tenant_secrets.test_connector(tenant_id, connector_id)
    return jsonify({"ok": result.get("ok", False), **result})


@app.post("/accio/<tenant_id>/settings/crm/test")
@require_api_key
def settings_test_crm(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    result = tenant_secrets.test_crm(tenant_id)
    return jsonify({"ok": result.get("ok", False), **result})


# --- Dashboard API (tenant) ---


@app.get("/accio/<tenant_id>/dashboard/api/summary")
@require_api_key
def dashboard_summary(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    app_id = _requested_app_id(tenant_id)
    return jsonify(dashboard_data.get_summary(tenant_id, app_id))


@app.get("/accio/<tenant_id>/dashboard/api/campaigns")
@require_api_key
def dashboard_campaigns(tenant_id: str):
    app_id = _requested_app_id(tenant_id)
    return jsonify({"ok": True, "app_id": app_id, "campaigns": dashboard_data.load_campaigns(tenant_id, app_id)})


@app.get("/accio/<tenant_id>/dashboard/api/calendar")
@require_api_key
def dashboard_calendar(tenant_id: str):
    app_id = _requested_app_id(tenant_id)
    return jsonify({"ok": True, "app_id": app_id, **dashboard_data.load_calendar_view(tenant_id, app_id)})


@app.get("/accio/<tenant_id>/dashboard/api/publications")
@require_api_key
def dashboard_publications(tenant_id: str):
    from Motor_Tecnico.accio_engine import publications_api

    app_id = request.args.get("app_id") or _requested_app_id(tenant_id)
    status = request.args.get("status")
    platform = request.args.get("platform") or request.args.get("channel")
    campaign_id = request.args.get("campaign_id")
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = max(int(request.args.get("offset", 0)), 0)
    if request.args.get("all_apps") == "1":
        app_id = None
    return jsonify(
        {
            "ok": True,
            **publications_api.list_publications(
                tenant_id,
                app_id=app_id,
                status=status,
                platform=platform,
                campaign_id=campaign_id,
                limit=limit,
                offset=offset,
            ),
        }
    )


@app.get("/accio/<tenant_id>/dashboard/api/metrics")
@require_api_key
def dashboard_metrics(tenant_id: str):
    app_id = _requested_app_id(tenant_id)
    return jsonify({"ok": True, "app_id": app_id, **dashboard_data.load_metrics(tenant_id, app_id)})


@app.get("/accio/<tenant_id>/dashboard/api/flyers")
@require_api_key
def dashboard_flyers(tenant_id: str):
    app_id = _requested_app_id(tenant_id)
    return jsonify({"ok": True, "app_id": app_id, **dashboard_data.load_flyers_library(tenant_id, app_id)})


@app.get("/accio/<tenant_id>/dashboard/api/connectors")
@require_api_key
def dashboard_connectors_api(tenant_id: str):
    return jsonify({"ok": True, "connectors": dashboard_data.load_connectors(tenant_id)})


@app.get("/accio/<tenant_id>/dashboard/api/knowledge")
@require_api_key
def dashboard_knowledge(tenant_id: str):
    summary = knowledge_api.knowledge_summary(tenant_id)
    queue = executor.load_content_queue(tenant_id)
    summary["editorial_balance"] = knowledge_api.editorial_balance(queue.get("posts", []), tenant_id)
    return jsonify({"ok": True, **summary})


@app.get("/accio/<tenant_id>/dashboard/api/settings")
@require_api_key
def dashboard_settings_api(tenant_id: str):
    return jsonify({"ok": True, **tenant_secrets.get_settings_view(tenant_id)})


# --- Knowledge & config ---


@app.get("/accio/<tenant_id>/config/business-context")
@require_api_key
def business_context_get(tenant_id: str):
    return jsonify({"ok": True, "context": knowledge_api.load_business_context(tenant_id)})


@app.post("/accio/<tenant_id>/config/business-context")
@require_api_key
def business_context_set(tenant_id: str):
    body = request.get_json(silent=True) or {}
    ctx = body.get("context", body)
    saved = knowledge_api.save_business_context(ctx, tenant_id)
    return jsonify({"ok": True, "context": saved})


@app.get("/accio/<tenant_id>/knowledge")
@require_api_key
def knowledge_list(tenant_id: str):
    return jsonify({"ok": True, "articles": knowledge_api.list_knowledge(tenant_id)})


@app.get("/accio/<tenant_id>/knowledge/<slug>")
@require_api_key
def knowledge_article(tenant_id: str, slug: str):
    try:
        article = knowledge_api.load_article(slug, tenant_id)
        return jsonify({"ok": True, "article": article})
    except FileNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404


@app.post("/accio/<tenant_id>/knowledge")
@require_api_key
def knowledge_create(tenant_id: str):
    body = request.get_json(silent=True) or {}
    try:
        article = knowledge_api.save_article(tenant_id, body)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "article": article})


@app.post("/accio/<tenant_id>/knowledge/<slug>")
@require_api_key
def knowledge_update(tenant_id: str, slug: str):
    body = request.get_json(silent=True) or {}
    try:
        article = knowledge_api.save_article(tenant_id, body, slug=slug)
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "article": article})


@app.delete("/accio/<tenant_id>/knowledge/<slug>")
@require_api_key
def knowledge_delete(tenant_id: str, slug: str):
    try:
        result = knowledge_api.delete_article(slug, tenant_id)
    except FileNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    return jsonify({"ok": True, **result})


@app.post("/accio/<tenant_id>/content/generate-topic")
@require_api_key
def content_generate_topic(tenant_id: str):
    body = request.get_json(silent=True) or {}
    try:
        result = knowledge_api.generate_topic(
            topic=body.get("topic"),
            product_slug=(body.get("product_slug") or body.get("product") or "easytech").strip(),
            content_type=(body.get("content_type") or "educacion").strip(),
            platform=(body.get("platform") or "linkedin").strip(),
            tenant_id=tenant_id,
        )
    except FileNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404

    if body.get("enqueue"):
        try:
            post = executor.enqueue_post(result["post"], tenant_id)
            result["enqueued"] = post
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc), "generated": result}), 400

    return jsonify({"ok": True, **result})


@app.get("/accio/<tenant_id>/connectors")
@require_api_key
def connectors_registry(tenant_id: str):
    from Motor_Tecnico.connectors.registry import load_registry

    return jsonify({"ok": True, **load_registry(tenant_id), "runtime": dashboard_data.load_connectors(tenant_id)})


@app.get("/accio/<tenant_id>/apps")
@require_api_key
def apps_list(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    apps = [a.to_dict() for a in marketing_app.list_apps(tenant_id)]
    provisioned = marketing_app.provision_all_apps(tenant_id)
    return jsonify(
        {
            "ok": True,
            "tenant_id": tenant_id,
            "default_app_id": marketing_app.default_app_id(tenant_id),
            "apps": apps,
            "provisioned": provisioned,
        }
    )


@app.get("/accio/<tenant_id>/apps/<app_id>")
@require_api_key
def apps_get(tenant_id: str, app_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    try:
        app = marketing_app.get_app(tenant_id, app_id)
    except marketing_app.AppNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    return jsonify(
        {
            "ok": True,
            "app": app.to_dict(),
            "paths": {k: str(v) for k, v in paths.items() if isinstance(v, Path)},
        }
    )


@app.post("/accio/<tenant_id>/apps")
@require_api_key
def apps_create(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    body = request.get_json(silent=True) or {}
    try:
        app = marketing_app.create_app(tenant_id, body)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except marketing_app.AppNotFoundError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "app": app.to_dict()}), 201


@app.get("/accio/assets/flyers/<path:filename>")
def flyer_asset(filename: str):
    safe = Path(filename).name
    if safe != filename or not safe.lower().endswith(".png"):
        return jsonify({"ok": False, "error": "Archivo no permitido"}), 400
    folder = BASE_DIR / "Marketing" / "flyers"
    path = folder / safe
    if not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    return send_from_directory(folder, safe, mimetype="image/png")


@app.get("/accio/<tenant_id>/tasks")
@require_api_key
def tasks_get(tenant_id: str):
    from Motor_Tecnico.accio_engine.tenant import effective_paths

    path = effective_paths(resolve_tenant(tenant_id))["tasks"]
    if not path.is_file():
        return jsonify({"ok": True, "tasks": []})
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.patch("/accio/<tenant_id>/tasks/<task_id>")
@require_api_key
def tasks_patch(tenant_id: str, task_id: str):
    from datetime import datetime, timezone

    from Motor_Tecnico.accio_engine.tenant import effective_paths

    body = request.get_json(silent=True) or {}
    path = effective_paths(resolve_tenant(tenant_id))["tasks"]
    data = json.loads(path.read_text(encoding="utf-8"))
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            if "status" in body:
                task["status"] = body["status"]
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return jsonify({"ok": True, "task": task})
    return jsonify({"ok": False, "error": "Tarea no encontrada"}), 404


@app.get("/accio/files/tree")
@require_api_key
def files_tree():
    return jsonify({"ok": True, **files_api.get_file_tree()})


@app.get("/accio/files/read")
@require_api_key
def files_read():
    rel = request.args.get("path", "").strip()
    if not rel:
        return jsonify({"ok": False, "error": "Parametro path requerido"}), 400
    try:
        return jsonify({"ok": True, **files_api.read_text_file(rel)})
    except FileNotFoundError:
        return jsonify({"ok": False, "error": "Archivo no encontrado"}), 404
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/accio/openapi.json")
def openapi_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Accio Marketing Engine — Multi-tenant", "version": "3.0.0"},
        "servers": [{"url": "https://emaccion.etsrv.site"}],
        "security": [{"bearerAuth": []}],
        "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}},
        "paths": {
            "/accio/{tenant_id}/status": {"get": {"summary": "Estado del motor por tenant"}},
            "/accio/{tenant_id}/settings": {"get": {"summary": "Configuración tenant"}},
            "/accio/{tenant_id}/apps": {"get": {"summary": "Apps de marketing del tenant"}},
            "/accio/{tenant_id}/apps/{app_id}": {"get": {"summary": "Detalle app"}},
        },
    }
    return jsonify(spec)


@app.get("/accio/<tenant_id>/status")
@require_api_key
def status(tenant_id: str):
    tenant, err = _tenant_or_404(tenant_id)
    if tenant is None:
        return jsonify({"ok": False, "error": err}), 404
    return jsonify({"ok": True, **executor.get_status(tenant_id, _requested_app_id(tenant_id))})


@app.get("/accio/<tenant_id>/content/queue")
@require_api_key
def content_queue(tenant_id: str):
    app_id = _requested_app_id(tenant_id)
    return jsonify({"ok": True, "app_id": app_id, "queue": executor.load_content_queue_for_app(tenant_id, app_id)})


@app.get("/accio/<tenant_id>/orders")
@require_api_key
def orders_list(tenant_id: str):
    status_filter = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify({"ok": True, "orders": queue_store.list_orders(status_filter, limit, tenant_id)})


@app.get("/accio/<tenant_id>/orders/<order_id>")
@require_api_key
def order_detail(tenant_id: str, order_id: str):
    order = queue_store.get_order(order_id, tenant_id)
    if not order:
        return jsonify({"ok": False, "error": "Orden no encontrada"}), 404
    return jsonify({"ok": True, "order": order})


@app.post("/accio/<tenant_id>/orders")
@require_api_key
def orders_create(tenant_id: str):
    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip()
    if not action:
        return jsonify({"ok": False, "error": "Campo action requerido"}), 400
    if action not in executor.ACTIONS:
        return jsonify({"ok": False, "error": f"Accion invalida: {action}"}), 400

    execute_now = bool(body.get("execute_now", False))
    order = queue_store.create_order(action, body.get("params") or {}, body.get("source", "accio"), tenant_id)

    if execute_now:
        order = _run_order(order, tenant_id)

    return jsonify({"ok": True, "order": order}), 201


@app.post("/accio/<tenant_id>/tick")
@require_api_key
def tick(tenant_id: str):
    pending = queue_store.pending_orders(tenant_id)
    if not pending:
        return jsonify({"ok": True, "message": "Sin ordenes pendientes", "processed": 0})

    order = pending[0]
    order = _run_order(order, tenant_id)
    return jsonify({"ok": True, "processed": 1, "order": order})


@app.post("/accio/<tenant_id>/run/pipeline")
@require_api_key
def run_pipeline_now(tenant_id: str):
    order = queue_store.create_order("run_pipeline", {}, "api", tenant_id)
    order = _run_order(order, tenant_id)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/<tenant_id>/run/publish-linkedin")
@require_api_key
def publish_linkedin_now(tenant_id: str):
    body = request.get_json(silent=True) or {}
    app_id = _requested_app_id(tenant_id)
    params = {"force": bool(body.get("force")), "dry_run": bool(body.get("dry_run")), "app_id": app_id}
    order = queue_store.create_order("publish_linkedin", params, "api", tenant_id)
    order = _run_order(order, tenant_id)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/<tenant_id>/run/publish-meta")
@require_api_key
def publish_meta_now(tenant_id: str):
    body = request.get_json(silent=True) or {}
    platform = (body.get("platform") or "all").strip().lower()
    app_id = _requested_app_id(tenant_id)
    params = {
        "platform": platform,
        "force": bool(body.get("force")),
        "dry_run": bool(body.get("dry_run")),
        "app_id": app_id,
    }
    action = "publish_meta"
    if platform == "facebook":
        action = "publish_facebook"
    elif platform == "instagram":
        action = "publish_instagram"
    order = queue_store.create_order(action, params, "api", tenant_id)
    order = _run_order(order, tenant_id)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/<tenant_id>/run/publish-channel")
@require_api_key
def publish_channel_now(tenant_id: str):
    body = request.get_json(silent=True) or {}
    connector = (body.get("connector") or body.get("platform") or "").strip()
    if not connector:
        return jsonify({"ok": False, "error": "Campo connector o platform requerido"}), 400
    app_id = _requested_app_id(tenant_id)
    params = {
        "connector": connector,
        "force": bool(body.get("force")),
        "dry_run": bool(body.get("dry_run")),
        "app_id": app_id,
    }
    order = queue_store.create_order("publish_channel", params, "api", tenant_id)
    order = _run_order(order, tenant_id)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/<tenant_id>/content/queue")
@require_api_key
def content_queue_add(tenant_id: str):
    body = request.get_json(silent=True) or {}
    app_id = _requested_app_id(tenant_id)
    if "posts" in body:
        result = executor.enqueue_posts(body["posts"], tenant_id)
        return jsonify({"ok": len(result["errors"]) == 0, **result})
    if "post" in body:
        try:
            post = executor.enqueue_post(body["post"], tenant_id, app_id=app_id)
            return jsonify({"ok": True, "post": post}), 201
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": False, "error": "Enviar post o posts"}), 400


@app.patch("/accio/<tenant_id>/content/queue/<post_id>")
@require_api_key
def content_queue_patch_status(tenant_id: str, post_id: str):
    body = request.get_json(silent=True) or {}
    new_status = (body.get("status") or "").strip()
    if not new_status:
        return jsonify({"ok": False, "error": "Campo status requerido"}), 400
    app_id = _requested_app_id(tenant_id)
    try:
        post = executor.update_post_status(post_id, new_status, tenant_id, app_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "app_id": app_id, "post": post})


@app.post("/accio/<tenant_id>/content/queue/migrate")
@require_api_key
def content_queue_migrate(tenant_id: str):
    from Motor_Tecnico.accio_engine import queue_migration

    body = request.get_json(silent=True) or {}
    dry_run = bool(body.get("dry_run"))
    result = queue_migration.migrate_default_queue_to_apps(tenant_id, dry_run=dry_run)
    return jsonify(result)


@app.get("/accio/<tenant_id>/publications/<post_id>")
@require_api_key
def publication_detail(tenant_id: str, post_id: str):
    from Motor_Tecnico.accio_engine import publications_api

    app_id = request.args.get("app_id") or _requested_app_id(tenant_id)
    row = publications_api.find_publication(tenant_id, post_id, app_id if request.args.get("all_apps") != "1" else None)
    if not row:
        return jsonify({"ok": False, "error": "Publicación no encontrada"}), 404
    return jsonify({"ok": True, "publication": row})


@app.post("/accio/<tenant_id>/publications/<post_id>/duplicate")
@require_api_key
def publication_duplicate(tenant_id: str, post_id: str):
    from Motor_Tecnico.accio_engine import publications_api

    body = request.get_json(silent=True) or {}
    app_id = _requested_app_id(tenant_id)
    try:
        post = publications_api.duplicate_publication(
            tenant_id,
            post_id,
            app_id=app_id,
            platform=body.get("platform"),
            author=session.get("user_name") or session.get("user_id") or "dashboard",
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "post": post})


@app.post("/accio/<tenant_id>/publications/<post_id>/archive")
@require_api_key
def publication_archive(tenant_id: str, post_id: str):
    app_id = _requested_app_id(tenant_id)
    try:
        post = executor.update_post_status(post_id, "archived", tenant_id, app_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "post": post})


@app.post("/accio/<tenant_id>/publications/<post_id>/reference")
@require_api_key
def publication_reference(tenant_id: str, post_id: str):
    from Motor_Tecnico.accio_engine import publications_api

    body = request.get_json(silent=True) or {}
    app_id = _requested_app_id(tenant_id)
    try:
        post = publications_api.mark_reference(tenant_id, post_id, value=bool(body.get("value", True)), app_id=app_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": True, "post": post})


@app.patch("/accio/<tenant_id>/publications/<post_id>")
@require_api_key
def publication_patch(tenant_id: str, post_id: str):
    from Motor_Tecnico.accio_engine import publications_api

    body = request.get_json(silent=True) or {}
    app_id = _requested_app_id(tenant_id)
    if body.get("scheduled_at"):
        try:
            post = publications_api.reschedule_publication(tenant_id, post_id, body["scheduled_at"], app_id)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "post": post})
    if body.get("status"):
        try:
            post = executor.update_post_status(post_id, body["status"], tenant_id, app_id)
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
        return jsonify({"ok": True, "post": post})
    return jsonify({"ok": False, "error": "Enviar scheduled_at o status"}), 400


@app.get("/accio/<tenant_id>/assistant/context")
@require_api_key
def assistant_context(tenant_id: str):
    from Motor_Tecnico.accio_engine import assistant_llm, assistant_service

    app_id = _requested_app_id(tenant_id)
    ctx = assistant_service.build_context(tenant_id, app_id)
    return jsonify(
        {
            "ok": True,
            "tenant_id": tenant_id,
            "app_id": app_id,
            "apps_count": len(ctx.get("apps_catalog") or []),
            "context": assistant_llm.compact_context(ctx),
        }
    )


@app.get("/accio/<tenant_id>/assistant/status")
@require_api_key
def assistant_status(tenant_id: str):
    from Motor_Tecnico.accio_engine import assistant_llm, settings_center
    from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider

    ai_cfg = settings_center.load_ai_config(tenant_id)
    enabled = assistant_llm.assistant_enabled(ai_cfg)
    prov = ai_provider.provider_status()
    llm_ok = assistant_llm.llm_available(tenant_id, ai_cfg)
    model = assistant_llm.resolve_model(tenant_id, ai_cfg) if llm_ok else None
    return jsonify(
        {
            "ok": True,
            "llm_available": llm_ok,
            "assistant_enabled": enabled,
            "provider": prov.get("provider"),
            "provider_configured": prov.get("configured", False),
            "provider_reachable": prov.get("reachable", False),
            "model": model,
            "ai_config": ai_cfg,
            # Deprecated — mantener false para clientes legacy
            "has_openai_key": False,
        }
    )


@app.post("/accio/<tenant_id>/assistant/chat")
@require_api_key
def assistant_chat(tenant_id: str):
    from Motor_Tecnico.accio_engine import assistant_service

    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or body.get("message") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Prompt requerido"}), 400
    app_id = _requested_app_id(tenant_id)
    result = assistant_service.process_message(
        tenant_id,
        prompt,
        app_id=app_id,
        user=session.get("user_name") or session.get("user_id") or "dashboard",
        view=body.get("view", ""),
        selected_post_id=body.get("selected_post_id"),
        chat_history=body.get("history"),
    )
    return jsonify(result)


@app.get("/accio/<tenant_id>/assistant/orders")
@require_api_key
def assistant_orders_list(tenant_id: str):
    from Motor_Tecnico.accio_engine import assistant_store

    # Todas las órdenes pendientes del tenant (visible desde cualquier app)
    return jsonify({"ok": True, "orders": assistant_store.list_pending_orders(tenant_id)})


@app.post("/accio/<tenant_id>/assistant/orders/<order_id>/approve")
@require_api_key
def assistant_order_approve(tenant_id: str, order_id: str):
    from Motor_Tecnico.accio_engine import assistant_service

    try:
        result = assistant_service.approve_order(
            tenant_id, order_id, user=session.get("user_name") or session.get("user_id") or "dashboard"
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify(result)


@app.post("/accio/<tenant_id>/assistant/orders/<order_id>/reject")
@require_api_key
def assistant_order_reject(tenant_id: str, order_id: str):
    from Motor_Tecnico.accio_engine import assistant_service

    try:
        result = assistant_service.reject_order(tenant_id, order_id)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify(result)


@app.get("/accio/<tenant_id>/assistant/history")
@require_api_key
def assistant_history(tenant_id: str):
    from Motor_Tecnico.accio_engine import assistant_store

    limit = min(int(request.args.get("limit", 30)), 100)
    return jsonify({"ok": True, "history": assistant_store.list_audit(tenant_id, limit=limit)})


@app.get("/accio/<tenant_id>/leads")
@require_api_key
def leads_list(tenant_id: str):
    from Motor_Tecnico.accio_engine import leads_store

    app_id = request.args.get("app_id") or _requested_app_id(tenant_id)
    limit = min(int(request.args.get("limit", 50)), 200)
    items = leads_store.list_leads(tenant_id, app_id=app_id if app_id else None, limit=limit)
    return jsonify({"ok": True, "tenant_id": tenant_id, "app_id": app_id, "leads": items})


@app.post("/accio/<tenant_id>/calendar")
@require_api_key
def calendar_set(tenant_id: str):
    body = request.get_json(silent=True) or {}
    calendar = body.get("calendar", body)
    payload = executor.set_calendar(calendar, tenant_id)
    return jsonify({"ok": True, "calendar": payload})


def _run_order(order: dict, tenant_id: str) -> dict:
    from datetime import datetime, timezone

    oid = order["id"]
    queue_store.update_order(oid, tenant_id, status="running", started_at=datetime.now(timezone.utc).isoformat())

    try:
        result = executor.execute_action(order["action"], order.get("params") or {}, tenant_id)
        ok = result.get("ok", True) if isinstance(result, dict) else True
        if isinstance(result, dict) and "ok" in result and not result["ok"]:
            raise RuntimeError(result.get("stderr") or result.get("stdout") or "Ejecucion fallida")

        state = queue_store.load_state(tenant_id)
        state["last_tick"] = datetime.now(timezone.utc).isoformat()
        state.setdefault("last_actions", {})[order["action"]] = {
            "at": state["last_tick"],
            "order_id": oid,
            "ok": True,
        }
        queue_store.save_state(state, tenant_id)

        return queue_store.update_order(
            oid,
            tenant_id,
            status="completed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            result=result,
            error=None,
        )
    except Exception as exc:
        state = queue_store.load_state(tenant_id)
        state["last_tick"] = datetime.now(timezone.utc).isoformat()
        state.setdefault("last_actions", {})[order["action"]] = {
            "at": state["last_tick"],
            "order_id": oid,
            "ok": False,
        }
        queue_store.save_state(state, tenant_id)
        return queue_store.update_order(
            oid,
            tenant_id,
            status="failed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            result=None,
            error=str(exc),
        )


register_marketing_plan_api(app, require_api_key)
register_memory_api(app, require_api_key)
register_company_brain_api(app, require_api_key)


# --- Legacy routes (default easytech) ---


def _legacy_tenant(f):
  @wraps(f)
  def wrapper(*args, **kwargs):
    kwargs.setdefault("tenant_id", DEFAULT_TENANT)
    return f(*args, **kwargs)
  return wrapper


@app.get("/accio/dashboard/api/summary")
@require_api_key
@_legacy_tenant
def legacy_dashboard_summary(tenant_id: str):
    return dashboard_summary(tenant_id)


@app.get("/accio/dashboard/api/knowledge")
@require_api_key
@_legacy_tenant
def legacy_dashboard_knowledge(tenant_id: str):
    return dashboard_knowledge(tenant_id)


@app.get("/accio/status")
@require_api_key
@_legacy_tenant
def legacy_status(tenant_id: str):
    return status(tenant_id)


@app.get("/accio/content/queue")
@require_api_key
@_legacy_tenant
def legacy_content_queue(tenant_id: str):
    return content_queue(tenant_id)


@app.post("/accio/run/pipeline")
@require_api_key
@_legacy_tenant
def legacy_run_pipeline(tenant_id: str):
    return run_pipeline_now(tenant_id)


@app.post("/accio/run/publish-linkedin")
@require_api_key
@_legacy_tenant
def legacy_publish_linkedin(tenant_id: str):
    return publish_linkedin_now(tenant_id)


@app.post("/accio/run/publish-meta")
@require_api_key
@_legacy_tenant
def legacy_publish_meta(tenant_id: str):
    return publish_meta_now(tenant_id)


@app.post("/accio/tick")
@require_api_key
@_legacy_tenant
def legacy_tick(tenant_id: str):
    return tick(tenant_id)


@app.post("/accio/config/business-context")
@require_api_key
@_legacy_tenant
def legacy_business_context_set(tenant_id: str):
    return business_context_set(tenant_id)


@app.get("/accio/config/business-context")
@require_api_key
@_legacy_tenant
def legacy_business_context_get(tenant_id: str):
    return business_context_get(tenant_id)


@app.post("/accio/content/generate-topic")
@require_api_key
@_legacy_tenant
def legacy_generate_topic(tenant_id: str):
    return content_generate_topic(tenant_id)


_secrets_imported = False


@app.before_request
def _maybe_import_secrets():
    global _secrets_imported
    if not _secrets_imported:
        try:
            tenant_secrets.import_env_to_tenant(DEFAULT_TENANT)
        except Exception:
            pass
        admin_pwd = os.getenv("ACCIO_ADMIN_PASSWORD", "").strip()
        if admin_pwd:
            try:
                settings_center.bootstrap_all_tenants(admin_pwd)
            except Exception:
                pass
        try:
            auth_service.migrate_from_tenant_json()
        except Exception:
            pass
        _secrets_imported = True


if __name__ == "__main__":
    port = int(os.getenv("ACCIO_ENGINE_PORT", "8092"))
    app.run(host="127.0.0.1", port=port)
