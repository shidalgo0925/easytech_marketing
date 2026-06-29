#!/usr/bin/env python3
"""Captura Pantalla 1 — Workspace para revisión UX (producto real, local)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "P1_workspace_revision"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
VIEWPORT = {"width": 1440, "height": 900}

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

PLAN_DATA = {
    "nombre": "Plan Q3 2026 — Validación Producto",
    "objetivo": "Incrementar leads cualificados en el segmento PYME panameño mediante contenido de valor consultivo.",
    "north": "Leads cualificados mensuales",
    "audience": "Gerentes PYME\nContadores independientes",
    "criteria": "100 leads\n20 reuniones comerciales",
    "brief": "Enfoque consultivo. Competencia local. CTA institucional DIAGNÓSTICO.",
}


def _start_server() -> subprocess.Popen:
    wrapper = f"""
import os
from pathlib import Path
os.environ["ACCIO_ENGINE_PORT"] = "{PORT}"
base = Path({str(BASE)!r})
from Motor_Tecnico.accio_engine.env_loader import load_accio_env
load_accio_env(base)
os.environ["ACCIO_ENGINE_PORT"] = "{PORT}"
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

    url = f"{BASE_URL}/accio/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Servidor local no respondió")


def _login_session():
    import requests

    api_key = os.getenv("ACCIO_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ACCIO_API_KEY requerida")
    s = requests.Session()
    r = s.post(f"{BASE_URL}/accio/auth/login", json={"tenant_id": TENANT, "api_key": api_key}, timeout=15)
    r.raise_for_status()
    return s


def _cookies(session) -> list[dict]:
    return [{"name": c.name, "value": c.value, "domain": HOST, "path": c.path or "/"} for c in session.cookies]


def _cleanup_plans() -> None:
    plans_dir = BASE / "Marketing" / "tenants" / TENANT / "apps" / "default" / "marketing_plans"
    if plans_dir.is_dir():
        for path in plans_dir.glob("*.json"):
            path.unlink(missing_ok=True)


def capture() -> None:
    from playwright.sync_api import sync_playwright

    _cleanup_plans()
    OUT.mkdir(parents=True, exist_ok=True)
    session = _login_session()
    url = f"{BASE_URL}/accio/plan/{TENANT}/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        context.add_cookies(_cookies(session))
        page = context.new_page()

        page.goto(url, wait_until="networkidle", timeout=90000)
        page.evaluate(f"localStorage.removeItem('vs1_draft_{TENANT}_default')")
        page.reload(wait_until="networkidle")
        page.wait_for_selector("#vs1OnboardCta", timeout=15000)
        page.wait_for_timeout(800)
        path1 = OUT / "P1_01_sin_plan_activo.png"
        page.screenshot(path=str(path1), full_page=True)
        print(f"  📸 {path1}")

        page.click("#vs1OnboardCta")
        page.wait_for_timeout(500)
        page.fill("#wNombre", PLAN_DATA["nombre"])
        page.fill("#wObj", PLAN_DATA["objetivo"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.click('button[data-strategy="lead_generation"]')
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wAud", PLAN_DATA["audience"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wNorth", PLAN_DATA["north"])
        page.fill("#wCrit", PLAN_DATA["criteria"])
        page.fill("#wIni", "2026-07-01")
        page.fill("#wFin", "2026-09-30")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wBrief", PLAN_DATA["brief"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(1200)
        page.click("#vs1ActGo")
        page.wait_for_selector(".vs1-card--banner-active", timeout=15000)
        page.wait_for_timeout(1000)
        path2 = OUT / "P1_02_con_plan_activo.png"
        page.screenshot(path=str(path2), full_page=True)
        print(f"  📸 {path2}")

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
