# Marketing OS — Framework de desarrollo

**Estado:** Regla oficial post–Product Vision v2.2  
**North star:** [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md)  
**Dominio:** [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md)

---

## Cambio de forma de trabajar

**Ya no se pide:** «Haz un módulo.»

**Siempre se pide:** responder las **cinco preguntas** antes de diseñar o codificar.

Si cada desarrollo las responde, EM+Acción crece ordenado y coherente con la visión.

---

## Las cinco preguntas (obligatorias)

| # | Pregunta | Qué valida |
|---|----------|------------|
| 1 | **¿A qué pilar pertenece?** | Visión v2.2 (Company Brain, Corporate Memory, … ROI Engine) |
| 2 | **¿Qué entidad del dominio afecta?** | [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) |
| 3 | **¿Qué evento genera?** | [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) |
| 4 | **¿Qué registra en Corporate Memory?** | Trazabilidad y aprendizaje acumulativo |
| 5 | **¿Cómo ayuda a vender más?** | Misión del producto |

Si **alguna** no tiene respuesta clara → **detener** y alinear con producto antes de implementar.

---

## Plantilla para tickets / PRs

```markdown
## Marketing OS — checklist

- [ ] **Pilar:** …
- [ ] **Entidad(es):** …
- [ ] **Evento(s):** …
- [ ] **Corporate Memory:** qué se registra y con qué `entity_refs`
- [ ] **Vender más:** …

## Fase del ciclo
Observar · Analizar · Planificar · Crear · Ejecutar · Medir · Aprender

## ¿Es otra pantalla suelta?
Sí / No — si sí, justificar
```

---

## Relación con otras reglas

| Marco | Preguntas |
|-------|-----------|
| **Visión §11** (6 preguntas dev) | Pilar, ciclo, conocimiento, reutilización, decisiones, ¿Marketing OS? |
| **Este framework** (5 preguntas) | Pilar, entidad, evento, memoria, ventas |
| **Sprint 1** | Prohibido feature sin entidad de dominio |

Las cinco preguntas son el **filtro operativo diario**. Las seis de la visión son el **filtro estratégico**. Usar ambas.

---

## Ejemplos

### ❌ Mal encuadrado

> «Integrar OpenAI en el chat.»

| Pregunta | Respuesta |
|----------|-----------|
| Pilar | ¿? |
| Entidad | Ninguna |
| Evento | Ninguno |
| Corporate Memory | Nada |
| Vender más | No claro |

### ✅ Bien encuadrado

> «Registrar `PublicationPublished` cuando LinkedIn confirma post ID.»

| Pregunta | Respuesta |
|----------|-----------|
| Pilar | 9 Automation Engine |
| Entidad | Publication, Campaign |
| Evento | `PublicationPublished` |
| Corporate Memory | actor, post_id, métricas iniciales |
| Vender más | Trazabilidad de contenido → medir → optimizar campañas |

---

## Regla final

> **El dominio gobierna el producto; el código implementa el dominio.**

No construir por intuición. Construir por pilar, entidad, evento, memoria y ventas.

---

## Referencias

- [MARKETING_OS_SPRINT1_DOMAIN_MODEL.md](MARKETING_OS_SPRINT1_DOMAIN_MODEL.md)
- [ROADMAP.md](ROADMAP.md)
- [MARKETING_OS_GLOSSARY.md](MARKETING_OS_GLOSSARY.md)
