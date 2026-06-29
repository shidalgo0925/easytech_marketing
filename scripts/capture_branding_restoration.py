#!/usr/bin/env python3
"""Capturas comparativas — branding Command Center vs Workspace Shell."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "branding_restoration"
BEFORE_SRC = BASE / "Marketing" / "deliverables" / "vertical_slice_1" / "P1_workspace_revision"
PORT = int(os.getenv("VS1_CAPTURE_PORT", "5099"))
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TENANT = os.getenv("VS1_CAPTURE_TENANT", "easytech")
VIEWPORT = {"width": 1440, "height": 900}

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)


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
        raise RuntimeError("ACCIO_API_KEY requerida para capturas")
    s = requests.Session()
    r = s.post(f"{BASE_URL}/accio/auth/login", json={"tenant_id": TENANT, "api_key": api_key}, timeout=15)
    r.raise_for_status()
    return s


def _cookies(session) -> list[dict]:
    return [{"name": c.name, "value": c.value, "domain": HOST, "path": c.path or "/"} for c in session.cookies]


def _copy_before_reference() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if BEFORE_SRC.is_dir():
        for src in BEFORE_SRC.glob("P1_*.png"):
            dst = OUT / f"ANTES_{src.name}"
            shutil.copy2(src, dst)
            print(f"  📋 Referencia antes: {dst}")


def capture() -> None:
    from playwright.sync_api import sync_playwright

    _copy_before_reference()
    session = _login_session()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        context.add_cookies(_cookies(session))
        page = context.new_page()

        dash_url = f"{BASE_URL}/accio/dashboard/{TENANT}/?vista=operaciones"
        page.goto(dash_url, wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(1500)
        ref = OUT / "REFERENCIA_dashboard_operaciones.png"
        page.screenshot(path=str(ref), full_page=False)
        print(f"  📸 {ref}")

        ws_url = f"{BASE_URL}/accio/plan/{TENANT}/"
        page.goto(ws_url, wait_until="networkidle", timeout=90000)
        page.wait_for_selector("#vs1Greeting", timeout=15000)
        page.wait_for_timeout(1200)
        after = OUT / "DESPUES_workspace_shell_branding.png"
        page.screenshot(path=str(after), full_page=True)
        print(f"  📸 {after}")

        page.click('.vs1-nav-item[data-nav="plan"]')
        page.wait_for_timeout(800)
        plan = OUT / "DESPUES_area_plan.png"
        page.screenshot(path=str(plan), full_page=True)
        print(f"  📸 {plan}")

        context.close()
        browser.close()

    print(f"\n✅ Entregables en {OUT}")


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
