#!/usr/bin/env python3
"""Captura evidencia visual del Vertical Slice 1 (servidor local, sin tocar producción)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
APP = os.getenv("VS1_CAPTURE_APP", "default")

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)


def _ensure_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])


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


def _wait_health(timeout: float = 30.0) -> None:
    import urllib.request

    deadline = time.time() + timeout
    url = f"{BASE_URL}/accio/health"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError("Servidor local no respondió a /accio/health")


def _login_session():
    import requests

    api_key = os.getenv("ACCIO_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ACCIO_API_KEY no disponible para captura local")
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/accio/auth/login",
        json={"tenant_id": TENANT, "api_key": api_key},
        timeout=15,
    )
    r.raise_for_status()
    if not r.json().get("ok"):
        raise RuntimeError("Login falló: " + str(r.json()))
    return s


def _cookies_for_playwright(session) -> list[dict]:
    rows = []
    for c in session.cookies:
        rows.append(
            {
                "name": c.name,
                "value": c.value,
                "domain": HOST,
                "path": c.path or "/",
            }
        )
    return rows


def capture() -> list[Path]:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    session = _login_session()
    saved: list[Path] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        context.add_cookies(_cookies_for_playwright(session))
        page = context.new_page()
        dash = f"{BASE_URL}/accio/dashboard/{TENANT}/"
        page.goto(dash, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)

        def shot(name: str) -> Path:
            path = OUT / name
            page.screenshot(path=str(path), full_page=True)
            saved.append(path)
            print(f"  ✓ {path.name}")
            return path

        # 1a Workspace sin plan — limpiar ids locales; si hay activo en API, igual se ve con plan
        page.evaluate(
            f"""() => {{
              localStorage.removeItem('emaccion_plan_ids_{TENANT}_{APP}');
            }}"""
        )
        page.click('button.nav-item[data-tab="plan"]')
        page.wait_for_timeout(800)
        shot("01_workspace_sin_plan_local.png")

        # 2 Crear plan — formulario
        page.click('button.plan-subnav-item[data-plan-view="create"]')
        page.wait_for_timeout(400)
        page.fill('input[name="nombre"]', "Plan Q3 2026 — Validación UX")
        page.fill(
            'textarea[name="objetivo_general"]',
            "Incrementar leads cualificados en el segmento PYME panameño mediante contenido de valor.",
        )
        page.select_option('select[name="strategy_type"]', "lead_generation")
        page.fill('input[name="north_star_metric"]', "Leads cualificados mensuales")
        page.fill('input[name="periodo_inicio"]', "2026-07-01")
        page.fill('input[name="periodo_fin"]', "2026-09-30")
        page.fill('input[name="budget_amount"]', "5000")
        page.fill(
            'textarea[name="marketing_brief"]',
            "Enfoque consultivo EN1. Competencia local. CTA DIAGNÓSTICO. Sin hard sell.",
        )
        page.fill('textarea[name="success_criteria"]', "100 leads\n20 reuniones")
        page.fill('textarea[name="publico_objetivo"]', "Gerentes PYME\nContadores")
        shot("02_crear_plan_formulario.png")

        # Crear borrador A
        page.click('button[type="submit"]')
        page.wait_for_timeout(1200)

        # Crear borrador B para forzar R2
        page.click('button.plan-subnav-item[data-plan-view="create"]')
        page.wait_for_timeout(300)
        page.fill('input[name="nombre"]', "Plan Q4 2026 — Lanzamiento")
        page.fill(
            'textarea[name="objetivo_general"]',
            "Impulsar awareness de marca para la nueva línea de productos en Q4.",
        )
        page.fill('input[name="north_star_metric"]', "Alcance orgánico mensual")
        page.fill('input[name="periodo_inicio"]', "2026-10-01")
        page.fill('input[name="periodo_fin"]', "2026-12-31")
        page.fill('textarea[name="success_criteria"]', "50k impresiones")
        page.fill('textarea[name="publico_objetivo"]', "Directores comerciales")
        page.click('button[type="submit"]')
        page.wait_for_timeout(1200)

        # Activar primer borrador
        page.click('button.plan-subnav-item[data-plan-view="workspace"]')
        page.wait_for_timeout(500)
        activate_btn = page.locator('button:has-text("Activar")').first
        if activate_btn.count():
            activate_btn.click()
            page.wait_for_timeout(1200)

        shot("03_workspace_con_plan_activo.png")

        # 3 Activar con R2 — segundo borrador
        if page.locator('button:has-text("Activar")').count():
            page.locator('button:has-text("Activar")').first.click()
            page.wait_for_timeout(600)
            page.locator("#planR2Modal:not([hidden])").wait_for(timeout=5000)
            shot("04_activar_plan_dialogo_r2.png")
            page.click('button:has-text("Finalizar anterior")')
            page.wait_for_timeout(1000)

        # 4 Context Builder
        page.click('button.plan-subnav-item[data-plan-view="context"]')
        page.wait_for_timeout(1500)
        shot("05_context_builder.png")

        # 5 Planner IA
        page.click('button.plan-subnav-item[data-plan-view="planner"]')
        page.wait_for_timeout(400)
        page.click('button:has-text("Generar propuestas")')
        page.wait_for_timeout(2500)
        shot("06_planner_primera_propuesta_ia.png")

        browser.close()
    return saved


def main() -> int:
    print("Vertical Slice 1 — captura visual (local)")
    print(f"Salida: {OUT}")
    _ensure_playwright()
    proc = _start_server()
    try:
        _wait_health()
        paths = capture()
        print(f"\n{len(paths)} capturas en {OUT}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        err = proc.stderr.read().decode() if proc.stderr else ""
        if err and proc.returncode not in (0, None, -15):
            print(err[-500:], file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
