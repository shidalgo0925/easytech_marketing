#!/usr/bin/env python3
"""Capturas Pantalla 5 — Opciones estratégicas para revisión UX."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "P5_propuestas_revision"
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
    "nombre": "Plan Q3 2026 — Propuestas UX",
    "objetivo_general": "Incrementar reuniones comerciales con PYME en Panamá.",
    "strategy_type": "lead_generation",
    "north_star_metric": "12 reuniones comerciales al mes",
    "success_criteria": ["100 leads", "20 reuniones"],
    "publico_objetivo": ["Gerentes de PYME"],
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

    headers = {"Content-Type": "application/json", "X-Accio-Tenant": TENANT, "X-Accio-App": APP}
    r = session.request(method, f"{BASE_URL}{path}", headers=headers, timeout=60, **kwargs)
    r.raise_for_status()
    return r.json()


def _cookies(session) -> list[dict]:
    return [{"name": c.name, "value": c.value, "domain": HOST, "path": c.path or "/"} for c in session.cookies]


def _activate_plan(session, plan_id: str, api_base: str) -> None:
    import requests

    try:
        _api(session, "POST", f"{api_base}/{plan_id}/activate", json={})
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409:
            _api(session, "POST", f"{api_base}/{plan_id}/activate", json={"resolution": "finalize_previous"})
            return
        raise


def capture() -> None:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    session = _session()
    api_base = f"/api/v1/tenants/{TENANT}/apps/{APP}/marketing-plans"
    plan_id = _api(session, "POST", api_base, json=PLAN_BODY)["data"]["id"]
    _activate_plan(session, plan_id, api_base)

    url = f"{BASE_URL}/accio/plan/{TENANT}/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        context.add_cookies(_cookies(session))
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=90000)
        page.wait_for_selector("#vs1Greeting", timeout=15000)
        page.click('button.vs1-nav-item[data-nav="proposals"]')
        page.wait_for_selector(".vs1-proposal-q", timeout=60000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "P5_01_opciones_estrategicas.png"), full_page=True)
        print("  📸 P5_01_opciones_estrategicas.png")
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
