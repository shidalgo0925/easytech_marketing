(function () {
  'use strict';

  const TENANT_ID = window.__ACCIO_TENANT__ || 'easytech';
  const APP_ID = window.__ACCIO_APP__ || localStorage.getItem(`accio_app_${TENANT_ID}`) || 'default';
  const USER_NAME = window.__ACCIO_USER_NAME__ || 'Administrador';
  const TENANTS = window.__ACCIO_TENANTS__ || [];
  const BRANDING = window.__ACCIO_BRANDING__ || {};

  function initBranding() {
    const logo = BRANDING.logo_url;
    const isCustom = logo && !logo.endsWith('em-logomark.svg');
    document.querySelectorAll('.brand-icon, .vs1-brand-logo').forEach((img) => {
      if (isCustom) {
        img.src = logo;
        img.hidden = false;
      } else {
        img.hidden = true;
      }
    });
    document.querySelectorAll('.topbar-mark, .vs1-logo-mark').forEach((svg) => {
      svg.hidden = isCustom;
    });
    const name = BRANDING.display_name || window.__ACCIO_EMPRESA_NAME__ || TENANT_ID;
    document.title = `${name} — EM+Acción`;
  }

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
  let pendingAssistantOrders = [];
  let proposalsPendingDecision = false;
  let currentArea = 'workspace';
  let planSubview = 'resumen';

  const AREA_VIEWS = {
    workspace: 'vs1ViewWorkspace',
    plan: 'vs1ViewPlan',
    context: 'vs1ViewContext',
    proposals: 'vs1ViewProposals',
    publications: 'vs1ViewPublications',
    clients: 'vs1ViewClients',
    operations: 'vs1ViewOperations',
    config: 'vs1ViewConfig',
  };

  const EMBED_FRAMES = {
    operations: { id: 'vs1OpsFrame', defaultTab: 'resumen' },
    publications: { id: 'vs1PubFrame', defaultTab: 'publicaciones' },
    clients: { id: 'vs1ClientsFrame', defaultTab: 'resumen' },
    config: { id: 'vs1ConfigFrame', defaultTab: 'configuracion' },
  };

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
    const autosave = $('vs1Autosave');
    if (autosave) {
      autosave.textContent = 'Guardado automáticamente · ' + new Date().toLocaleTimeString('es-PA', { hour: '2-digit', minute: '2-digit' });
    }
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

  function opsEmbeddedUrl(tab) {
    const base = `/accio/dashboard/${encodeURIComponent(TENANT_ID)}/?vista=operaciones&embedded=1&app_id=${encodeURIComponent(APP_ID)}`;
    return tab ? `${base}&tab=${encodeURIComponent(tab)}` : base;
  }

  function opsUrl(tab) {
    return opsEmbeddedUrl(tab);
  }

  function loadEmbedFrame(area, tab) {
    const cfg = EMBED_FRAMES[area];
    if (!cfg) return;
    const iframe = $(cfg.id);
    if (!iframe) return;
    const t = tab || cfg.defaultTab;
    const url = opsEmbeddedUrl(t);
    if (iframe.dataset.loadedTab !== t) {
      iframe.src = url;
      iframe.dataset.loadedTab = t;
    }
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
    const iaLabel = $('vs1IaLabel');
    const iaDot = $('vs1IaDot');
    const iaInd = $('vs1IaIndicator');
    try {
      const res = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/assistant/status`, { credentials: 'include' });
      const data = await res.json().catch(() => ({}));
      if (!data.ok) {
        if (iaLabel) iaLabel.textContent = 'IA —';
        return;
      }
      const active = data.llm_available && data.assistant_enabled;
      if (iaLabel) {
        if (!data.assistant_enabled) iaLabel.textContent = 'IA off';
        else if (active) iaLabel.textContent = 'IA activa';
        else if (!data.provider_configured) iaLabel.textContent = 'IA sin motor';
        else if (!data.provider_reachable) iaLabel.textContent = 'IA no alcanzable';
        else iaLabel.textContent = 'IA inactiva';
      }
      if (iaInd) {
        iaInd.classList.remove('is-active', 'is-off');
        if (active) iaInd.classList.add('is-active');
        else iaInd.classList.add('is-off');
      }
      if (iaDot) iaDot.hidden = true;
      if (!banner) return;
      if (data.llm_available) {
        banner.hidden = true;
        return;
      }
      banner.hidden = false;
      bannerTitle.textContent = '¿Quieres recomendaciones personalizadas?';
      bannerCta.textContent = 'Configurar asistente';
      bannerCta.onclick = () => navigateTo('config');
      if (!data.assistant_enabled) {
        bannerText.textContent = 'Activa el asistente en Configuración para recibir propuestas alineadas a tu negocio.';
      } else if (!data.provider_configured) {
        bannerText.textContent = 'El motor de IA (LiteLLM en CODITO) aún no está configurado en el servidor. El administrador debe definir ACCIO_AI_BASE_URL.';
      } else if (!data.provider_reachable) {
        bannerText.textContent = 'El proveedor de IA no responde desde este servidor. Revisa conectividad hacia CODITO.';
      } else {
        bannerText.textContent = 'El asistente está listo pero desactivado. Actívalo en Configuración cuando quieras usarlo.';
      }
    } catch (_) {
      if (iaLabel) iaLabel.textContent = 'IA —';
    }
  }

  function proposalsStorageKey() {
    return `vs1_proposals_${TENANT_ID}_${APP_ID}`;
  }

  function loadStoredProposals() {
    proposalsPendingDecision = false;
    try {
      const raw = JSON.parse(localStorage.getItem(proposalsStorageKey()) || 'null');
      if (raw && activePlan && raw.planId === activePlan.id && raw.pending && raw.data) {
        proposalData = raw.data;
        proposalsPendingDecision = true;
        return true;
      }
    } catch (_) { /* ignore */ }
    proposalData = null;
    return false;
  }

  function storeProposalsPending(data) {
    if (!activePlan) return;
    proposalData = data;
    proposalsPendingDecision = true;
    localStorage.setItem(proposalsStorageKey(), JSON.stringify({
      planId: activePlan.id,
      data,
      pending: true,
    }));
  }

  function clearStoredProposals() {
    proposalsPendingDecision = false;
    localStorage.removeItem(proposalsStorageKey());
  }

  async function loadAssistantOrders() {
    try {
      const res = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/assistant/orders`, { credentials: 'include' });
      const data = await res.json().catch(() => ({}));
      pendingAssistantOrders = data.ok ? (data.orders || []) : [];
    } catch (_) {
      pendingAssistantOrders = [];
    }
  }

  function signalCard(question, answer, detail, action) {
    const cls = action ? 'vs1-signal-card is-clickable' : 'vs1-signal-card';
    const attrs = action ? ` data-signal-action="${action}" role="button" tabindex="0"` : '';
    return `<div class="${cls}"${attrs}>
      <p class="vs1-signal-label">${esc(question)}</p>
      <p class="vs1-signal-value">${esc(answer)}</p>
      ${detail ? `<p class="vs1-signal-meaning">${esc(detail)}</p>` : ''}
    </div>`;
  }

  function bindSignalActions() {
    $('vs1SignalsGrid').querySelectorAll('[data-signal-action]').forEach((el) => {
      const run = () => handleSignalAction(el.dataset.signalAction);
      el.addEventListener('click', run);
      el.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          run();
        }
      });
    });
  }

  function handleSignalAction(action) {
    if (action === 'publications') {
      navigateTo('publications');
      return;
    }
    if (action === 'leads') {
      navigateTo('clients');
      return;
    }
    if (action === 'proposals') {
      navigateTo('proposals');
      return;
    }
    if (action === 'context') {
      navigateTo('context');
    }
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

    const proposalCount = proposalsPendingDecision && proposalData && (proposalData.proposals || []).length
      ? (proposalData.proposals || []).length
      : 0;
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
      signalCard('¿Qué publicaciones están pendientes?', String(pendingCount), pubDetail, 'publications'),
      signalCard('¿Cuántos prospectos tienes en marketing?', leadsAnswer, leadsDetail, 'leads'),
      signalCard('¿Hay propuestas por decidir?', String(proposalCount), propDetail, 'proposals'),
      signalCard('¿Qué tan completo está tu contexto?', ctxAnswer, ctxDetail, 'context'),
    ].join('');
    bindSignalActions();
  }

  function renderPubQueue(posts) {
    const el = $('vs1PubQueue');
    if (!posts || !posts.length) {
      el.innerHTML = `<div class="vs1-empty-task"><p>No tienes publicaciones pendientes.</p><button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" id="vs1GoCalendar">Ver calendario</button></div>`;
      const btn = $('vs1GoCalendar');
      if (btn) btn.onclick = () => navigateTo('publications');
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

  function renderPendingAttention(assistantOrders, plans) {
    const el = $('vs1DraftPlans');
    const items = [];
    (assistantOrders || []).forEach((o) => items.push({ kind: 'assistant', data: o }));
    (plans || []).forEach((p) => items.push({ kind: 'plan', data: p }));

    if (!items.length) {
      el.innerHTML = `<div class="vs1-empty-task"><p>No hay borradores ni planes esperando tu decisión.</p><button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" id="vs1NewDraft">Crear plan</button></div>`;
      $('vs1NewDraft').onclick = () => goWizard();
      return;
    }

    el.innerHTML = `<ul class="vs1-draft-list">${items.map((item) => {
      if (item.kind === 'assistant') {
        const o = item.data;
        const preview = (o.preview || [])[0];
        const snippet = preview ? String(preview.text || '').replace(/\s+/g, ' ').trim().slice(0, 72) : (o.title || 'Publicación sugerida');
        const channel = platformLabel(o.channel || (preview && preview.platform));
        return `<li class="vs1-draft-item"><div class="vs1-draft-row">
          <div><span class="vs1-pending-tag">Borrador IA</span><p class="vs1-draft-name">${esc(snippet)}${snippet.length >= 72 ? '…' : ''}</p>
          <p class="vs1-draft-sub">${esc(channel)} · Sugerida hoy</p></div>
          <button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" data-review-order="${esc(o.id)}">Revisar</button>
        </div></li>`;
      }
      const p = item.data;
      const created = (p.created_at || p.updated_at || '').slice(0, 10);
      const when = created ? `Guardado el ${created}` : 'Guardado recientemente';
      return `<li class="vs1-draft-item"><div class="vs1-draft-row">
        <div><span class="vs1-pending-tag">Plan</span><p class="vs1-draft-name">${esc(p.nombre)}</p><p class="vs1-draft-sub">${esc(when)}</p></div>
        <button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" data-activate="${esc(p.id)}">Activar</button>
      </div></li>`;
    }).join('')}</ul>`;

    el.querySelectorAll('[data-activate]').forEach((btn) => {
      btn.onclick = () => goActivate(btn.getAttribute('data-activate'));
    });
    el.querySelectorAll('[data-review-order]').forEach((btn) => {
      btn.onclick = () => {
        const order = assistantOrders.find((o) => o.id === btn.getAttribute('data-review-order'));
        if (order) openAssistantReview(order);
      };
    });
  }

  async function loadWorkspace() {
    greeting();
    loadAssistantStatus();
    await loadAssistantOrders();
    let summary = null;
    try {
      const resp = await v1Api('/marketing-plans/active');
      activePlan = resp.data;
    } catch (e) {
      if (e.message !== 'Sesión expirada') activePlan = null;
      else throw e;
    }
    if (activePlan) {
      loadStoredProposals();
      if (!contextData) {
        try {
          const ctxResp = await v1Api('/marketing-context');
          contextData = ctxResp.data;
          contextUpdatedAt = 'Actualizado recientemente';
        } catch (_) { /* optional for workspace */ }
      }
    } else {
      contextData = null;
      clearStoredProposals();
    }
    try {
      summary = await dashFetch('/summary');
    } catch (e) {
      toast(e.message, true);
    }
    const ctxPct = contextData ? computeConfidence(contextData) : null;
    const posts = summary ? summary.pending_posts : [];
    renderPlanBanner();
    renderNextAction(posts, ctxPct);
    renderSignals(summary || {}, ctxPct);
    renderPubQueue(posts);
    try {
      const drafts = await loadDraftPlansList();
      renderPendingAttention(pendingAssistantOrders, drafts);
    } catch (e) {
      renderPendingAttention(pendingAssistantOrders, []);
    }
    await loadDecisionConsole();
  }

  function pickNextAction(posts, ctxPct) {
    const firstOrder = pendingAssistantOrders[0];
    if (firstOrder) {
      return {
        title: 'Revisa la publicación sugerida',
        desc: 'El asistente preparó un borrador que espera tu aprobación antes de encolarlo.',
        primary: 'Revisar publicación sugerida',
        onPrimary: () => openAssistantReview(firstOrder),
        secondary: 'Ver todas las publicaciones',
        onSecondary: () => navigateTo('publications'),
      };
    }

    const queue = posts || [];
    if (queue.length) {
      const p = queue[0];
      const channel = platformLabel(p.platform);
      const snippet = (p.preview || '').replace(/…$/, '').trim();
      return {
        title: `Tienes una publicación lista para ${channel}`,
        desc: snippet
          ? `Revisa el texto y confirma si quieres publicarla: «${snippet.slice(0, 90)}${snippet.length > 90 ? '…' : ''}»`
          : 'Revisa el contenido y confirma si quieres publicarla.',
        primary: 'Revisar publicación',
        onPrimary: () => openPostReview(p),
        secondary: 'Ver calendario',
        onSecondary: () => navigateTo('publications'),
      };
    }

    if (!activePlan) {
      return {
        title: 'Define tu plan de marketing',
        desc: 'Sin un plan activo, no sabemos qué priorizar para ti.',
        primary: 'Crear plan',
        onPrimary: () => goWizard(),
        secondary: null,
      };
    }

    if (proposalsPendingDecision && proposalData && (proposalData.proposals || []).length) {
      return {
        title: 'Tienes propuestas por revisar',
        desc: 'Compara las opciones estratégicas y elige con cuál avanzar.',
        primary: 'Ver propuestas',
        onPrimary: () => { navigateTo('proposals'); },
        secondary: 'Ver contexto',
        onSecondary: () => navigateTo('context'),
      };
    }

    if (ctxPct != null && ctxPct < 50) {
      return {
        title: 'Completa tu contexto',
        desc: 'Falta información sobre tu negocio para proponer con precisión.',
        primary: 'Completar contexto',
        onPrimary: () => navigateTo('context'),
        secondary: null,
      };
    }

    return {
      title: 'Elige tu próximo movimiento estratégico',
      desc: 'Revisa tu contexto y recibe tres opciones concretas para avanzar.',
      primary: 'Ver opciones estratégicas',
      onPrimary: () => navigateTo('context'),
      secondary: 'Ver contexto',
      onSecondary: () => navigateTo('context'),
    };
  }

  function renderNextAction(posts, ctxPct) {
    const action = pickNextAction(posts, ctxPct);
    $('vs1NextTitle').textContent = action.title;
    $('vs1NextDesc').textContent = action.desc;
    $('vs1NextPrimary').textContent = action.primary;
    $('vs1NextPrimary').onclick = action.onPrimary;

    const sec = $('vs1NextSecondary');
    if (action.secondary && action.onSecondary) {
      sec.hidden = false;
      sec.textContent = action.secondary;
      sec.onclick = action.onSecondary;
    } else {
      sec.hidden = true;
    }
  }

  function closeReviewModal() {
    const modal = $('vs1ReviewModal');
    if (modal) modal.hidden = true;
  }

  function openReviewModal(title, bodyHtml, footHtml) {
    $('vs1ReviewTitle').textContent = title;
    $('vs1ReviewBody').innerHTML = bodyHtml;
    $('vs1ReviewFoot').innerHTML = footHtml;
    $('vs1ReviewModal').hidden = false;
    $('vs1ReviewClose').onclick = closeReviewModal;
    $('vs1ReviewBackdrop').onclick = closeReviewModal;
  }

  function openAssistantReview(order) {
    const preview = (order.preview || [])[0];
    const text = preview ? String(preview.text || '').trim() : '';
    const channel = platformLabel(order.channel || (preview && preview.platform));
    const body = `${text ? `<p>${esc(text)}</p>` : '<p class="vs1-review-meta">Sin vista previa de texto.</p>'}
      <p class="vs1-review-meta">${esc(channel)} · ${esc(order.title || 'Borrador del asistente')}</p>`;
    const foot = `
      <button type="button" class="vs1-btn vs1-btn--ghost" id="vs1ReviewReject">Rechazar</button>
      <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ReviewApprove">Aprobar y encolar</button>`;
    openReviewModal('Revisar publicación sugerida', body, foot);
    $('vs1ReviewReject').onclick = async () => {
      try {
        await rejectAssistantOrder(order.id);
        closeReviewModal();
        await loadWorkspace();
      } catch (e) { toast(e.message, true); }
    };
    $('vs1ReviewApprove').onclick = async () => {
      try {
        await approveAssistantOrder(order.id);
        closeReviewModal();
        await loadWorkspace();
      } catch (e) { toast(e.message, true); }
    };
  }

  function openPostReview(post) {
    const text = (post.preview || '').replace(/…$/, '').trim() || 'Sin vista previa';
    const meta = `${platformLabel(post.platform)} · ${humanPostStatus(post.status_label)} · ${formatSchedule(post.scheduled_at)}`;
    const body = `<p>${esc(text)}</p><p class="vs1-review-meta">${esc(meta)}</p>`;
    const foot = `
      <button type="button" class="vs1-btn vs1-btn--ghost" id="vs1ReviewOps">Ver en Operaciones</button>
      <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ReviewPub">Ir a publicaciones</button>`;
    openReviewModal('Revisar publicación', body, foot);
    $('vs1ReviewOps').onclick = () => { closeReviewModal(); navigateTo('operations'); };
    $('vs1ReviewPub').onclick = () => { closeReviewModal(); navigateTo('publications'); };
  }

  async function approveAssistantOrder(id) {
    const res = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/assistant/orders/${encodeURIComponent(id)}/approve`, {
      method: 'POST',
      credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'No se pudo aprobar');
    toast('Publicación encolada correctamente');
  }

  async function rejectAssistantOrder(id) {
    const res = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/assistant/orders/${encodeURIComponent(id)}/reject`, {
      method: 'POST',
      credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'No se pudo rechazar');
    toast('Borrador descartado');
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

  async function tenantV1Api(path, opts = {}) {
    const res = await fetch(`/api/v1/tenants/${encodeURIComponent(TENANT_ID)}${path}`, {
      ...opts,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-Accio-Tenant': TENANT_ID,
        ...(opts.headers || {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      location.href = `/accio/login/?next=${encodeURIComponent(location.pathname)}`;
      throw new Error('Sesión expirada');
    }
    if (!res.ok) {
      const msg = data.message || data.error?.message || data.error || res.statusText;
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function priorityPill(priority) {
    const p = String(priority || 'medium').toLowerCase();
    const cls = p === 'high' ? 'is-high' : p === 'low' ? 'is-low' : 'is-medium';
    return `<span class="vs1-priority-pill ${cls}">${esc(p)}</span>`;
  }

  function renderDecisionList(el, rows, emptyText) {
    if (!el) return;
    if (!rows || !rows.length) {
      el.innerHTML = `<p class="vs1-muted">${esc(emptyText)}</p>`;
      return;
    }
    el.innerHTML = rows.join('');
  }

  async function loadDecisionConsole() {
    const oppList = $('vs1OppList');
    const recList = $('vs1RecList');
    const roadmapSummary = $('vs1RoadmapSummary');
    if (!oppList || !recList) return;

    try {
      const [oppResp, recResp] = await Promise.all([
        tenantV1Api('/opportunities?status=detected&limit=20'),
        tenantV1Api('/recommendations?status=pending_approval&limit=20'),
      ]);
      const opps = oppResp.data || [];
      const recs = recResp.data || [];

      renderDecisionList(
        oppList,
        opps.map((o) => {
          const id = esc(o.opportunity_id);
          return `<article class="vs1-decision-item" data-opp-id="${id}">
            <p class="vs1-decision-item-title">${priorityPill(o.priority)}${esc(o.title)}</p>
            <p class="vs1-decision-item-meta">${esc(o.sector || '')} · ${esc(o.product_slug || o.brand_id)} · ${esc(o.signal_type || '')}</p>
            <div class="vs1-decision-item-actions">
              <button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" data-action="promote-opp" data-id="${id}">Promover</button>
              <button type="button" class="vs1-btn vs1-btn--ghost vs1-btn--sm" data-action="dismiss-opp" data-id="${id}">Descartar</button>
            </div>
          </article>`;
        }),
        'Sin oportunidades pendientes. Usa «Detectar» para escanear señales.',
      );

      renderDecisionList(
        recList,
        recs.map((r) => {
          const id = esc(r.recommendation_id);
          return `<article class="vs1-decision-item" data-rec-id="${id}">
            <p class="vs1-decision-item-title">${priorityPill(r.priority)}${esc(r.title)}</p>
            <p class="vs1-decision-item-meta">${esc(r.brand_id)} · ${esc(r.action)} · ${esc(r.source || '')}</p>
            <div class="vs1-decision-item-actions">
              <button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" data-action="approve-rec" data-id="${id}">Aprobar</button>
              <button type="button" class="vs1-btn vs1-btn--ghost vs1-btn--sm" data-action="enrich-rec" data-id="${id}">Enriquecer IA</button>
            </div>
          </article>`;
        }),
        'Cola vacía. Promueve oportunidades o genera el roadmap del día.',
      );

      oppList.querySelectorAll('[data-action="promote-opp"]').forEach((btn) => {
        btn.onclick = async () => {
          try {
            await tenantV1Api(`/opportunities/${encodeURIComponent(btn.dataset.id)}/promote`, { method: 'POST', body: '{}' });
            toast('Oportunidad promovida a recomendación');
            await loadDecisionConsole();
          } catch (e) { toast(e.message, true); }
        };
      });
      oppList.querySelectorAll('[data-action="dismiss-opp"]').forEach((btn) => {
        btn.onclick = async () => {
          try {
            await tenantV1Api(`/opportunities/${encodeURIComponent(btn.dataset.id)}/dismiss`, { method: 'POST', body: '{}' });
            toast('Oportunidad descartada');
            await loadDecisionConsole();
          } catch (e) { toast(e.message, true); }
        };
      });
      recList.querySelectorAll('[data-action="approve-rec"]').forEach((btn) => {
        btn.onclick = async () => {
          try {
            await tenantV1Api(`/recommendations/${encodeURIComponent(btn.dataset.id)}/approve`, { method: 'POST', body: '{}' });
            toast('Recomendación aprobada');
            await loadDecisionConsole();
          } catch (e) { toast(e.message, true); }
        };
      });
      recList.querySelectorAll('[data-action="enrich-rec"]').forEach((btn) => {
        btn.onclick = async () => {
          try {
            await tenantV1Api(`/recommendations/${encodeURIComponent(btn.dataset.id)}/enrich`, {
              method: 'POST',
              body: JSON.stringify({ persist: true }),
            });
            toast('Recomendación enriquecida con IA');
            await loadDecisionConsole();
          } catch (e) { toast(e.message, true); }
        };
      });

      try {
        const roadmap = await tenantV1Api('/roadmaps/today');
        const summary = roadmap.data?.summary || {};
        if (roadmapSummary && summary.total) {
          roadmapSummary.hidden = false;
          roadmapSummary.textContent = `Roadmap hoy: ${summary.total} recomendación(es) · alta: ${summary.by_priority?.high || 0}`;
        } else if (roadmapSummary) {
          roadmapSummary.hidden = true;
        }
      } catch (_) {
        if (roadmapSummary) roadmapSummary.hidden = true;
      }
    } catch (e) {
      if (e.message !== 'Sesión expirada') {
        renderDecisionList(oppList, [], 'Motor de decisiones no disponible.');
        renderDecisionList(recList, [], e.message);
      }
    }
  }

  function bindDecisionConsoleToolbar() {
    const pipelineBtn = $('vs1PipelineRunBtn');
    const detectBtn = $('vs1OppDetectBtn');
    const promoteHighBtn = $('vs1OppPromoteHighBtn');
    const roadmapBtn = $('vs1RoadmapGenBtn');
    if (pipelineBtn) {
      pipelineBtn.onclick = async () => {
        try {
          const resp = await tenantV1Api('/opportunities/run-pipeline', {
            method: 'POST',
            body: JSON.stringify({ priority: 'high', limit: 10, enrich: true }),
          });
          const d = resp.data || {};
          const enrichNote = d.llm_skipped ? ' · IA no disponible' : (d.enrichment ? ` · ${d.enrichment.enriched_count} enriquecidas` : '');
          toast(`Pipeline: ${d.promoted_count} promovidas · roadmap listo${enrichNote}`);
          const summaryEl = $('vs1RoadmapSummary');
          if (summaryEl && d.roadmap?.summary) {
            summaryEl.hidden = false;
            summaryEl.textContent = d.roadmap.summary.headline || `Roadmap ${d.roadmap.roadmap_date}`;
          }
          await loadDecisionConsole();
        } catch (e) { toast(e.message, true); }
      };
    }
    if (detectBtn) {
      detectBtn.onclick = async () => {
        try {
          const resp = await tenantV1Api('/opportunities/detect', { method: 'POST', body: '{}' });
          toast(`Detectadas: ${resp.data.created_count} nuevas, ${resp.data.updated_count} actualizadas`);
          await loadDecisionConsole();
        } catch (e) { toast(e.message, true); }
      };
    }
    if (promoteHighBtn) {
      promoteHighBtn.onclick = async () => {
        try {
          const resp = await tenantV1Api('/opportunities/detect-and-promote', {
            method: 'POST',
            body: JSON.stringify({ priority: 'high', limit: 10 }),
          });
          toast(`Promovidas: ${resp.data.promoted_count} recomendación(es)`);
          await loadDecisionConsole();
        } catch (e) { toast(e.message, true); }
      };
    }
    if (roadmapBtn) {
      roadmapBtn.onclick = async () => {
        try {
          const resp = await tenantV1Api('/roadmaps/today/generate', { method: 'POST', body: '{}' });
          const n = resp.data?.recommendations?.length || resp.data?.summary?.total || 0;
          toast(`Roadmap del día: ${n} recomendación(es)`);
          await loadDecisionConsole();
        } catch (e) { toast(e.message, true); }
      };
    }
  }

  function renderGlobalStrategyBanner() {
    const nameEl = $('wsStrategyPlanName');
    const stateEl = $('wsStrategyPlanState');
    const topPlan = $('vs1TopbarPlanName');
    if (!nameEl || !stateEl) return;
    if (!activePlan || activePlan.estado !== 'activo') {
      nameEl.textContent = '—';
      stateEl.textContent = 'Sin plan activo';
      if (topPlan) topPlan.textContent = 'Sin plan';
      return;
    }
    const strategy = strategyLabel(activePlan.strategy_type);
    const label = strategy ? `${activePlan.nombre} — ${strategy}` : activePlan.nombre;
    nameEl.textContent = label;
    stateEl.textContent = 'Activo';
    if (topPlan) topPlan.textContent = activePlan.nombre;
  }

  function showPlanSubview(sub) {
    planSubview = sub;
    ['resumen', 'crear', 'historial'].forEach((s) => {
      const el = $('vs1PlanView' + s.charAt(0).toUpperCase() + s.slice(1));
      if (el) el.hidden = s !== sub;
    });
    document.querySelectorAll('.ws-area-nav-item[data-plan-view]').forEach((btn) => {
      btn.classList.toggle('is-active', btn.dataset.planView === sub);
    });
    if (sub === 'crear') {
      renderWizardChrome();
      renderWizardStep();
    } else if (sub === 'resumen') {
      showPlanResumen();
    } else if (sub === 'historial') {
      renderPlanHistorial();
    }
  }

  async function showPlanResumen() {
    if (!activateTarget && activePlan) activateTarget = activePlan.id;
    if (!activateTarget) {
      $('vs1ActivateCard').innerHTML = `<div class="vs1-empty-task">
        <p>Aún no tienes un plan para revisar.</p>
        <button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" id="vs1PlanEmptyCta">Crear plan</button>
      </div>`;
      const cta = $('vs1PlanEmptyCta');
      if (cta) cta.onclick = () => showPlanSubview('crear');
      return;
    }
    renderActivate();
  }

  async function renderPlanHistorial() {
    const el = $('vs1PlanHistorialList');
    if (!el) return;
    el.innerHTML = '<p class="vs1-page-sub">Cargando historial…</p>';
    try {
      const drafts = await loadDraftPlansList();
      const items = [...drafts];
      if (activePlan) items.unshift(activePlan);
      if (!items.length) {
        el.innerHTML = `<div class="vs1-empty-task"><p>No hay planes guardados todavía.</p>
          <button type="button" class="vs1-btn vs1-btn--primary vs1-btn--sm" id="vs1HistNew">Crear plan</button></div>`;
        $('vs1HistNew').onclick = () => showPlanSubview('crear');
        return;
      }
      el.innerHTML = `<ul class="vs1-draft-list">${items.map((p) => {
        const estado = p.estado === 'activo' ? 'Activo' : 'Borrador';
        const created = (p.created_at || p.updated_at || '').slice(0, 10);
        return `<li class="vs1-draft-item"><div class="vs1-draft-row">
          <div><span class="vs1-pending-tag">${esc(estado)}</span>
          <p class="vs1-draft-name">${esc(p.nombre)}</p>
          <p class="vs1-draft-sub">${created ? `Actualizado ${created}` : ''}</p></div>
          <button type="button" class="vs1-btn vs1-btn--secondary vs1-btn--sm" data-hist-plan="${esc(p.id)}">Ver</button>
        </div></li>`;
      }).join('')}</ul>`;
      el.querySelectorAll('[data-hist-plan]').forEach((btn) => {
        btn.onclick = () => goActivate(btn.getAttribute('data-hist-plan'));
      });
    } catch (e) {
      el.innerHTML = `<p class="vs1-page-sub">${esc(e.message)}</p>`;
    }
  }

  function navigateTo(area, opts = {}) {
    const { planView, opsTab, skipLoad } = opts;
    currentArea = area;

    Object.entries(AREA_VIEWS).forEach(([key, id]) => {
      const el = $(id);
      if (el) el.hidden = key !== area;
    });

    document.querySelectorAll('.vs1-nav-item[data-nav]').forEach((btn) => {
      btn.classList.toggle('is-active', btn.dataset.nav === area);
    });

    if (area === 'plan') {
      const sub = planView || (activePlan ? 'resumen' : 'crear');
      showPlanSubview(sub);
    }

    if (EMBED_FRAMES[area]) {
      loadEmbedFrame(area, opsTab);
    }

    if (skipLoad) return;

    if (area === 'workspace') loadWorkspace();
    else if (area === 'context') loadContext();
    else if (area === 'proposals') loadProposalCachedOrGenerate();
  }

  function greeting() {
    const h = new Date().getHours();
    const sal = h < 12 ? 'Buenos días' : h < 19 ? 'Buenas tardes' : 'Buenas noches';
    $('vs1Greeting').textContent = `${sal}, ${USER_NAME.split(' ')[0] || USER_NAME}`;
    $('vs1Avatar').textContent = (USER_NAME[0] || 'A').toUpperCase();
  }

  function renderPlanBanner() {
    const slot = $('vs1PlanBannerSlot');
    renderGlobalStrategyBanner();
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
    slot.innerHTML = '';
    $('vs1DayStatus').textContent = `Tu prioridad hoy: avanzar «${activePlan.nombre}».`;
  }

  function goWizard() {
    wizardStep = 0;
    navigateTo('plan', { planView: 'crear', skipLoad: true });
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

  function strategyLabel(strategyId) {
    const row = STRATEGIES.find((s) => s.id === strategyId);
    return row ? row.name : 'Sin definir';
  }

  function formatPlanPeriod(plan) {
    const p = plan.periodo || {};
    const ini = String(p.inicio || plan.periodo_inicio || '').slice(0, 10);
    const fin = String(p.fin || plan.periodo_fin || '').slice(0, 10);
    const fmt = (d) => {
      if (!d) return '—';
      const dt = new Date(d + 'T12:00:00');
      if (Number.isNaN(dt.getTime())) return d;
      return dt.toLocaleDateString('es-PA', { day: 'numeric', month: 'short', year: 'numeric' });
    };
    if (!ini && !fin) return '—';
    return `${fmt(ini)} – ${fmt(fin)}`;
  }

  function formatAudience(plan) {
    const pub = plan.publico_objetivo;
    if (Array.isArray(pub)) return pub.filter(Boolean).join(' · ') || '—';
    return pub || '—';
  }

  function formatCriteria(plan) {
    const c = plan.success_criteria;
    if (Array.isArray(c) && c.length) return c.join(' · ');
    return '—';
  }

  function planSummaryFactsHtml(plan) {
    return `<dl class="vs1-activate-facts">
      <div><dt>Tu objetivo</dt><dd>${esc(plan.objetivo_general || '—')}</dd></div>
      <div><dt>Tu enfoque</dt><dd>${esc(strategyLabel(plan.strategy_type))}</dd></div>
      <div><dt>Tu audiencia</dt><dd>${esc(formatAudience(plan))}</dd></div>
      <div><dt>Tu meta</dt><dd>${esc(plan.north_star_metric || '—')}</dd></div>
      <div><dt>Periodo</dt><dd>${esc(formatPlanPeriod(plan))}</dd></div>
      ${formatCriteria(plan) !== '—' ? `<div><dt>Hitos de progreso</dt><dd>${esc(formatCriteria(plan))}</dd></div>` : ''}
    </dl>`;
  }

  function bindActivateCancel() {
    const cancel = () => navigateTo('workspace');
    $('vs1ActCancel').onclick = cancel;
  }

  function goActivate(planId) {
    activateTarget = planId;
    navigateTo('plan', { planView: 'resumen', skipLoad: true });
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
        navigateTo('workspace');
        return;
      }
    }

    const isActiveView = plan.estado === 'activo';
    let otherActive = null;
    if (!isActiveView) {
      if (activePlan && activePlan.id !== plan.id && activePlan.estado === 'activo') {
        otherActive = activePlan;
      } else {
        try {
          const r = await v1Api('/marketing-plans/active');
          if (r.data && r.data.id !== plan.id) otherActive = r.data;
        } catch (_) { /* ignore */ }
      }
    }

    const summaryCard = `<div class="vs1-card vs1-activate-summary">
      <h3 class="vs1-activate-plan-name">${esc(plan.nombre)}</h3>
      ${planSummaryFactsHtml(plan)}
    </div>`;

    if (isActiveView) {
      $('vs1ActivateCard').innerHTML = `
        <div class="vs1-activate-intro">
          <p class="vs1-page-label">Tu plan en curso</p>
          <h2 class="vs1-activate-q">¿Qué estás trabajando ahora?</h2>
          <p class="vs1-page-sub">Este plan guía tus recomendaciones y el trabajo pendiente en Inicio.</p>
        </div>
        ${summaryCard}
        <div class="vs1-activate-footer" id="vs1ActFooter">
          <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActCancel">Volver al inicio</button>
          <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ActStrategic">Ver opciones estratégicas</button>
        </div>`;
      bindActivateCancel();
      $('vs1ActStrategic').onclick = () => navigateTo('proposals');
      return;
    }

    const conflictCard = otherActive ? `
      <div class="vs1-card vs1-activate-choice">
        <p class="vs1-label-upper">Tu plan actual</p>
        <h3 class="vs1-activate-subq">¿Qué hacemos con «${esc(otherActive.nombre)}»?</h3>
        <p>Ese plan sigue en curso. Elige si lo pausas o lo das por terminado antes de continuar con el nuevo.</p>
      </div>` : '';

    $('vs1ActivateCard').innerHTML = `
      <div class="vs1-activate-intro">
        <p class="vs1-page-label">Confirmar plan</p>
        <h2 class="vs1-activate-q">¿Quieres poner en marcha este plan?</h2>
        <p class="vs1-page-sub">Revisa el resumen. Al confirmar, será tu referencia para las próximas recomendaciones.</p>
      </div>
      ${summaryCard}
      <div class="vs1-card" style="margin-bottom:var(--space-lg);padding:var(--space-xl)">
        <p class="vs1-label-upper">Qué pasará</p>
        <ul class="vs1-activate-effects">
          <li><i class="ti ti-check" aria-hidden="true"></i><span>Tus siguientes recomendaciones se basarán en este plan.</span></li>
          <li><i class="ti ti-check" aria-hidden="true"></i><span>Las publicaciones sugeridas apuntarán a tu meta.</span></li>
          <li><i class="ti ti-check" aria-hidden="true"></i><span>Puedes cambiar de plan cuando lo necesites.</span></li>
        </ul>
      </div>
      ${conflictCard}
      <div class="vs1-activate-footer" id="vs1ActFooter"></div>`;

    bindActivateCancel();

    if (otherActive) {
      $('vs1ActFooter').innerHTML = `
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActCancel">Cancelar</button>
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActPause">Pausar el anterior y continuar</button>
        <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ActFinalize">Terminar el anterior y continuar</button>`;
      bindActivateCancel();
      $('vs1ActPause').onclick = () => doActivate(plan.id, 'pause_previous');
      $('vs1ActFinalize').onclick = () => doActivate(plan.id, 'finalize_previous');
    } else {
      $('vs1ActFooter').innerHTML = `
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1ActCancel">Cancelar</button>
        <button type="button" class="vs1-btn vs1-btn--primary" id="vs1ActGo">Poner en marcha</button>`;
      bindActivateCancel();
      $('vs1ActGo').onclick = () => doActivate(plan.id, null);
    }
  }

  async function doActivate(planId, resolution) {
    try {
      const body = resolution ? { resolution } : {};
      const resp = await v1Api('/marketing-plans/' + encodeURIComponent(planId) + '/activate', { method: 'POST', body: JSON.stringify(body) });
      activePlan = resp.data;
      contextData = null;
      toast('Plan en marcha');
      navigateTo('workspace');
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

  function navigateToSourceFix(sourceId) {
    if (sourceId === 'plan') {
      navigateTo('plan', { planView: activePlan ? 'resumen' : 'crear' });
      return;
    }
    navigateTo('config', { opsTab: 'conocimiento' });
  }

  function sourceFixUrl(sourceId) {
    return '#';
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
        btn.onclick = () => navigateToSourceFix(btn.dataset.source);
      });

      const incomplete = rows.find((r) => r.status === 'incomplete');
      const nextBanner = $('vs1ContextNextBanner');
      const nextCta = $('vs1ContextNextCta');
      if (incomplete) {
        nextBanner.hidden = false;
        $('vs1ContextNextText').textContent = `Completa «${incomplete.name}» para que las propuestas reflejen mejor tu negocio.`;
        nextCta.textContent = `Ir a ${incomplete.name}`;
        nextCta.onclick = () => navigateToSourceFix(incomplete.id);
      } else {
        nextBanner.hidden = true;
      }
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function loadProposalCachedOrGenerate() {
    if (!activePlan) {
      try {
        const r = await v1Api('/marketing-plans/active');
        activePlan = r.data;
      } catch (_) { /* ignore */ }
    }
    if (!activePlan) {
      toast('Activa un plan antes de ver propuestas', true);
      navigateTo('workspace');
      return;
    }
    if (proposalData && renderProposalUI()) return;
    await loadProposal();
  }

  function channelHintHuman(hint) {
    const h = String(hint || '').toLowerCase();
    if (h.includes('linkedin')) return 'LinkedIn';
    if (h.includes('facebook') || h.includes('meta') || h.includes('instagram')) return 'Redes sociales';
    if (h.includes('email') || h.includes('correo')) return 'Email';
    if (h.includes('web') || h.includes('landing') || h.includes('sitio')) return 'Web';
    return hint || 'Varios canales';
  }

  function priorityHuman(p) {
    const map = { alta: 'Prioridad alta', media: 'Prioridad media', baja: 'Prioridad baja' };
    return map[String(p || '').toLowerCase()] || 'Prioridad media';
  }

  function proposalOptionCard(row, index) {
    const rec = index === 0;
    return `<article class="vs1-option-card${rec ? ' is-recommended' : ''}">
      <div class="vs1-option-head">
        <span class="vs1-option-num">${index + 1}</span>
        <h3>${esc(row.title)}</h3>
        ${rec ? '<span class="vs1-badge vs1-badge--rec">Para empezar</span>' : ''}
      </div>
      <p class="vs1-option-meta">${esc(channelHintHuman(row.channel_hint))} · ${esc(priorityHuman(row.priority))}</p>
      <p class="vs1-option-body">${esc(row.summary || '')}</p>
      <div class="vs1-option-actions">
        <button type="button" class="vs1-btn vs1-btn--${rec ? 'primary' : 'secondary'} vs1-btn--sm" data-choose-proposal="${index}">Elegir esta opción</button>
      </div>
    </article>`;
  }

  async function chooseProposalOption(index) {
    const all = (proposalData && proposalData.proposals) || [];
    const row = all[index];
    if (!row) return;
    clearStoredProposals();
    toast(`Opción elegida: ${row.title}`);
    navigateTo('workspace');
    await loadWorkspace();
  }

  function bindProposalActions() {
    document.querySelectorAll('[data-choose-proposal]').forEach((btn) => {
      btn.onclick = () => chooseProposalOption(Number(btn.getAttribute('data-choose-proposal')));
    });
    const regen = $('vs1PropRegen');
    if (regen) regen.onclick = () => loadProposal();
    const back = $('vs1PropBack');
    if (back) back.onclick = () => navigateTo('workspace');
    const backTop = $('vs1BackFromProposal');
    if (backTop) backTop.onclick = () => navigateTo('workspace');
  }

  function renderProposalUI() {
    const all = proposalData.proposals || [];
    if (!all.length) return false;

    const intro = proposalData.executive_summary || '';
    const ideas = (all[0].actions || []).filter(Boolean);

    $('vs1ProposalMain').innerHTML = `
      <div class="vs1-proposal-intro">
        <p class="vs1-page-label">Opciones para tu plan</p>
        <h1 class="vs1-proposal-q">¿Cuál movimiento quieres explorar primero?</h1>
        <p class="vs1-page-sub">Tres caminos concretos basados en tu plan y lo que sabemos de tu negocio.</p>
      </div>
      ${intro ? `<div class="vs1-card vs1-proposal-summary"><p class="vs1-label-upper">En pocas palabras</p><p>${esc(intro)}</p></div>` : ''}
      ${ideas.length ? `<div class="vs1-card vs1-proposal-ideas"><p class="vs1-label-upper">Qué podrías hacer</p><ul class="vs1-opp-list">${ideas.map((a) => `<li><i class="ti ti-check" aria-hidden="true"></i><span>${esc(a)}</span></li>`).join('')}</ul></div>` : ''}
      <div class="vs1-proposal-options" aria-label="Opciones estratégicas">
        ${all.map((row, i) => proposalOptionCard(row, i)).join('')}
      </div>
      <div class="vs1-proposal-footer">
        <button type="button" class="vs1-btn vs1-btn--ghost" id="vs1PropBack">Volver al inicio</button>
        <button type="button" class="vs1-btn vs1-btn--secondary" id="vs1PropRegen">Ver otras opciones</button>
      </div>`;
    bindProposalActions();
    return true;
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
      navigateTo('workspace');
      return;
    }
    $('vs1ProposalMain').innerHTML = '<p class="vs1-page-sub">Preparando opciones para ti…</p>';
    try {
      if (!contextData) await loadContext();
      const resp = await v1Api('/planner/proposals', { method: 'POST', body: '{}' });
      storeProposalsPending(resp.data);
      if (!renderProposalUI()) throw new Error('Sin propuestas');
    } catch (e) {
      toast(e.message, true);
    }
  }

  function initLogoLinks() {
    const home = `/accio/plan/${encodeURIComponent(TENANT_ID)}/`;
    document.querySelectorAll('.vs1-logo').forEach((a) => { a.href = home; });
  }

  function initNav() {
    document.querySelectorAll('.vs1-nav-item[data-nav]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const nav = btn.dataset.nav;
        if (nav === 'plan') {
          navigateTo('plan', { planView: activePlan ? 'resumen' : 'crear' });
        } else {
          navigateTo(nav);
        }
      });
    });
    document.querySelectorAll('.ws-area-nav-item[data-plan-view]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const sub = btn.dataset.planView;
        if (sub === 'crear') goWizard();
        else showPlanSubview(sub);
      });
    });
  }

  async function initAppSelect() {
    const sel = $('vs1AppSelect');
    if (!sel) return;
    try {
      const r = await fetch(`/accio/${encodeURIComponent(TENANT_ID)}/apps`, { credentials: 'include' });
      const data = await r.json().catch(() => ({}));
      const apps = data.ok ? (data.apps || []) : [];
      if (!apps.length) {
        sel.innerHTML = `<option value="${esc(APP_ID)}">${esc(APP_ID)}</option>`;
        sel.disabled = true;
        return;
      }
      sel.innerHTML = apps.map((a) =>
        `<option value="${esc(a.app_id)}"${a.app_id === APP_ID ? ' selected' : ''}>${esc(a.name || a.app_id)}</option>`
      ).join('');
      sel.onchange = () => {
        localStorage.setItem(`accio_app_${TENANT_ID}`, sel.value);
        location.reload();
      };
    } catch (_) {
      sel.innerHTML = `<option>${esc(APP_ID)}</option>`;
    }
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
    const genBtn = $('vs1GenProposalBtn');
    if (genBtn) genBtn.onclick = () => { navigateTo('proposals'); loadProposal(); };
  }

  async function bootstrap() {
    initBranding();
    initLogoLinks();
    initTenantSelect();
    await initAppSelect();
    initNav();
    initWizardNav();
    initTopActions();
    bindDecisionConsoleToolbar();
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && $('vs1ReviewModal') && !$('vs1ReviewModal').hidden) closeReviewModal();
    });
    navigateTo('workspace');
    await loadWorkspace();
    const hash = location.hash.replace('#', '');
    if (hash === 'crear') goWizard();
    if (hash === 'contexto') navigateTo('context');
    if (hash === 'propuestas') navigateTo('proposals');
  }

  bootstrap();
  window.__vs1GoActivate = goActivate;
})();
