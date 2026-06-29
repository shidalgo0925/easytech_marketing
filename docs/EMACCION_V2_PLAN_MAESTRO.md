# EM+Acción V2 — Plan Maestro de Desarrollo

**Producto:** EM+Acción (EasyMarketingOne)  
**Visión:** Marketing OS — [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) **(CONGELADO)**  
**Visión técnica (legacy):** Motor Comercial IA Multi-Tenant del Ecosistema EasyTech  
**Versión:** 2.0  
**Estado:** Plan Maestro — fuente de verdad estratégica  
**Regla principal:** **No implementar una fase hasta cerrar completamente la anterior.**

**Repo:** `github.com/shidalgo0925/easytech_marketing` · **VPS:** `/opt/easytech_marketing`  
**Dashboard:** https://emaccion.etsrv.site/accio/dashboard/

> Documento operativo de seguimiento: [ROADMAP.md](ROADMAP.md)  
> Estado vs código actual: [EMACCION_V2_ESTADO.md](EMACCION_V2_ESTADO.md)

---

## 1. Objetivo

EM+Acción será el producto encargado de **generar demanda** para todo el ecosistema EasyTech.

No será un simple publicador de contenido. Será un **Agente Comercial Inteligente** capaz de:

- Detectar oportunidades
- Entender el contexto
- Seleccionar el producto correcto
- Crear campañas
- Publicarlas
- Capturar prospectos
- Enviarlos al CRM
- Medir resultados
- Aprender continuamente

---

## 2. Arquitectura general

```
Internet
      │
      ▼
Opportunity Engine
      │
      ▼
Knowledge Engine
      │
      ▼
Campaign Engine
      │
      ▼
Image / Copy Generator
      │
      ▼
Publisher
      │
      ▼
Landing
      │
      ▼
EN1 CRM
      │
      ▼
Automation
      │
      ▼
Analytics
      │
      ▼
Learning Engine
```

---

## 3. Fases V2 (orden obligatorio)

| Fase | Nombre | Objetivo resumido |
|------|--------|-------------------|
| **A** | Base técnica | DEV / TEST / PROD independientes, estable |
| **B** | Multi-Tenant Core | Un motor, muchos clientes, datos aislados |
| **C** | Configuration Center | Toda config desde UI, sin JSON manual |
| **D** | Knowledge Engine | Conoce portafolio, sectores, objeciones, CTAs |
| **E** | Opportunity Engine | Detecta y clasifica oportunidades |
| **F** | Campaign Engine | Oportunidad → campaña completa |
| **G** | Image Engine | Flyers, carruseles, stories, ads |
| **H** | Publisher | LI + FB + IG → multicanal |
| **I** | Landing Manager | Landings por producto + UTM |
| **J** | CRM Integration | EN1, Odoo, HubSpot, Zoho, API |
| **K** | Analytics | Conversión, ROI, rendimiento por canal |
| **L** | Learning Engine | Reutilizar lo que funciona, descartar lo que falla |
| **M** | Community Manager IA | Comentarios, DMs, FAQ, escalado humano |
| **N** | Scheduler | Mejor hora/día/frecuencia por red |
| **O** | Automation Engine | Email, WhatsApp, nurturing |
| **P** | API Marketplace | API pública para campañas, métricas, leads |

---

## 4. FASE A — Base técnica

**Objetivo:** Motor completamente estable.

**Pendientes:**

- Estructura limpia
- Git limpio
- Documentación
- Backup `.env`
- Separar **DEV · TEST · PROD** (independientes, sin mezclar configuraciones)
- systemd
- nginx
- SSL
- logs

**Criterio de cierre:** Tres entornos desplegables y documentados; PROD estable.

---

## 5. FASE B — Multi-Tenant Core

**Objetivo:** Un solo EMAcción, muchos clientes.

**Ejemplo de tenants:** EasyTech · Relatic · Cliente A · B · C

**Cada tenant tiene (aislado):** branding · usuarios · productos · campañas · CRM · conocimiento · métricas · conectores · OAuth · API keys · landings

**Regla:** Nunca compartir datos entre tenants.

**Modelo tenant:**

```
id, nombre, dominio, logo, color, timezone, estado, created_at
```

**Regla de datos:** Todas las tablas/colecciones incluyen `tenant_id`.

---

## 6. FASE C — Configuration Center

**Objetivo:** Consola de configuración completa desde UI.

**Menú:**

```
Empresa · Tenant · Usuarios · Roles · Productos · Conectores · CRM
Landing · IA · Publicación · Variables · Logs · Backups · Seguridad
```

**Regla:** Nunca editar JSON manualmente en operación normal.

---

## 7. FASE D — Knowledge Engine

**Corazón del sistema.** Debe conocer: EasyTech, EN1, EPOSOne, EPayRoll, EClassOne, Odoo, Converso.

También: sectores · problemas · objeciones · CTA · FAQ · argumentos · competencia · casos de éxito.

Debe responder preguntas automáticamente (por tenant).

---

## 8. FASE E — Opportunity Engine

**Detecta señales en:** Facebook · Instagram · LinkedIn · noticias · blogs · RSS · Google · web.

