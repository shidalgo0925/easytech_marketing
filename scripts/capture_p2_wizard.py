#!/usr/bin/env python3
"""Capturas Pantalla 2 — Crear Plan (wizard) para revisión UX."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "P2_crear_plan_revision"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
VIEWPORT = {"width": 1440, "height": 900}

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

PLAN = {
    "nombre": "Plan Q3 2026 — Validación Producto",
    "objetivo": "Incrementar leads cualificados en PYME panameñas con contenido consultivo.",
    "audience": "Gerentes PYME\nContadores independientes",
    "north": "Leads cualificados mensuales",
    "criteria": "100 leads\n20 reuniones comerciales",
    "brief": "Enfoque consultivo. Competencia local. CTA diagnóstico gratuito.",
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


def capture() -> None:
    from playwright.sync_api import sync_playwright

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
        page.click('button.vs1-nav-item[data-nav="plan"]')
        page.wait_for_selector(".vs1-wizard-step-q", timeout=15000)
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "P2_01_paso1_vacio.png"), full_page=True)
        print("  📸 P2_01_paso1_vacio.png")

        page.fill("#wNombre", PLAN["nombre"])
        page.fill("#wObj", PLAN["objetivo"])
        page.screenshot(path=str(OUT / "P2_02_paso1_datos.png"), full_page=True)
        print("  📸 P2_02_paso1_datos.png")

        shots = [
            ("P2_03_paso2_enfoque.png", lambda: page.click("#vs1WizardNext")),
            ("P2_04_paso3_audiencia.png", lambda: (
                page.click('button[data-strategy="lead_generation"]'),
                page.click("#vs1WizardNext"),
            )),
            ("P2_05_paso4_meta.png", lambda: (
                page.fill("#wAud", PLAN["audience"]),
                page.click("#vs1WizardNext"),
            )),
            ("P2_06_paso5_contexto.png", lambda: (
                page.fill("#wNorth", PLAN["north"]),
                page.fill("#wCrit", PLAN["criteria"]),
                page.fill("#wIni", "2026-07-01"),
                page.fill("#wFin", "2026-09-30"),
                page.click("#vs1WizardNext"),
            )),
        ]
        for name, action in shots:
            action()
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / name), full_page=True)
            print(f"  📸 {name}")

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
