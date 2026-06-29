#!/usr/bin/env python3
"""Genera capturas PNG del Vertical Slice 1 (WeasyPrint + PyMuPDF)."""

from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Marketing" / "deliverables" / "vertical_slice_1"
CSS = BASE / "Motor_Tecnico" / "accio_engine" / "static" / "accio-design.css"

if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from weasyprint import CSS as WCSS  # noqa: E402
from weasyprint import HTML  # noqa: E402

import fitz  # noqa: E402

SHELL = """
<div id="app">
  <header class="topbar">
    <div class="topbar-left">
      <a class="topbar-brand"><span class="brand-name">EMAccion</span></a>
      <div class="empresa-pill empresa-pill--claro"><span class="empresa-pill-label">Tenant:</span> easytech</div>
      <div class="empresa-pill empresa-pill--claro"><span class="empresa-pill-label">App:</span> default</div>
    </div>
    <div class="topbar-right">
      <span class="status-pill">Admin</span>
      <button class="btn-primary">Actualizar plan</button>
    </div>
  </header>
  <nav class="navbar">
    <button class="nav-item">Resumen</button>
    <button class="nav-item active">Plan</button>
    <button class="nav-item">Campañas</button>
    <button class="nav-item">Publicaciones</button>
  </nav>
  <main class="content dashboard-workspace">
    {body}
  </main>
</div>
"""

PLAN_HEADER = """
<header class="plan-workspace-header">
  <div>
    <h2 class="plan-workspace-title">Plan de Marketing</h2>
    <p class="plan-workspace-sub">Estrategia declarativa · contexto unificado · propuestas IA</p>
  </div>
  <nav class="plan-subnav">
    <button class="plan-subnav-item {ws}">Workspace</button>
    <button class="plan-subnav-item {cr}">Crear</button>
    <button class="plan-subnav-item {cx}">Contexto</button>
    <button class="plan-subnav-item {pl}">Planner IA</button>
  </nav>
</header>
"""