**Busca:** congresos · cursos · eventos · ERP · POS · planilla · facturación · restaurantes · retail · educación · hospitales.

**Clasifica:** sector · necesidad · producto · prioridad.

---

## 9. FASE F — Campaign Engine

Recibe oportunidad aprobada. Genera: título · copy · hashtags · CTA · landing · prompt imagen · prompt video · calendario · canal.

---

## 10. FASE G — Image Engine

Genera: flyers · carruseles · stories · posts · banners · miniaturas.

Compatible: Instagram · Facebook · LinkedIn · blog · ads.

---

## 11. FASE H — Publisher

Publicación automática.

**Inicial:** LinkedIn · Facebook · Instagram  
**Luego:** blog · email · Google Business · TikTok · YouTube · X

Registrar: post ID · fecha · estado · errores (por tenant).

---

## 12. FASE I — Landing Manager

Landings por producto, ej.:

```
easytech.services/en1
easytech.services/eposone
easytech.services/epayroll
easytech.services/eclassone
easytech.services/odoo
```

Cada landing: formulario · CTA · UTM · analytics.

---

## 13. FASE J — CRM Integration

CRM configurable: **EN1 · Odoo · HubSpot · Zoho · API** — no depender de uno solo.

---

## 14. FASE K — Analytics

Responder: qué campaña vendió más · qué producto convierte · qué red genera clientes · qué CTA funciona · qué landing convierte.

Registrar: clics · CTR · leads · ventas · ROI · costo por lead.

---

## 15. FASE L — Learning Engine

Si una campaña funciona → reutilizar estrategia. Si falla → descartarla.

---

## 16. FASE M — Community Manager IA

Responder en Facebook · Instagram · LinkedIn — comentarios · mensajes · FAQ · escalar a humano.

---

## 17. FASE N — Scheduler

Calendario inteligente: mejor hora · mejor día · frecuencia por red social.

---

## 18. FASE O — Automation Engine

Correo · WhatsApp · seguimiento · recordatorios · reactivación · nurturing.

---

## 19. FASE P — API Marketplace

API pública, ej.:

```
POST campañas · GET métricas · GET leads · GET publicaciones
POST oportunidades · POST imágenes · POST campañas IA
```

---

## 20. Dashboard definitivo (objetivo UI)

```
Dashboard · Oportunidades · Campañas · Publicaciones · Leads · CRM
Productos · Knowledge · Conectores · Automatizaciones · Métricas · Configuración
```

---

## 21. Configuración (alcance completo)

Administrar: empresa · tenant · logo · colores · usuarios · roles · OAuth · API keys · CRM · landing · IA · conectores · productos · variables · backups · logs.

---

## 22. Productos (catálogo por tenant)

EN1 · EPOSOne · EPayRoll · EClassOne · Odoo · Converso · nuevos productos.

Cada uno: landing · CTA · conocimiento · hashtags · imágenes · embudos.

---

## 23. Agentes IA (futuro)

Trend Hunter · Opportunity Analyzer · Knowledge Agent · Campaign Planner · Copy Writer · Image Creator · Publisher · Community Manager · Lead Analyzer · Sales Assistant · Analytics Agent · Learning Agent.

---

## 24. Seguridad

RBAC · auditoría · historial · logs · 2FA (futuro) · rotación de tokens · secret manager.

---

## 25. Escalabilidad (preparación)

Docker (opcional) · Redis · Celery · RabbitMQ (si aplica) · workers · queue · scheduler · horizontal scaling.

---

## 26. Regla arquitectónica

EM+Acción es el **único motor comercial** del ecosistema.

EN1 · EPOSOne · EPayRoll · EClassOne · Odoo · Converso **no implementan motores de marketing propios**.

---

## 27. Criterio de finalización V2

EM+Acción estará terminado cuando pueda:

1. Detectar una oportunidad en Internet
2. Clasificarla automáticamente
3. Seleccionar el producto correcto
4. Generar una campaña completa
5. Crear imágenes y contenido
6. Publicar en varios canales
7. Enviar tráfico a una landing específica
8. Capturar el lead
9. Crear el lead en EN1 CRM
10. Dar seguimiento automático
11. Medir resultados
12. Aprender y optimizar futuras campañas

---

## 28. Reglas para el desarrollo

- No comenzar una fase sin cerrar la anterior
- Cada fase: documentación técnica + funcional
- Cada fase: pruebas unitarias e integración
- No mezclar configuración entre tenants
- No almacenar secretos en código fuente
- Toda funcionalidad multi-tenant desde el diseño
- EasyTech = tenant principal; Relatic y nuevos clientes sin cambios de código
- Cada fase cierra con: documentación · checklist · roadmap actualizado · evidencia de pruebas

---

## 29. Mapeo documentos históricos → V2

| Doc anterior | Equivalente V2 |
|--------------|----------------|
| `EMACCION_PHASE_M_MULTI_TENANT.md` | Fase **B** |
| `EMACCION_PHASE_N_TENANT_SETTINGS.md` | Fase **C** (parcial) |
| `EMACCION_PHASE_E_KNOWLEDGE_ENGINE.md` | Fase **D** |
| Roadmap fases F–K (v1) | Fases E–L (v2) |

**Actualizado:** 2026-06-26
