(function () {
  'use strict';

  const TENANT_ID = window.__ACCIO_TENANT__ || 'easytech';
  const APP_ID = window.__ACCIO_APP__ || localStorage.getItem(`accio_app_${TENANT_ID}`) || 'default';
  const USER_NAME = window.__ACCIO_USER_NAME__ || 'Administrador';
  const TENANTS = window.__ACCIO_TENANTS__ || [];

  const WIZARD_STEPS = [
    { id: 'name', name: 'Tu objetivo', desc: 'Qué quieres lograr y cómo lo llamas' },
    { id: 'strategy', name: 'Tu enfoque', desc: 'Cómo vas a conseguirlo' },
    { id: 'audience', name: 'Tu audiencia', desc: 'A quién te diriges' },
    { id: 'metrics', name: 'Tu meta', desc: 'Cómo medirás el progreso' },
    { id: 'brief', name: 'Contexto extra', desc: 'Lo que debemos tener en cuenta' },
  ];

  const WIZARD_QUESTIONS = {
    name: '¿Qué quieres lograr este periodo?',
    strategy: '¿Cómo quieres lograrlo?',
    audience: '¿A quién te diriges?',
    metrics: '¿Cómo sabrás que lo lograste?',
    brief: '¿Hay algo más que debamos considerar?',
  };

  const WIZARD_TIPS = {
    name: 'Usa un nombre con periodo y producto, por ejemplo «Plan Q3 2026 — Lanzamiento EN1». El objetivo debe caber en una frase medible.',
    strategy: 'Si estás empezando a darte a conocer, suele ayudar priorizar visibilidad antes de captar leads.',
    audience: 'Sé concreto: rol, sector y tamaño de empresa. Ejemplo: gerentes de PYME en servicios.',
    metrics: 'Elige una meta principal y dos o tres hitos que puedas verificar en el camino.',
    brief: 'Incluye restricciones, competencia local y el mensaje que quieres que recuerden (por ejemplo, tu diagnóstico gratuito).',
  };

  const STRATEGIES = [
    { id: 'lead_generation', icon: 'ti-target', name: 'Generación de leads', desc: 'Captar prospectos cualificados' },
    { id: 'brand_awareness', icon: 'ti-speakerphone', name: 'Darte a conocer', desc: 'Más visibilidad y reconocimiento' },
    { id: 'retention', icon: 'ti-repeat', name: 'Retención', desc: 'Fidelizar clientes actuales' },
    { id: 'launch', icon: 'ti-rocket', name: 'Lanzamiento', desc: 'Introducir producto o línea nueva' },
  ];

  let activePlan = null;
  let draftPlans = [];
  let activateTarget = null;
  let wizardStep = 0;
  let draft = loadDraft();
  let contextData = null;
  let proposalData = null;
  let contextUpdatedAt = null;

  const $ = (id) => document.getElementById(id);

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
  }

  function toast(msg, isError) {
    const el = $('vs1Toast');
    el.textContent = msg;
    el.className = 'vs1-toast is-show' + (isError ? ' is-error' : '');
    setTimeout(() => el.classList.remove('is-show'), 4000);
  }

  function draftKey() {
    return `vs1_draft_${TENANT_ID}_${APP_ID}`;
  }

  function loadDraft() {
    try {
      return JSON.parse(localStorage.getItem(draftKey()) || '{}') || defaultDraft();
    } catch (_) {
      return defaultDraft();
    }
  }

  function defaultDraft() {
    return {
      nombre: '',
      objetivo_general: '',
      strategy_type: 'lead_generation',
      publico_objetivo: '',
      north_star_metric: '',
      success_criteria: '',
      marketing_brief: '',
      prioridad: 'media',
      periodo_inicio: '',
      periodo_fin: '',
      budget_amount: '5000',
    };
  }

  function saveDraft() {
    localStorage.setItem(draftKey(), JSON.stringify(draft));
    $('vs1Autosave').textContent = 'Guardado automáticamente · ' + new Date().toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' });
  }

  function planSessionKey() {
    return `emaccion_plan_ids_${TENANT_ID}_${APP_ID}`;
  }

  function rememberPlanId(id) {
    const ids = JSON.parse(localStorage.getItem(planSessionKey()) || '[]');
    if (!ids.includes(id)) {
      ids.unshift(id);
      localStorage.setItem(planSessionKey(), JSON.stringify(ids.slice(0, 20)));
    }
  }

  function v1Base() {
    return `/api/v1/tenants/${encodeURIComponent(TENANT_ID)}/apps/${encodeURIComponent(APP_ID)}`;
  }

  function dashApi(path) {
    const sep = path.includes('?') ? '&' : '?';
    return `/accio/${encodeURIComponent(TENANT_ID)}/dashboard/api${path}${sep}app_id=${encodeURIComponent(APP_ID)}`;
  }

  const PLATFORM_LABELS = {
    linkedin: 'LinkedIn',
    facebook: 'Facebook',
    instagram: 'Instagram',
  };

  function platformLabel(code) {
    return PLATFORM_LABELS[String(code || '').toLowerCase()] || 'Red social';
  }

  function formatSchedule(iso) {
    if (!iso) return 'Sin fecha programada';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return 'Sin fecha programada';
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diff = Math.round((day - today) / 86400000);
    const time = d.toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' });
    if (diff === 0) return `Hoy · ${time}`;
    if (diff === 1) return `Mañana · ${time}`;
    if (diff === -1) return `Ayer · ${time}`;
    return d.toLocaleDateString('es-PA', { day: 'numeric', month: 'short' }) + ' · ' + time;
  }

  async function dashFetch(path) {
    const res = await fetch(dashApi(path), { credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      location.href = `/accio/login/?next=${encodeURIComponent(location.pathname)}`;
      throw new Error('Sesión expirada');
    }
    if (!res.ok || data.ok === false) {
      throw new Error(data.error || res.statusText || 'Error al cargar datos');
    }
    return data;
  }

  function humanPostStatus(label) {
    const raw = String(label || '').trim();
    if (!raw) return 'Listo para publicar';
    if (/legacy/i.test(raw)) return 'Programado';
    return raw.replace(/\s*\([^)]*\)\s*/g, ' ').trim() || 'Programado';
  }

  async function loadAssistantStatus() {
    const banner = $('vs1IaBanner');
    const bannerTitle = $('vs1IaBannerTitle');
    const bannerText = $('vs1IaBannerText');
    const bannerCta = $('vs1IaBannerCta');
    if (!banner) return;
    try {
      const res = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/assistant/status`, { credentials: 'include' });
      const data = await res.json().catch(() => ({}));
      if (!data.ok) return;
      if (data.llm_available) {
        banner.hidden = true;
        return;
      }
      banner.hidden = false;
      bannerTitle.textContent = '¿Quieres recomendaciones personalizadas?';
      bannerCta.textContent = 'Configurar asistente';
      bannerCta.onclick = () => { location.href = `/accio/dashboard/${TENANT_ID}/#configuracion`; };
      if (!data.assistant_enabled) {
        bannerText.textContent = 'Activa el asistente en Configuración para recibir propuestas alineadas a tu negocio.';
      } else if (!data.has_openai_key) {
        bannerText.textContent = 'Completa la configuración del asistente para desbloquear propuestas estratégicas.';
      } else {
        bannerText.textContent = 'El asistente está listo pero desactivado. Actívalo en Configuración cuando quieras usarlo.';
      }
    } catch (_) { /* ignore */ }
  }

  function signalCard(question, answer, detail) {
    return `<div class="vs1-signal-card">
      <p class="vs1-signal-label">${esc(question)}</p>
      <p class="vs1-signal-value">${esc(answer)}</p>
      ${detail ? `<p class="vs1-signal-meaning">${esc(detail)}</p>` : ''}
    </div>`;
  }

  function renderSignals(summary, ctxPct) {
    const stats = summary.stats || {};
    const odoo = summary.odoo || {};
    const pendingPosts = summary.pending_posts || [];
    const pendingCount = pendingPosts.length || stats.linkedin_pending || 0;
    const pubDetail = pendingCount
      ? (pendingCount === 1 ? 'Una publicación espera tu revisión' : `${pendingCount} publicaciones esperan tu revisión`)
      : 'Nada pendiente por ahora';

    let leadsAnswer = '—';
    let leadsDetail = 'Conecta tu pipeline comercial para ver prospectos aquí';
    if (odoo.ok) {
      const mkt = odoo.marketing_stage != null ? odoo.marketing_stage : 0;
      leadsAnswer = String(mkt);
      leadsDetail = mkt
        ? (mkt === 1 ? 'Un prospecto en etapa comercial' : `${mkt} prospectos en etapa comercial`)
        : 'Sin prospectos en etapa comercial todavía';
    }

    const proposalCount = proposalData && (proposalData.proposals || []).length ? (proposalData.proposals || []).length : 0;
    let propDetail;
    if (proposalCount) {
      propDetail = proposalCount === 1 ? 'Una propuesta espera tu decisión' : `${proposalCount} propuestas esperan tu decisión`;
    } else if (activePlan) {
      propDetail = 'Aún no has generado propuestas para este plan';
    } else {
      propDetail = 'Necesitas un plan activo primero';
    }

    const ctxAnswer = ctxPct != null ? ctxPct + '%' : '—';
    let ctxDetail;
    if (ctxPct == null) {
      ctxDetail = 'Revisa tu contexto para saberlo';
    } else if (ctxPct >= 75) {
      ctxDetail = 'Suficiente para proponer con confianza';
    } else if (ctxPct >= 50) {
      ctxDetail = 'Puedes proponer, pero conviene completar más fuentes';
    } else {
      ctxDetail = 'Completa más fuentes antes de proponer';
    }

    $('vs1SignalsGrid').innerHTML = [
      signalCard('¿Qué publicaciones están pendientes?', String(pendingCount), pubDetail),
      signalCard('¿Cuántos prospectos tienes en marketing?', leadsAnswer, leadsDetail),
      signalCard('¿Hay propuestas por decidir?', String(proposalCount), propDetail),
      signalCard('¿Qué tan completo está tu contexto?', ctxAnswer, ctxDetail),
    ].join('');
  }

  function renderPubQueue(posts) {
    const el = $('vs1PubQueue');
    if (!posts || !posts.length) {
      el.innerHTML = `<div class="vs1-empty-task"><p>No tienes publicaciones pendientes.</p><button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" id="vs1GoCalendar">Ver calendario</button></div>`;
      const btn = $('vs1GoCalendar');
      if (btn) btn.onclick = () => { location.href = `/accio/dashboard/${TENANT_ID}/#calendario`; };
      return;
    }
    el.innerHTML = `<ul class="vs1-queue-list">${posts.slice(0, 6).map((p) => {
      const title = (p.preview || '').replace(/…$/, '').trim() || 'Publicación sin texto';
      const meta = `${platformLabel(p.platform)} · ${humanPostStatus(p.status_label)} · ${formatSchedule(p.scheduled_at)}`;
      return `<li class="vs1-queue-item"><p class="vs1-queue-title">${esc(title)}</p><p class="vs1-queue-meta">${esc(meta)}</p></li>`;
    }).join('')}</ul>`;
  }

  async function loadDraftPlansList() {
    const ids = JSON.parse(localStorage.getItem(planSessionKey()) || '[]');
    const plans = [];
    for (const id of ids) {
      if (activePlan && activePlan.id === id) continue;
      try {
        const resp = await v1Api('/marketing-plans/' + encodeURIComponent(id));
        const plan = resp.data;
        if (plan && plan.estado === 'borrador') {
          plans.push(plan);
        }
      } catch (_) { /* skip stale id */ }
    }
    draftPlans = plans;
    return plans;
  }

  function renderDraftPlans(plans) {
    const el = $('vs1DraftPlans');
    if (!plans.length) {
      el.innerHTML = `<div class="vs1-empty-task"><p>No tienes planes guardados sin activar.</p><button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" id="vs1NewDraft">Crear plan</button></div>`;
      $('vs1NewDraft').onclick = () => goWizard();
      return;
    }
    el.innerHTML = `<ul class="vs1-draft-list">${plans.map((p) => {
      const created = (p.created_at || p.updated_at || '').slice(0, 10);
      const when = created ? `Guardado el ${created}` : 'Guardado recientemente';
      return `<li class="vs1-draft-item"><div class="vs1-draft-row">
        <div><p class="vs1-draft-name">${esc(p.nombre)}</p><p class="vs1-draft-sub">${esc(when)}</p></div>
        <button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" data-activate="${esc(p.id)}">Activar</button>
      </div></li>`;
    }).join('')}</ul>`;
    el.querySelectorAll('[data-activate]').forEach((btn) => {
      btn.onclick = () => goActivate(btn.getAttribute('data-activate'));
    });
  }

  async function loadWorkspace() {
    greeting();
    loadAssistantStatus();
    let summary = null;
    try {
      const resp = await v1Api('/marketing-plans/active');
      activePlan = resp.data;
    } catch (e) {
      if (e.message !== 'Sesión expirada') activePlan = null;
      else throw e;
    }
    try {
      summary = await dashFetch('/summary');
    } catch (e) {
      toast(e.message, true);
    }
    if (!contextData && activePlan) {
      try {
        const ctxResp = await v1Api('/marketing-context');
        contextData = ctxResp.data;
        contextUpdatedAt = 'Actualizado recientemente';
      } catch (_) { /* optional for workspace */ }
    }
    renderPlanBanner();
    renderNextAction();
    const ctxPct = contextData ? computeConfidence(contextData) : null;
    renderSignals(summary || {}, ctxPct);
    renderPubQueue(summary ? summary.pending_posts : []);
    try {
      const drafts = await loadDraftPlansList();
      renderDraftPlans(drafts);
    } catch (e) {
      renderDraftPlans([]);
    }
    $('vs1NextSecondary').onclick = () => { showScreen('context'); loadContext(); };
  }

  async function v1Api(path, opts = {}) {
    const res = await fetch(v1Base() + path, {
      ...opts,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Accio-Tenant': TENANT_ID,
        'X-Accio-App': APP_ID,
        ...(opts.headers || {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      location.href = `/accio/login/?next=${encodeURIComponent(location.pathname)}`;
      throw new Error('Sesión expirada');
    }
    if (!res.ok) {
      const msg = data.error?.message || data.error || res.statusText;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function showScreen(name) {
    const screens = {
      workspace: 'vs1ScreenWorkspace',
      wizard: 'vs1ScreenWizard',
      activate: 'vs1ScreenActivate',
      context: 'vs1ScreenContext',
      proposal: 'vs1ScreenProposal',
    };
    Object.entries(screens).forEach(([k, id]) => {
      const el = $(id);
      if (el) el.hidden = k !== name;
    });
    ['vs1TopbarDefault', 'vs1TopbarWizard', 'vs1TopbarContext', 'vs1TopbarProposal', 'vs1TopbarActivate'].forEach((id) => {
      if ($(id)) $(id).hidden = true;
    });
    const topbars = {
      workspace: 'vs1TopbarDefault',
      wizard: 'vs1TopbarWizard',
      activate: 'vs1TopbarActivate',
      context: 'vs1TopbarContext',
      proposal: 'vs1TopbarProposal',
    };
    if (topbars[name] && $(topbars[name])) $(topbars[name]).hidden = false;
    document.querySelectorAll('.vs1-nav-item[data-nav]').forEach((btn) => {
      btn.classList.toggle('is-active', btn.dataset.nav === name || (name === 'wizard' && btn.dataset.nav === 'plan') || (name === 'proposal' && btn.dataset.nav === 'proposals'));
    });
  }

  function greeting() {
    const h = new Date().getHours();
    const sal = h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches';
    $('vs1Greeting').textContent = `${sal}, ${USER_NAME.split(' ')[0] || USER_NAME}`;
    $('vs1Avatar').textContent = (USER_NAME[0] || 'A').toUpperCase();
  }

  function renderPlanBanner() {
    const slot = $('vs1PlanBannerSlot');
    if (!activePlan) {
      slot.innerHTML = `<div class="vs1-card vs1-onboarding">
        <h3>¿Cuál es tu objetivo este trimestre?</h3>
        <p>Define qué quieres lograr antes de publicar o proponer acciones concretas.</p>
        <button type="button" class="vs1-btn vs1-btn--primary" id="vs1OnboardCta">Crear tu primer plan</button>
      </div>`;
      $('vs1OnboardCta').onclick = () => goWizard();
      $('vs1DayStatus').textContent = 'Empieza definiendo tu plan de marketing.';
      return;
    }
    const activated = activePlan.activated_at ? activePlan.activated_at.slice(0, 10) : '';
    const meta = [
      activated ? `En curso desde ${activated}` : '',
      activePlan.north_star_metric ? `Meta: ${activePlan.north_star_metric}` : '',
    ].filter(Boolean).join(' · ');
    slot.innerHTML = `<div class="vs1-card vs1-card--banner-active">
      <span class="vs1-dot-green" aria-hidden="true"></span>
      <div class="vs1-banner-meta">
        <p class="vs1-banner-title">${esc(activePlan.nombre)}</p>
        <p class="vs1-banner-sub">${esc(meta || 'Plan en curso')}</p>
      </div>
      <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ViewPlanBtn">Ver detalle</button>
    </div>`;
    $('vs1ViewPlanBtn').onclick = () => goActivate(activePlan.id);
    $('vs1DayStatus').textContent = `Tu prioridad hoy: avanzar «${activePlan.nombre}».`;
  }

  function renderNextAction() {
    $('vs1NextSecondary').hidden = false;
    if (!activePlan) {
      $('vs1NextTitle').textContent = 'Define tu plan de marketing';
      $('vs1NextDesc').textContent = 'Sin un plan activo, no sabemos qué priorizar para ti.';
      $('vs1NextPrimary').textContent = 'Crear plan';
      $('vs1NextPrimary').onclick = () => goWizard();
      $('vs1NextSecondary').hidden = true;
      return;
    }
    $('vs1NextTitle').textContent = 'Elige tu próximo movimiento estratégico';
    $('vs1NextDesc').textContent = 'Revisa tu contexto y recibe tres opciones concretas para avanzar.';
    $('vs1NextPrimary').textContent = 'Ver opciones estratégicas';
    $('vs1NextPrimary').onclick = () => { showScreen('context'); loadContext(); };
  }

  function goWizard() {
    wizardStep = 0;
    showScreen('wizard');
    renderWizardChrome();
    renderWizardStep();
  }

  function renderWizardChrome() {
    $('vs1WizardSteps').innerHTML = WIZARD_STEPS.map((s, i) => {
      let cls = 'vs1-step-item';
      if (i === wizardStep) cls += ' is-active';
      if (i < wizardStep) cls += ' is-done';
      const inner = i < wizardStep ? '<i class="ti ti-check"></i>' : String(i + 1);
      return `<div class="${cls}"><div class="vs1-step-num">${inner}</div><div class="vs1-step-body"><p class="vs1-step-name">${esc(s.name)}</p><p class="vs1-step-desc">${esc(s.desc)}</p></div></div>`;
    }).join('');
    const pct = ((wizardStep + 1) / WIZARD_STEPS.length) * 100;
    $('vs1WizardBar').style.width = pct + '%';
    $('vs1WizardPrev').disabled = wizardStep === 0;
    $('vs1WizardNext').textContent = wizardStep === WIZARD_STEPS.length - 1 ? 'Guardar y continuar' : 'Siguiente';
  }

  function bindDraftInput(el, field) {
    el.addEventListener('input', () => {
      draft[field] = el.value;
      saveDraft();
    });
  }

  function renderWizardStep() {
    renderWizardChrome();
    const stepId = WIZARD_STEPS[wizardStep].id;
    const question = WIZARD_QUESTIONS[stepId];
    const tip = `<div class="vs1-step-tip"><i class="ti ti-bulb" aria-hidden="true"></i><span>${esc(WIZARD_TIPS[stepId])}</span></div>`;
    let html = `<div class="vs1-wizard-step-intro"><h2 class="vs1-wizard-step-q">${esc(question)}</h2></div>${tip}`;
    const step = stepId;
    if (step === 'name') {
      html += `<div class="vs1-field"><label for="wNombre">Nombre del plan</label><input id="wNombre" value="${esc(draft.nombre)}" placeholder="Plan Q3 2026 — Lanzamiento EN1"></div>
        <div class="vs1-field"><label for="wObj">Tu objetivo en una frase</label><textarea id="wObj" rows="4" placeholder="Incrementar reuniones comerciales con PYME…">${esc(draft.objetivo_general)}</textarea></div>`;
    } else if (step === 'strategy') {
      html += `<div class="vs1-strategy-grid">${STRATEGIES.map((s) => `
        <button type="button" class="vs1-strategy-opt${draft.strategy_type === s.id ? ' is-selected' : ''}" data-strategy="${s.id}">
          <i class="ti ${s.icon}"></i><strong>${esc(s.name)}</strong><span>${esc(s.desc)}</span>
        </button>`).join('')}</div>`;
    } else if (step === 'audience') {
      html += `<div class="vs1-field"><label for="wAud">Describe a tu audiencia</label><textarea id="wAud" rows="5" placeholder="Un perfil por línea">${esc(draft.publico_objetivo)}</textarea></div>`;
    } else if (step === 'metrics') {
      html += `<div class="vs1-field"><label for="wNorth">Meta principal</label><input id="wNorth" value="${esc(draft.north_star_metric)}" placeholder="Reuniones comerciales al mes"></div>
        <div class="vs1-field"><label for="wCrit">Hitos que confirman el progreso</label><textarea id="wCrit" rows="4" placeholder="Un hito por línea">${esc(draft.success_criteria)}</textarea></div>
        <div class="vs1-field"><label for="wIni">Fecha de inicio</label><input id="wIni" type="date" value="${esc(draft.periodo_inicio)}"></div>
        <div class="vs1-field"><label for="wFin">Fecha de fin</label><input id="wFin" type="date" value="${esc(draft.periodo_fin)}"></div>`;
    } else {
      html += `<div class="vs1-field"><label for="wBrief">Contexto adicional</label><textarea id="wBrief" rows="8" placeholder="Restricciones, mensajes clave, competencia local…">${esc(draft.marketing_brief)}</textarea></div>`;
    }
    $('vs1WizardStepContent').innerHTML = html;
    if (step === 'name') {
      bindDraftInput($('wNombre'), 'nombre');
      bindDraftInput($('wObj'), 'objetivo_general');
    } else if (step === 'strategy') {
      document.querySelectorAll('[data-strategy]').forEach((btn) => {
        btn.onclick = () => {
          draft.strategy_type = btn.dataset.strategy;
          saveDraft();
          renderWizardStep();
        };
      });
    } else if (step === 'audience') {
      bindDraftInput($('wAud'), 'publico_objetivo');
    } else if (step === 'metrics') {
      bindDraftInput($('wNorth'), 'north_star_metric');
      bindDraftInput($('wCrit'), 'success_criteria');
      bindDraftInput($('wIni'), 'periodo_inicio');
      bindDraftInput($('wFin'), 'periodo_fin');
    } else {
      bindDraftInput($('wBrief'), 'marketing_brief');
    }
  }

  function parseLines(raw) {
    return String(raw || '').split('\n').map((s) => s.trim()).filter(Boolean);
  }

  async function submitDraft() {
    if (!draft.periodo_inicio) draft.periodo_inicio = '2026-07-01';
    if (!draft.periodo_fin) draft.periodo_fin = '2026-09-30';
    const body = {
      nombre: draft.nombre,
      objetivo_general: draft.objetivo_general,
      strategy_type: draft.strategy_type,
      north_star_metric: draft.north_star_metric,
      success_criteria: parseLines(draft.success_criteria),
      publico_objetivo: parseLines(draft.publico_objetivo),
      marketing_brief: draft.marketing_brief || draft.objetivo_general,
      periodo: { inicio: draft.periodo_inicio, fin: draft.periodo_fin },
      budget: { amount: String(draft.budget_amount || '0'), currency: 'USD' },
      prioridad: draft.prioridad || 'media',
    };
    const resp = await v1Api('/marketing-plans', { method: 'POST', body: JSON.stringify(body) });
    rememberPlanId(resp.data.id);
    draftPlans.push(resp.data);
    toast('Plan guardado');
    goActivate(resp.data.id);
  }

  function goActivate(planId) {
    activateTarget = planId;
    showScreen('activate');
    renderActivate();
  }

  async function renderActivate() {
    let plan = draftPlans.find((p) => p.id === activateTarget);
    if (!plan) {
      try {
        const resp = await v1Api('/marketing-plans/' + encodeURIComponent(activateTarget));
        plan = resp.data;
      } catch (e) {
        toast(e.message, true);
        showScreen('workspace');
        return;
      }
    }
    let otherActive = null;
    if (activePlan && activePlan.id !== plan.id) {
      otherActive = activePlan;
    } else {
      try {
        const r = await v1Api('/marketing-plans/active');
        if (r.data && r.data.id !== plan.id) otherActive = r.data;
      } catch (_) { /* ignore */ }
    }
    const pub = Array.isArray(plan.publico_objetivo) ? plan.publico_objetivo.join(', ') : plan.publico_objetivo;
    $('vs1ActivateCard').innerHTML = `
      <div class="vs1-activate-block">
        <p class="vs1-page-label">Activar plan</p>
        <h2 class="vs1-page-title" style="margin-bottom:6px">${esc(plan.nombre)}</h2>
        <p class="vs1-page-sub" style="margin:0">Al activar, la IA usará este plan como referencia estratégica principal.</p>
      </div>
      <div class="vs1-activate-block">
        <div class="vs1-meta-grid">
          <div class="vs1-meta-item"><span>Objetivo</span><strong>${esc((plan.objetivo_general || '').slice(0, 80))}</strong></div>
          <div class="vs1-meta-item"><span>Estrategia</span><strong>${esc(plan.strategy_type)}</strong></div>
          <div class="vs1-meta-item"><span>Público objetivo</span><strong>${esc(pub || '—')}</strong></div>
          <div class="vs1-meta-item"><span>North Star Metric</span><strong>${esc(plan.north_star_metric || '—')}</strong></div>
        </div>
      </div>
      ${otherActive ? `<div class="vs1-activate-block"><div class="vs1-conflict-banner"><i class="ti ti-alert-triangle"></i><div><strong>Conflicto R2:</strong> El plan «${esc(otherActive.nombre)}» está activo. Al continuar, debes finalizarlo o pausarlo.</div></div></div>` : ''}
      <div class="vs1-activate-block">
        <ul class="vs1-impact-list">
          <li class="vs1-impact-item"><span class="vs1-impact-icon vs1-impact-icon--ok"><i class="ti ti-brain"></i></span><div><strong>Contexto IA actualizado</strong><p>El Context Builder priorizará este plan en las propuestas.</p></div></li>
          <li class="vs1-impact-item"><span class="vs1-impact-icon vs1-impact-icon--ok"><i class="ti ti-chart-line"></i></span><div><strong>North Star operativa</strong><p>Las acciones recomendadas se alinearán a ${esc(plan.north_star_metric || 'tu métrica')}.</p></div></li>
          <li class="vs1-impact-item"><span class="vs1-impact-icon vs1-impact-icon--warn"><i class="ti ti-switch-horizontal"></i></span><div><strong>Plan anterior</strong><p>${otherActive ? 'Requiere resolución: finalizar o pausar el plan activo actual.' : 'No hay otro plan activo; activación directa.'}</p></div></li>
        </ul>
      </div>
      <div class="vs1-activate-block vs1-activate-footer" id="vs1ActFooter">
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActCancel">Cancelar</button>
        <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ActGo"><i class="ti ti-player-play"></i> Activar plan</button>
      </div>`;
    $('vs1ActCancel').onclick = () => { showScreen('workspace'); loadWorkspace(); };
    if (otherActive) {
      $('vs1ActFooter').innerHTML = `
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActCancel">Cancelar</button>
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActPause">Activar · pausar anterior</button>
        <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ActFinalize"><i class="ti ti-player-play"></i> Activar · finalizar anterior</button>`;
      $('vs1ActCancel').onclick = () => { showScreen('workspace'); loadWorkspace(); };
      $('vs1ActPause').onclick = () => doActivate(plan.id, 'pause_previous');
      $('vs1ActFinalize').onclick = () => doActivate(plan.id, 'finalize_previous');
    } else {
      $('vs1ActGo').onclick = () => doActivate(plan.id, null);
    }
  }

  async function doActivate(planId, resolution) {
    try {
      const body = resolution ? { resolution } : {};
      const resp = await v1Api('/marketing-plans/' + encodeURIComponent(planId) + '/activate', { method: 'POST', body: JSON.stringify(body) });
      activePlan = resp.data;
      toast('Plan activado');
      showScreen('workspace');
      await loadWorkspace();
    } catch (e) {
      toast(e.message, true);
    }
  }

  function sourceRows(data) {
    const biz = data.business_context || {};
    const app = data.app_profile || {};
    const kb = data.knowledge_base || [];
    const plan = data.marketing_plan_active;
    const companyName = biz.empresa || biz.company || biz.display_name || '';
    const tone = app.tone || biz.tono_comunicacion || '';
    return [
      {
        id: 'company',
        name: 'Perfil de la empresa',
        meta: companyName || 'Sin completar',
        meaning: companyName ? 'Identidad y sector disponibles para la IA' : 'Define quién eres y a quién vendes',
        status: companyName ? 'complete' : 'incomplete',
      },
      {
        id: 'plan',
        name: 'Plan activo',
        meta: plan ? plan.nombre : 'Sin plan activo',
        meaning: plan ? 'Estrategia y North Star alineados' : 'Activa un plan para orientar propuestas',
        status: plan ? 'complete' : 'incomplete',
      },
      {
        id: 'kb',
        name: 'Base de conocimiento',
        meta: kb.length ? `${kb.length} artículo${kb.length === 1 ? '' : 's'}` : 'Sin artículos',
        meaning: kb.length >= 2 ? 'Material suficiente para propuestas' : kb.length ? 'Agrega más artículos para mayor precisión' : 'Añade contenido sobre productos y servicios',
        status: kb.length >= 2 ? 'complete' : kb.length ? 'incomplete' : 'incomplete',
      },
      {
        id: 'brand',
        name: 'Branding y tono de voz',
        meta: tone || 'Sin definir',
        meaning: tone ? 'La IA respetará tu estilo de comunicación' : 'Define cómo debe sonar tu marca',
        status: tone ? 'complete' : 'incomplete',
      },
      {
        id: 'campaigns',
        name: 'Campañas anteriores',
        meta: 'Próximamente',
        meaning: 'Historial de campañas en una fase posterior',
        status: 'na',
      },
      {
        id: 'metrics',
        name: 'Métricas de rendimiento',
        meta: 'Próximamente',
        meaning: 'Resultados pasados en una fase posterior',
        status: 'na',
      },
    ];
  }

  function sourceStatusLabel(status) {
    if (status === 'complete') return 'Listo';
    if (status === 'incomplete') return 'Pendiente';
    return 'Próximamente';
  }

  function sourceFixUrl(sourceId) {
    const dash = `/accio/dashboard/${encodeURIComponent(TENANT_ID)}/`;
    const map = {
      company: dash + '#conocimiento',
      kb: dash + '#conocimiento',
      brand: dash + '#conocimiento',
      plan: `/accio/plan/${encodeURIComponent(TENANT_ID)}/`,
    };
    return map[sourceId] || dash + '#conocimiento';
  }

  function confidenceMeaning(pct) {
    if (pct >= 75) return 'Contexto sólido — puedes generar propuestas con confianza';
    if (pct >= 50) return 'Contexto parcial — completa fuentes pendientes para mejorar precisión';
    return 'Contexto limitado — las propuestas serán genéricas hasta completar fuentes';
  }

  function computeConfidence(data) {
    const rows = sourceRows(data);
    const scorable = rows.filter((r) => r.status !== 'na');
    const score = scorable.filter((r) => r.status === 'complete').length;
    return scorable.length ? Math.round((score / scorable.length) * 100) : 0;
  }

  async function loadContext() {
    try {
      const resp = await v1Api('/marketing-context');
      contextData = resp.data;
      contextUpdatedAt = 'Actualizado recientemente';
      $('vs1ContextTs').textContent = contextUpdatedAt;

      const plan = contextData.marketing_plan_active;
      const planRef = $('vs1ContextPlanRef');
      if (plan) {
        planRef.hidden = false;
        $('vs1ContextPlanName').textContent = plan.nombre;
        $('vs1ContextPlanMeta').textContent = `North Star: ${plan.north_star_metric || '—'}`;
      } else {
        planRef.hidden = true;
      }

      const pct = computeConfidence(contextData);
      $('vs1ConfidenceCard').innerHTML = `
        <div class="vs1-confidence-num">${pct}%</div>
        <div class="vs1-confidence-body">
          <p class="vs1-label-upper" style="margin:0">Nivel de confianza del contexto</p>
          <div class="vs1-progress-track"><div class="vs1-progress-fill" style="width:${pct}%"></div></div>
          <p class="vs1-banner-sub">${esc(confidenceMeaning(pct))}</p>
        </div>`;

      const rows = sourceRows(contextData);
      $('vs1SourcesList').innerHTML = rows.map((r) => {
        const iconCls = r.status === 'complete' ? 'ok' : r.status === 'incomplete' ? 'warn' : 'na';
        const badge = r.status === 'complete' ? 'vs1-badge--ok' : r.status === 'incomplete' ? 'vs1-badge--warn' : '';
        const label = sourceStatusLabel(r.status);
        const naCls = r.status === 'na' ? ' is-na' : '';
        return `<button type="button" class="vs1-source-row${naCls}" data-source="${r.id}"${r.status === 'na' ? ' disabled' : ''}>
          <span class="vs1-source-icon vs1-source-icon--${iconCls}"><i class="ti ti-${iconCls === 'ok' ? 'check' : iconCls === 'warn' ? 'alert-circle' : 'minus'}"></i></span>
          <span class="vs1-source-body">
            <p class="vs1-source-name">${esc(r.name)}</p>
            <p class="vs1-source-meta">${esc(r.meta)}</p>
            <p class="vs1-source-meaning">${esc(r.meaning)}</p>
          </span>
          <span class="vs1-badge ${badge}">${label}</span>
          ${r.status === 'na' ? '' : '<i class="ti ti-chevron-right vs1-source-chevron"></i>'}
        </button>`;
      }).join('');

      $('vs1SourcesList').querySelectorAll('.vs1-source-row:not(.is-na)').forEach((btn) => {
        btn.onclick = () => { location.href = sourceFixUrl(btn.dataset.source); };
      });

      const incomplete = rows.find((r) => r.status === 'incomplete');
      const nextBanner = $('vs1ContextNextBanner');
      const nextCta = $('vs1ContextNextCta');
      if (incomplete) {
        nextBanner.hidden = false;
        $('vs1ContextNextText').textContent = `Completa «${incomplete.name}» para que las propuestas reflejen mejor tu negocio.`;
        nextCta.textContent = `Ir a ${incomplete.name}`;
        nextCta.onclick = () => { location.href = sourceFixUrl(incomplete.id); };
      } else {
        nextBanner.hidden = true;
      }
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function loadProposal() {
    if (!activePlan) {
      try {
        const r = await v1Api('/marketing-plans/active');
        activePlan = r.data;
      } catch (_) { /* ignore */ }
    }
    if (!activePlan) {
      toast('Activa un plan antes de generar propuestas', true);
      showScreen('workspace');
      return;
    }
    $('vs1PropPlanName').textContent = activePlan.nombre;
    $('vs1ProposalMain').innerHTML = '<p class="vs1-page-sub">Generando propuesta…</p>';
    try {
      if (!contextData) await loadContext();
      const resp = await v1Api('/planner/proposals', { method: 'POST', body: '{}' });
      proposalData = resp.data;
      const p = (proposalData.proposals || [])[0];
      if (!p) throw new Error('Sin propuestas');
      const opps = (p.actions || []).map((a) => `<li><i class="ti ti-check"></i><span>${esc(a)}</span></li>`).join('');
      const all = proposalData.proposals || [];
      $('vs1ProposalMain').innerHTML = `
        <div class="vs1-doc-header">
          <div class="vs1-doc-label"><i class="ti ti-sparkles"></i> Generado por EM+Acción IA</div>
          <h1 class="vs1-doc-title">${esc(p.title)}</h1>
          <p class="vs1-doc-meta">${esc(window.__ACCIO_EMPRESA_NAME__ || TENANT_ID)} · ${new Date().toLocaleDateString('es-PA')} · ${(contextData?.knowledge_base || []).length} fuentes</p>
        </div>
        <div class="vs1-section"><h3>Resumen ejecutivo</h3><div class="vs1-exec-card">${esc(proposalData.executive_summary || '')}</div></div>
        <div class="vs1-section"><h3>Oportunidades identificadas</h3><ul class="vs1-opp-list">${opps || '<li><i class="ti ti-check"></i><span>—</span></li>'}</ul></div>
        <div class="vs1-section"><h3>Propuestas priorizadas</h3>
          ${all.map((row, i) => {
            const conf = i === 0 ? 88 : i === 1 ? 72 : 65;
            return `<div class="vs1-priority-card${i === 0 ? ' is-recommended' : ''}">
              <div class="vs1-priority-head"><span class="vs1-priority-num">${i + 1}</span><h4>${esc(row.title)}</h4>${i === 0 ? '<span class="vs1-badge vs1-badge--rec">Recomendada</span>' : ''}</div>
              <p class="vs1-priority-type">${esc(row.channel_hint || '')} · Prioridad ${esc(row.priority || 'media')}</p>
              <p>${esc(row.summary || '')}</p>
              <div class="vs1-confidence-bar"><div class="vs1-progress-track"><div class="vs1-progress-fill" style="width:${conf}%"></div></div><span>${conf}% confianza</span></div>
            </div>`;
          }).join('')}
        </div>`;
      const rows = contextData ? sourceRows(contextData) : [];
      $('vs1ProposalAside').innerHTML = `
        <div class="vs1-aside-block"><h4>Contexto utilizado</h4><ul class="vs1-ctx-used">
          ${rows.map((r) => `<li><i class="ti ti-${r.status === 'complete' ? 'check ok' : 'minus na'}"></i> ${esc(r.name)}</li>`).join('')}
        </ul></div>
        <div class="vs1-aside-divider"></div>
        <div class="vs1-aside-block"><h4>Tu decisión</h4>
          <div class="vs1-aside-actions">
            <button type="button" class="vs1-btn vs1-btn--primary" id="vs1Approve">Aprobar propuesta</button>
            <textarea id="vs1Feedback" placeholder="¿Qué quieres cambiar?"></textarea>
            <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1RequestChanges">Solicitar cambios</button>
            <button type="button" class="vs1-btn vs1-btn--ghost vs1-btn--sm" id="vs1Regen">Generar otra propuesta</button>
          </div>
        </div>`;
      $('vs1Approve').onclick = () => toast('Propuesta aprobada (registro pendiente Fase C)');
      $('vs1RequestChanges').onclick = () => toast('Solicitud registrada (integración pendiente Fase C)');
      $('vs1Regen').onclick = () => loadProposal();
    } catch (e) {
      toast(e.message, true);
    }
  }

  function initNav() {
    document.querySelectorAll('.vs1-nav-item[data-nav]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const nav = btn.dataset.nav;
        if (nav === 'workspace') { showScreen('workspace'); loadWorkspace(); }
        else if (nav === 'plan') goWizard();
        else if (nav === 'context') { showScreen('context'); loadContext(); }
        else if (nav === 'proposals') { showScreen('proposal'); loadProposal(); }
        else if (nav === 'connectors') location.href = `/accio/dashboard/${TENANT_ID}/#conectores`;
        else if (nav === 'config') location.href = `/accio/dashboard/${TENANT_ID}/#configuracion`;
      });
    });
  }

  function initTenantSelect() {
    const sel = $('vs1TenantSelect');
    if (!sel || !TENANTS.length) {
      if (sel) sel.innerHTML = `<option>${TENANT_ID}</option>`;
      return;
    }
    sel.innerHTML = TENANTS.map((t) => `<option value="${esc(t.id)}"${t.id === TENANT_ID ? ' selected' : ''}>${esc(t.label || t.id)}</option>`).join('');
    sel.onchange = () => {
      location.href = `/accio/plan/${sel.value}/`;
    };
  }

  function initWizardNav() {
    $('vs1BackWorkspace').onclick = () => { showScreen('workspace'); loadWorkspace(); };
    $('vs1WizardPrev').onclick = () => {
      if (wizardStep > 0) { wizardStep -= 1; renderWizardStep(); }
    };
    $('vs1WizardNext').onclick = async () => {
      if (wizardStep < WIZARD_STEPS.length - 1) {
        wizardStep += 1;
        renderWizardStep();
        return;
      }
      try {
        await submitDraft();
      } catch (e) {
        toast(e.message, true);
      }
    };
  }

  function initTopActions() {
    $('vs1GenProposalBtn').onclick = () => { showScreen('proposal'); loadProposal(); };
    $('vs1ViewCtxBtn').onclick = () => { showScreen('context'); loadContext(); };
    $('vs1ExportBtn').onclick = () => toast('Exportación disponible en Fase C');
  }

  async function bootstrap() {
    initTenantSelect();
    initNav();
    initWizardNav();
    initTopActions();
    showScreen('workspace');
    await loadWorkspace();
    const hash = location.hash.replace('#', '');
    if (hash === 'crear') goWizard();
    if (hash === 'contexto') { showScreen('context'); loadContext(); }
    if (hash === 'propuestas') { showScreen('proposal'); loadProposal(); }
  }

  bootstrap();
})();