SCREENS: dict[str, str] = {
    "01_workspace_sin_plan": PLAN_HEADER.format(ws="active", cr="", cx="", pl="")
    + """
<div class="plan-view active">
  <div class="plan-status-banner"><span class="plan-status-dot"></span><span>Sin plan activo en esta app</span></div>
  <section class="accio-card panel-full"><div class="accio-card-head">Plan activo</div>
  <div class="accio-card-body"><div class="plan-empty-state"><p>Sin plan activo</p><span class="muted">Crea y activa un plan para operar el ciclo estratégico.</span></div></div></section>
  <section class="accio-card panel-full"><div class="accio-card-head">Planes en workspace</div>
  <div class="accio-card-body"><div class="empty">Crea un plan para verlo aquí</div></div></section>
</div>""",
    "02_workspace_con_plan": PLAN_HEADER.format(ws="active", cr="", cx="", pl="")
    + """
<div class="plan-view active">
  <div class="plan-status-banner"><span class="plan-status-dot is-active"></span><span>Plan activo: Plan Q3 2026 — Validación UX</span></div>
  <section class="accio-card panel-full"><div class="accio-card-head">Plan activo</div>
  <div class="accio-card-body"><div class="plan-active-card">
    <div class="plan-active-head"><h3>Plan Q3 2026 — Validación UX</h3><span class="accio-badge accio-badge--green">activo</span></div>
    <p class="plan-active-objective">Incrementar leads cualificados en el segmento PYME panameño mediante contenido de valor.</p>
    <div class="plan-active-meta">
      <div><span class="muted">North star</span><strong>Leads cualificados mensuales</strong></div>
      <div><span class="muted">Periodo</span><strong>2026-07-01 → 2026-09-30</strong></div>
      <div><span class="muted">Presupuesto</span><strong>USD 5000</strong></div>
      <div><span class="muted">Estrategia</span><strong>lead_generation</strong></div>
    </div>
  </div></div></section>
  <section class="accio-card panel-full"><div class="accio-card-head">Planes en workspace</div>
  <div class="accio-card-body"><table class="accio-table"><thead><tr><th>Plan</th><th>Estado</th><th></th></tr></thead>
  <tbody><tr><td>Plan Q3 2026 — Validación UX<div class="muted is-mono">mpl_a1b2c3d4e5f6</div></td><td><span class="accio-badge accio-badge--green">activo</span></td><td></td></tr>
  <tr><td>Plan Q4 2026 — Lanzamiento<div class="muted is-mono">mpl_f6e5d4c3b2a1</div></td><td><span class="accio-badge">borrador</span></td><td><button class="btn-ghost">Activar</button></td></tr></tbody></table></div></section>
</div>""",
    "03_crear_plan_formulario": PLAN_HEADER.format(ws="", cr="active", cx="", pl="")
    + """
<div class="plan-view active">
<section class="accio-card panel-full"><div class="accio-card-head">Nuevo plan · borrador</div>
<div class="accio-card-body"><form class="accio-form plan-create-form"><div class="plan-form-grid">
<label class="plan-form-span2">Nombre del plan<input value="Plan Q3 2026 — Validación UX"></label>
<label class="plan-form-span2">Objetivo general<textarea rows="3">Incrementar leads cualificados en el segmento PYME panameño mediante contenido de valor.</textarea></label>
<label>Estrategia<select><option selected>Generación de leads</option></select></label>
<label>Prioridad<select><option>Alta</option><option selected>Media</option></select></label>
<label class="plan-form-span2">North star metric<input value="Leads cualificados mensuales"></label>
<label>Periodo inicio<input value="2026-07-01"></label>
<label>Periodo fin<input value="2026-09-30"></label>
<label>Presupuesto (USD)<input value="5000"></label>
<label>Moneda<input value="USD" readonly></label>
<label class="plan-form-span2">Brief de marketing<textarea rows="3">Enfoque consultivo EN1. Competencia local. CTA DIAGNÓSTICO.</textarea></label>
<label class="plan-form-span2">Criterios de éxito<textarea rows="2">100 leads&#10;20 reuniones</textarea></label>
<label class="plan-form-span2">Público objetivo<textarea rows="2">Gerentes PYME&#10;Contadores</textarea></label>
</div><div class="plan-form-actions"><button type="button" class="btn-ghost">Cancelar</button><button type="submit" class="btn-primary">Crear plan en borrador</button></div></form></div></section>
</div>""",
    "04_activar_plan_dialogo_r2": PLAN_HEADER.format(ws="active", cr="", cx="", pl="")
    + """
<div class="plan-view active" style="position:relative">
  <div class="plan-status-banner"><span class="plan-status-dot is-active"></span><span>Plan activo: Plan Q3 2026 — Validación UX</span></div>
  <section class="accio-card panel-full"><div class="accio-card-head">Planes en workspace</div>
  <div class="accio-card-body"><table class="accio-table"><tbody>
  <tr><td>Plan Q4 2026 — Lanzamiento</td><td>borrador</td><td><button class="btn-ghost">Activar</button></td></tr>
  </tbody></table></div></section>
  <div class="plan-r2-modal" style="display:flex">
    <div class="plan-r2-backdrop"></div>
    <div class="plan-r2-dialog accio-card">
      <div class="accio-card-head">Resolver plan activo (R2)</div>
      <div class="accio-card-body">
        <p>Ya existe un plan activo en esta app. Para activar el nuevo plan, elige cómo resolver el conflicto:</p>
        <ul class="plan-r2-options"><li><strong>Finalizar anterior</strong> — cierra el plan activo como finalizado.</li>
        <li><strong>Pausar anterior</strong> — deja el plan activo en pausa.</li></ul>
        <div class="plan-form-actions"><button class="btn-ghost">Pausar anterior</button><button class="btn-primary">Finalizar anterior</button></div>
      </div>
    </div>
  </div>
</div>""",
    "05_context_builder": PLAN_HEADER.format(ws="", cr="", cx="active", pl="")
    + """
<div class="plan-view active">
<section class="accio-card panel-full"><div class="accio-card-head">Context Builder · contexto operativo</div>
<div class="accio-card-body"><p class="plan-context-intro">Vista ejecutiva del contexto que alimenta al Planner.</p>
<div class="plan-context-grid">
<article class="plan-context-card"><h4>Negocio</h4><p class="plan-context-lead">Easy Technology Services</p>
<ul class="plan-context-list"><li><span>Sector</span><strong>Servicios TI</strong></li><li><span>CTA</span><strong>DIAGNÓSTICO</strong></li></ul></article>
<article class="plan-context-card"><h4>App / línea</h4><p class="plan-context-lead">EasyTech — Default</p>
<ul class="plan-context-list"><li><span>Tono</span><strong>Profesional consultivo</strong></li><li><span>Audiencia</span><strong>PYME Panamá</strong></li></ul></article>
<article class="plan-context-card"><h4>Conocimiento</h4><p class="plan-context-lead">4 fuentes activas</p>
<ul class="plan-context-tags"><li>productos</li><li>buyer_persona</li><li>competencia</li><li>tono_editorial</li></ul></article>
<article class="plan-context-card plan-context-card--highlight"><h4>Plan activo</h4>
<p class="plan-context-lead">Plan Q3 2026 — Validación UX</p>
<ul class="plan-context-list"><li><span>Objetivo</span><strong>Incrementar leads cualificados…</strong></li><li><span>North star</span><strong>Leads cualificados mensuales</strong></li></ul></article>
</div></div></section></div>""",
    "06_planner_primera_propuesta_ia": PLAN_HEADER.format(ws="", cr="", cx="", pl="active")
    + """
<div class="plan-view active">
<section class="accio-card panel-full"><div class="accio-card-head">Planner IA · primera propuesta estratégica</div>
<div class="accio-card-body plan-planner-output">
<section class="plan-exec-summary"><h4>Resumen ejecutivo</h4>
<p>Para EasyTech — Default, el plan «Plan Q3 2026 — Validación UX» apunta a incrementar leads cualificados en PYME. Con 4 fuentes de conocimiento, la recomendación prioritaria es contenido educativo alineado al plan, equilibrando valor editorial y conversión consultiva.</p></section>
<div class="plan-proposals-grid">
<article class="plan-proposal-card"><header><span class="plan-proposal-num">1</span><span class="plan-priority plan-priority--alta">alta</span></header>
<h3>Contenido educativo alineado al Plan Q3</h3><p>Serie de piezas de valor que refuercen generación de leads cualificados.</p>
<div class="plan-proposal-channel">LinkedIn</div><div class="plan-proposal-actions"><strong>Acciones</strong><ul>
<li>Definir 3 pilares de contenido alineados al objetivo</li><li>Programar calendario editorial de 4 semanas</li><li>Medir engagement vs. north star</li></ul></div></article>
<article class="plan-proposal-card"><header><span class="plan-proposal-num">2</span><span class="plan-priority plan-priority--media">media</span></header>
<h3>Caso de uso / prueba social</h3><p>Destacar resultado medible relacionado con la north star del plan.</p>
<div class="plan-proposal-actions"><strong>Acciones</strong><ul><li>Seleccionar 1 caso cliente verificable</li><li>Estructurar narrativa problema → resultado</li></ul></div></article>
<article class="plan-proposal-card"><header><span class="plan-proposal-num">3</span><span class="plan-priority plan-priority--media">media</span></header>
<h3>CTA diagnóstico consultivo</h3><p>Invitar a conversación alineada al CTA institucional DIAGNÓSTICO.</p>
<div class="plan-proposal-actions"><strong>Acciones</strong><ul><li>Redactar invitación con beneficio concreto</li><li>Enlazar guía y WhatsApp</li></ul></div></article>
</div></div></section></div>""",
}


