#!/usr/bin/env python3
"""Accio Marketing Engine — API REST orquestador."""

from __future__ import annotations

import os
import sys
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.accio_engine import dashboard_data, executor, files_api, queue_store  # noqa: E402

load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(STATIC_DIR))


def require_api_key(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = os.getenv("ACCIO_API_KEY", "").strip()
        if not expected:
            return jsonify({"ok": False, "error": "ACCIO_API_KEY no configurada en .env"}), 503
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else request.headers.get("X-Accio-Key", "")
        if token != expected:
            return jsonify({"ok": False, "error": "No autorizado"}), 401
        return view(*args, **kwargs)

    return wrapped


@app.get("/accio/health")
def health():
    return jsonify({"ok": True, "service": "accio_engine"})


@app.get("/accio/dashboard")
def dashboard_redirect():
    return redirect("/accio/dashboard/", code=302)


@app.get("/accio/dashboard/")
def dashboard_page():
    return send_from_directory(app.static_folder, "dashboard.html")


@app.get("/accio/privacidad")
def privacy_redirect():
    return redirect("/accio/privacidad/", code=302)


@app.get("/accio/privacidad/")
def privacy_page():
    return send_from_directory(app.static_folder, "privacidad.html", mimetype="text/html")


@app.get("/accio/dashboard/<path:asset>")
def dashboard_assets(asset: str):
    allowed = {"accio-design.css", "accio-logomark.svg", "em-logomark.svg", "em-accion-app-icon.svg", "em-accion-app-icon-1024.png", "accio-wordmark.svg", "accio-logo-horizontal.svg", "accio-og.svg", "palette-preview.html"}
    if asset not in allowed:
        return jsonify({"ok": False, "error": "Asset no permitido"}), 404
    if asset.endswith(".svg"):
        mimetype = "image/svg+xml"
    elif asset.endswith(".png"):
        mimetype = "image/png"
    elif asset.endswith(".html"):
        mimetype = "text/html"
    else:
        mimetype = "text/css"
    return send_from_directory(app.static_folder, asset, mimetype=mimetype)


@app.get("/accio/dashboard/api/summary")
@require_api_key
def dashboard_summary():
    return jsonify(dashboard_data.get_summary())


@app.get("/accio/dashboard/api/campaigns")
@require_api_key
def dashboard_campaigns():
    return jsonify({"ok": True, "campaigns": dashboard_data.load_campaigns()})


@app.get("/accio/dashboard/api/calendar")
@require_api_key
def dashboard_calendar():
    return jsonify({"ok": True, **dashboard_data.load_calendar_view()})


@app.get("/accio/dashboard/api/metrics")
@require_api_key
def dashboard_metrics():
    return jsonify({"ok": True, **dashboard_data.load_metrics()})


@app.get("/accio/dashboard/api/flyers")
@require_api_key
def dashboard_flyers():
    return jsonify({"ok": True, **dashboard_data.load_flyers_library()})


@app.get("/accio/dashboard/api/connectors")
@require_api_key
def dashboard_connectors_api():
    return jsonify({"ok": True, "connectors": dashboard_data.load_connectors()})


@app.get("/accio/connectors")
@require_api_key
def connectors_registry():
    from Motor_Tecnico.connectors.registry import load_registry

    return jsonify({"ok": True, **load_registry(), "runtime": dashboard_data.load_connectors()})


@app.get("/accio/assets/flyers/<path:filename>")
def flyer_asset(filename: str):
    """Imagenes de marketing (publicas, solo PNG en Marketing/flyers/)."""
    safe = Path(filename).name
    if safe != filename or not safe.lower().endswith(".png"):
        return jsonify({"ok": False, "error": "Archivo no permitido"}), 400
    folder = BASE_DIR / "Marketing" / "flyers"
    path = folder / safe
    if not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    return send_from_directory(folder, safe, mimetype="image/png")


@app.get("/accio/tasks")
@require_api_key
def tasks_get():
    path = BASE_DIR / "Marketing" / "accio" / "tasks.json"
    import json

    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.patch("/accio/tasks/<task_id>")
@require_api_key
def tasks_patch(task_id: str):
    import json
    from datetime import datetime, timezone

    body = request.get_json(silent=True) or {}
    path = BASE_DIR / "Marketing" / "accio" / "tasks.json"
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
    """Especificación para que Accio Work importe herramientas HTTP."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Accio Marketing Engine — ArrozConPollo", "version": "1.0.0"},
        "servers": [{"url": "https://n8n.etsrv.site"}],
        "security": [{"bearerAuth": []}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "paths": {
            "/accio/status": {"get": {"summary": "Estado del motor"}},
            "/accio/tasks": {"get": {"summary": "Lista de tareas del roadmap"}},
            "/accio/files/tree": {"get": {"summary": "Árbol Marketing + Motor_Tecnico"}},
            "/accio/content/queue": {
                "get": {"summary": "Cola de publicaciones"},
                "post": {"summary": "Agregar post LinkedIn"},
            },
            "/accio/run/pipeline": {"post": {"summary": "Scraper + Odoo sync"}},
            "/accio/run/publish-linkedin": {"post": {"summary": "Publicar siguiente post"}},
            "/accio/run/publish-meta": {"post": {"summary": "Publicar Facebook/Instagram"}},
            "/accio/run/publish-channel": {"post": {"summary": "Publicar por conector (registry)"}},
            "/accio/connectors": {"get": {"summary": "Registro de conectores Fase D"}},
        },
    }
    return jsonify(spec)


@app.get("/accio/status")
@require_api_key
def status():
    return jsonify({"ok": True, **executor.get_status()})


@app.get("/accio/content/queue")
@require_api_key
def content_queue():
    return jsonify({"ok": True, "queue": executor.load_content_queue()})


@app.get("/accio/orders")
@require_api_key
def orders_list():
    status_filter = request.args.get("status")
    limit = min(int(request.args.get("limit", 50)), 200)
    return jsonify({"ok": True, "orders": queue_store.list_orders(status_filter, limit)})


@app.get("/accio/orders/<order_id>")
@require_api_key
def order_detail(order_id: str):
    order = queue_store.get_order(order_id)
    if not order:
        return jsonify({"ok": False, "error": "Orden no encontrada"}), 404
    return jsonify({"ok": True, "order": order})


@app.post("/accio/orders")
@require_api_key
def orders_create():
    body = request.get_json(silent=True) or {}
    action = (body.get("action") or "").strip()
    if not action:
        return jsonify({"ok": False, "error": "Campo action requerido"}), 400
    if action not in executor.ACTIONS:
        return jsonify({"ok": False, "error": f"Accion invalida: {action}"}), 400

    execute_now = bool(body.get("execute_now", False))
    order = queue_store.create_order(action, body.get("params") or {}, body.get("source", "accio"))

    if execute_now:
        order = _run_order(order)

    return jsonify({"ok": True, "order": order}), 201


@app.post("/accio/tick")
@require_api_key
def tick():
    """Procesa la siguiente orden pendiente (para cron o Accio)."""
    pending = queue_store.pending_orders()
    if not pending:
        return jsonify({"ok": True, "message": "Sin ordenes pendientes", "processed": 0})

    order = pending[0]
    order = _run_order(order)
    return jsonify({"ok": True, "processed": 1, "order": order})


@app.post("/accio/run/pipeline")
@require_api_key
def run_pipeline_now():
    order = queue_store.create_order("run_pipeline", {}, "api")
    order = _run_order(order)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/run/publish-linkedin")
@require_api_key
def publish_linkedin_now():
    body = request.get_json(silent=True) or {}
    params = {"force": bool(body.get("force")), "dry_run": bool(body.get("dry_run"))}
    order = queue_store.create_order("publish_linkedin", params, "api")
    order = _run_order(order)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/run/publish-meta")
@require_api_key
def publish_meta_now():
    body = request.get_json(silent=True) or {}
    platform = (body.get("platform") or "all").strip().lower()
    params = {
        "platform": platform,
        "force": bool(body.get("force")),
        "dry_run": bool(body.get("dry_run")),
    }
    action = "publish_meta"
    if platform == "facebook":
        action = "publish_facebook"
    elif platform == "instagram":
        action = "publish_instagram"
    order = queue_store.create_order(action, params, "api")
    order = _run_order(order)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/run/publish-channel")
@require_api_key
def publish_channel_now():
    body = request.get_json(silent=True) or {}
    connector = (body.get("connector") or body.get("platform") or "").strip()
    if not connector:
        return jsonify({"ok": False, "error": "Campo connector o platform requerido"}), 400
    params = {
        "connector": connector,
        "force": bool(body.get("force")),
        "dry_run": bool(body.get("dry_run")),
    }
    order = queue_store.create_order("publish_channel", params, "api")
    order = _run_order(order)
    return jsonify({"ok": order["status"] == "completed", "order": order})


@app.post("/accio/content/queue")
@require_api_key
def content_queue_add():
    body = request.get_json(silent=True) or {}
    if "posts" in body:
        result = executor.enqueue_posts(body["posts"])
        return jsonify({"ok": len(result["errors"]) == 0, **result})
    if "post" in body:
        try:
            post = executor.enqueue_post(body["post"])
            return jsonify({"ok": True, "post": post}), 201
        except ValueError as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
    return jsonify({"ok": False, "error": "Enviar post o posts"}), 400


@app.post("/accio/calendar")
@require_api_key
def calendar_set():
    body = request.get_json(silent=True) or {}
    calendar = body.get("calendar", body)
    payload = executor.set_calendar(calendar)
    return jsonify({"ok": True, "calendar": payload})


def _run_order(order: dict) -> dict:
    from datetime import datetime, timezone

    oid = order["id"]
    queue_store.update_order(oid, status="running", started_at=datetime.now(timezone.utc).isoformat())

    try:
        result = executor.execute_action(order["action"], order.get("params") or {})
        ok = result.get("ok", True) if isinstance(result, dict) else True
        if isinstance(result, dict) and "ok" in result and not result["ok"]:
            raise RuntimeError(result.get("stderr") or result.get("stdout") or "Ejecucion fallida")

        state = queue_store.load_state()
        state["last_tick"] = datetime.now(timezone.utc).isoformat()
        state.setdefault("last_actions", {})[order["action"]] = {
            "at": state["last_tick"],
            "order_id": oid,
            "ok": True,
        }
        queue_store.save_state(state)

        return queue_store.update_order(
            oid,
            status="completed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            result=result,
            error=None,
        )
    except Exception as exc:
        state = queue_store.load_state()
        state["last_tick"] = datetime.now(timezone.utc).isoformat()
        state.setdefault("last_actions", {})[order["action"]] = {
            "at": state["last_tick"],
            "order_id": oid,
            "ok": False,
        }
        queue_store.save_state(state)
        return queue_store.update_order(
            oid,
            status="failed",
            completed_at=datetime.now(timezone.utc).isoformat(),
            result=None,
            error=str(exc),
        )


if __name__ == "__main__":
    port = int(os.getenv("ACCIO_ENGINE_PORT", "8092"))
    app.run(host="127.0.0.1", port=port)
