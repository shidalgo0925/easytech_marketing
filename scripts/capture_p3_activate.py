#!/usr/bin/env python3
"""Capturas Pantalla 3 — Activar Plan para revisión UX."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "P3_activar_plan_revision"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
APP = os.getenv("VS1_CAPTURE_APP", "default")
VIEWPORT = {"width": 1440, "height": 900}

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

PLAN_BODY = {
    "nombre": "Plan Q3 2026 — Validación Activar",
    "objetivo_general": "Incrementar reuniones comerciales con PYME en Panamá.",
    "strategy_type": "lead_generation",
    "north_star_metric": "12 reuniones comerciales al mes",
    "success_criteria": ["100 leads", "20 reuniones"],
    "publico_objetivo": ["Gerentes de PYME", "Contadores independientes"],
    "marketing_brief": "Enfoque consultivo. CTA diagnóstico gratuito.",
    "periodo": {"inicio": "2026-07-01", "fin": "2026-09-30"},
    "budget": {"amount": "5000", "currency": "USD"},
    "prioridad": "media",
}


def _start_server() -> subprocess.Popen:
    wrapper = f"""
import os
from pathlib import Path
os.environ["ACCIO_ENGINE_PORT"] = "{PORT}"
base = Path({str(BASE)!r})
from Motor_Tecnico.accio_engine.env_loader import load_accio_env
load_accio_env(base)
from Motor_Tecnico.accio_engine.app import app
app.run(host="{HOST}", port={PORT}, use_reloader=False)
"""
    return subprocess.Popen(
        [sys.executable, "-c", wrapper],
        cwd=str(BASE),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def _wait_health(timeout: float = 45.0) -> None:
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/accio/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Servidor local no respondió")


def _session():
    import requests

    api_key = os.getenv("ACCIO_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ACCIO_API_KEY requerida")
    s = requests.Session()
    r = s.post(f"{BASE_URL}/accio/auth/login", json={"tenant_id": TENANT, "api_key": api_key}, timeout=15)
    r.raise_for_status()
    return s


def _api(session, method: str, path: str, **kwargs):
    import requests

    headers = {
        "Content-Type": "application/json",
        "X-Accio-Tenant": TENANT,
        "X-Accio-App": APP,
    }
    url = f"{BASE_URL}{path}"
    r = session.request(method, url, headers=headers, timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()


def _activate_plan(session, plan_id: str, api_base: str, resolution: str | None = None) -> None:
    import requests

    body = {"resolution": resolution} if resolution else {}
    try:
        _api(session, "POST", f"{api_base}/{plan_id}/activate", json=body)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409 and not resolution:
            _api(session, "POST", f"{api_base}/{plan_id}/activate", json={"resolution": "finalize_previous"})
            return
        raise


def _ensure_no_active_plan(session, api_base: str) -> None:
    import requests

    try:
        active = _api(session, "GET", f"{api_base}/active")
    except requests.HTTPError:
        return
    if not active.get("data"):
        return
    temp = _create_plan(session, "cleanup")
    _activate_plan(session, temp, api_base, "finalize_previous")


def _cookies(session) -> list[dict]:
    return [{"name": c.name, "value": c.value, "domain": HOST, "path": c.path or "/"} for c in session.cookies]


def _create_plan(session, suffix: str) -> str:
    body = {**PLAN_BODY, "nombre": f"{PLAN_BODY['nombre']} ({suffix})"}
    data = _api(
        session,
        "POST",
        f"/api/v1/tenants/{TENANT}/apps/{APP}/marketing-plans",
        json=body,
    )
    return data["data"]["id"]


def capture() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    session = _session()
    api_base = f"/api/v1/tenants/{TENANT}/apps/{APP}/marketing-plans"

    _ensure_no_active_plan(session, api_base)
    plan_simple = _create_plan(session, "simple")
    plan_conflict = _create_plan(session, "conflicto")

    url = f"{BASE_URL}/accio/plan/{TENANT}/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        context.add_cookies(_cookies(session))
        page = context.new_page()

        page.goto(url, wait_until="networkidle", timeout=90000)
        page.wait_for_selector("#vs1Greeting", timeout=15000)

        page.evaluate("(id) => window.__vs1GoActivate(id)", plan_simple)
        page.wait_for_selector(".vs1-activate-q", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "P3_01_confirmar_sin_conflicto.png"), full_page=True)
        print("  📸 P3_01_confirmar_sin_conflicto.png")

        active_first = _create_plan(session, "activo previo")
        _activate_plan(session, active_first, api_base)
        page.evaluate("(id) => window.__vs1GoActivate(id)", plan_conflict)
        page.wait_for_selector(".vs1-activate-choice", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "P3_02_conflicto_plan_actual.png"), full_page=True)
        print("  📸 P3_02_conflicto_plan_actual.png")

        page.evaluate("(id) => window.__vs1GoActivate(id)", active_first)
        page.wait_for_selector(".vs1-activate-q", timeout=15000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "P3_03_plan_en_curso.png"), full_page=True)
        print("  📸 P3_03_plan_en_curso.png")

        context.close()
        browser.close()

    print(f"\n✅ Entregables UX en {OUT}")


def main() -> int:
    proc = _start_server()
    try:
        _wait_health()
        capture()
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