def _html_page(body: str) -> str:
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{CSS}">
<style>
  @page {{ size: 1440px 900px; margin: 0; }}
  body {{ margin: 0; background: #eef6f0; }}
  .capture-label {{ position: fixed; top: 8px; right: 12px; background: #1a4a2e; color: #fff; padding: 4px 10px; border-radius: 6px; font-size: 11px; z-index: 9; }}
</style></head><body>{SHELL.format(body=body)}</body></html>"""


def render_png(name: str, html: str) -> Path:
    pdf_path = OUT / f"{name}.pdf"
    png_path = OUT / f"{name}.png"
    HTML(string=html, base_url=str(BASE)).write_pdf(
        str(pdf_path),
        stylesheets=[WCSS(filename=str(CSS))],
    )
    doc = fitz.open(str(pdf_path))
    doc[0].get_pixmap(dpi=144, alpha=False).save(str(png_path))
    doc.close()
    pdf_path.unlink(missing_ok=True)
    return png_path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, fragment in SCREENS.items():
        html = _html_page(fragment)
        path = render_png(name, html)
        paths.append(path)
        print(f"  ✓ {path.name}")
    # Pack PDF multi-página para revisión
    pack = OUT / "VS1_Revision_UX.pdf"
    combined = fitz.open()
    for p in paths:
        img = fitz.open(str(p))
        pdfbytes = img.convert_to_pdf()
        img.close()
        combined.insert_pdf(fitz.open("pdf", pdfbytes))
    combined.save(str(pack))
    combined.close()
    print(f"\n{len(paths)} PNG + {pack.name} en {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
