#!/usr/bin/env python3
"""Recorrido real del Vertical Slice — capturas + video (servidor local)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "evidence_live"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
VIEWPORT = {"width": 1440, "height": 900}

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

PLAN_DATA_1 = {
    "nombre": "Plan Q3 2026 — Validación Producto",
    "objetivo": "Incrementar leads cualificados en el segmento PYME panameño mediante contenido de valor consultivo.",
    "north": "Leads cualificados mensuales",
    "audience": "Gerentes PYME\nContadores independientes",
    "criteria": "100 leads\n20 reuniones comerciales",
    "brief": "Enfoque consultivo EN1. Competencia local. CTA institucional DIAGNÓSTICO. Sin hard sell.",
}

PLAN_DATA_2 = {
    "nombre": "Plan Q4 2026 — Lanzamiento",
    "objetivo": "Impulsar awareness de marca para la nueva línea de productos en el mercado panameño.",
    "north": "Alcance orgánico mensual",
    "audience": "Directores comerciales\nGerentes de operaciones",
    "criteria": "50k impresiones\n500 interacciones",
    "brief": "Narrativa de lanzamiento. Prueba social. CTA diagnóstico consultivo.",
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
        raise RuntimeError("ACCIO_API_KEY requerida para captura local")
    s = requests.Session()
    r = s.post(f"{BASE_URL}/accio/auth/login", json={"tenant_id": TENANT, "api_key": api_key}, timeout=15)
    r.raise_for_status()
    if not r.json().get("ok"):
        raise RuntimeError("Login falló")
    return s


def _cookies(session) -> list[dict]:
    return [{"name": c.name, "value": c.value, "domain": HOST, "path": c.path or "/"} for c in session.cookies]


def _cleanup_plans() -> None:
    """Estado inicial sin planes (solo entorno local de captura)."""
    plans_dir = BASE / "Marketing" / "tenants" / TENANT / "apps" / "default" / "marketing_plans"
    if plans_dir.is_dir():
        for path in plans_dir.glob("*.json"):
            path.unlink(missing_ok=True)
            print(f"  🧹 removed {path.name}")


def record() -> None:
    from playwright.sync_api import sync_playwright

    _cleanup_plans()
    OUT.mkdir(parents=True, exist_ok=True)
    shots: list[Path] = []

    def shot(page, name: str) -> None:
        path = OUT / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        shots.append(path)
        print(f"  📸 {path.name}")

    session = _login_session()
    video_dir = OUT / "video"
    video_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(video_dir),
            record_video_size=VIEWPORT,
        )
        context.add_cookies(_cookies(session))
        page = context.new_page()
        url = f"{BASE_URL}/accio/plan/{TENANT}/"
        page.goto(url, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1500)

        # ── Flujo 1: Workspace sin plan → crear → activar ──
        print("\n=== Flujo 1 ===")
        page.evaluate(f"localStorage.removeItem('vs1_draft_{TENANT}_default')")
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(1200)
        shot(page, "F1_01_workspace_sin_plan")

        page.click("#vs1OnboardCta")
        page.wait_for_timeout(600)
        shot(page, "F1_02_wizard_paso1_vacio")

        page.fill("#wNombre", PLAN_DATA_1["nombre"])
        page.fill("#wObj", PLAN_DATA_1["objetivo"])
        shot(page, "F1_03_wizard_paso1_datos")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(400)

        page.click('button[data-strategy="lead_generation"]')
        shot(page, "F1_04_wizard_paso2_estrategia")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(400)

        page.fill("#wAud", PLAN_DATA_1["audience"])
        shot(page, "F1_05_wizard_paso3_audiencia")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(400)

        page.fill("#wNorth", PLAN_DATA_1["north"])
        page.fill("#wCrit", PLAN_DATA_1["criteria"])
        page.fill("#wIni", "2026-07-01")
        page.fill("#wFin", "2026-09-30")
        shot(page, "F1_06_wizard_paso4_metricas")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(400)

        page.fill("#wBrief", PLAN_DATA_1["brief"])
        shot(page, "F1_07_wizard_paso5_brief")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(1500)

        shot(page, "F1_08_activar_plan_sin_conflicto")
        page.click("#vs1ActGo")
        page.wait_for_selector(".vs1-card--banner-active", timeout=15000)
        page.wait_for_timeout(800)
        shot(page, "F1_09_workspace_plan_activo_banner")

        # ── Flujo 2: Context Builder → propuesta ──
        print("\n=== Flujo 2 ===")
        page.click('button.vs1-nav-item[data-nav="context"]')
        page.wait_for_timeout(2000)
        shot(page, "F2_01_context_builder_fuentes")

        page.click("#vs1GenProposalBtn")
        page.wait_for_timeout(3500)
        shot(page, "F2_02_primera_propuesta_ia_completa")

        # ── Flujo 3: Segundo plan → R2 ──
        print("\n=== Flujo 3 ===")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1200)
        page.click('button.vs1-nav-item[data-nav="plan"]')
        page.wait_for_timeout(600)
        page.fill("#wNombre", PLAN_DATA_2["nombre"])
        page.fill("#wObj", PLAN_DATA_2["objetivo"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.click('button[data-strategy="brand_awareness"]')
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wAud", PLAN_DATA_2["audience"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wNorth", PLAN_DATA_2["north"])
        page.fill("#wCrit", PLAN_DATA_2["criteria"])
        page.fill("#wIni", "2026-10-01")
        page.fill("#wFin", "2026-12-31")
        page.click("#vs1WizardNext")
        page.wait_for_timeout(300)
        page.fill("#wBrief", PLAN_DATA_2["brief"])
        page.click("#vs1WizardNext")
        page.wait_for_timeout(1500)

        shot(page, "F3_01_activar_conflicto_r2")
        page.click("#vs1ActFinalize")
        page.wait_for_selector(".vs1-card--banner-active", timeout=15000)
        page.wait_for_timeout(800)
        shot(page, "F3_02_workspace_nuevo_plan_activo")

        # ── Estado de error: crear borrador inválido ──
        print("\n=== Estado error ===")
        page.goto(url, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(800)
        page.click('button.vs1-nav-item[data-nav="plan"]')
        page.wait_for_timeout(400)
        page.fill("#wNombre", "")
        page.fill("#wObj", "x")
        for _ in range(4):
            page.click("#vs1WizardNext")
            page.wait_for_timeout(250)
        page.click("#vs1WizardNext")
        page.wait_for_timeout(1200)
        shot(page, "ERR_01_toast_error_validacion")

        video_path = None
        if page.video:
            page.close()
            video_path = Path(page.video.path())
        context.close()
        browser.close()

        if video_path and video_path.exists():
            dest = OUT / "VS1_recorrido_completo.webm"
            video_path.rename(dest)
            print(f"\n🎬 Video: {dest}")

    print(f"\n✅ {len(shots)} capturas en {OUT}")


def main() -> int:
    print("Vertical Slice — evidencia en vivo (local)")
    print(f"URL: {BASE_URL}/accio/plan/{TENANT}/")
    print(f"Salida: {OUT}\n")
    proc = _start_server()
    try:
        _wait_health()
        record()
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
