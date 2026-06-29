# MARKETING_OS_CONSTITUTION.md

## Constitución del Marketing Operating System

**Versión:** 1.0  
**Estado:** ✅ **v1.0 aprobada** — reglas inmutables  

## Jerarquía documental (orden obligatorio)

```
1. Constitución          →  reglas inmutables          →  este documento
2. Product Vision        →  qué es el producto         →  EMACCION_PRODUCT_VISION_v2.2.md
3. Domain Model          →  qué objetos existen        →  MARKETING_OS_DOMAIN_MODEL.md
4. Arquitectura          →  cómo se implementa         →  (post Domain Model v1.0)
5. Roadmap               →  orden de construcción      →  ROADMAP.md
6. Código                →  implementación
```

**Después de esta Constitución:** no más documentos conceptuales. No redefinir el producto. Cada sprint produce **entregables concretos y verificables**.

---

# Preámbulo

EM+Acción no es un conjunto de funcionalidades.

EM+Acción es un **sistema operativo** especializado en ayudar a las empresas a **vender más**.

Toda decisión de arquitectura, desarrollo, inteligencia artificial, automatización o experiencia de usuario deberá respetar esta Constitución.

**Ningún módulo está por encima de estos principios.**

---

# Principio 1 — La misión

Toda funcionalidad deberá responder una única pregunta:

**¿Cómo ayuda esto a vender más?**

Si no existe una respuesta clara, probablemente no pertenece al núcleo del Marketing OS.

---

# Principio 2 — El conocimiento es el activo principal

El verdadero valor del producto no es la IA.

Es el **conocimiento acumulado de la empresa**.

Por lo tanto:

- Nunca se **perderá** conocimiento.
- Nunca se **duplicará** conocimiento.
- Nunca se **ignorará** conocimiento existente.

---

# Principio 3 — Buscar antes de crear

Antes de generar cualquier contenido el sistema deberá consultar:

```
Company Brain
      ↓
Corporate Memory
      ↓
Product Knowledge Base
      ↓
Brand Center
      ↓
Asset Manager
```

Solo si no existe información suficiente podrá recurrir a la IA.

---

# Principio 4 — La IA nunca decide sola

La IA genera. Sugiere. Resume. Explica.

Pero quien **toma decisiones** es el **Marketing Brain**.

---

# Principio 5 — Todo debe aprender

Cada acción genera aprendizaje.

Toda campaña. Todo flyer. Todo correo. Toda publicación. Todo comentario. Toda conversión. Todo rechazo.

**Todo deberá enriquecer Corporate Memory.**

---

# Principio 6 — Todo debe ser observable

Todo objeto del sistema debe poder observarse.

Producto · Cliente · Lead · Campaña · Flyer · Correo · Workflow · Activo · Automatización.

**Todo entra al ciclo.**

---

# Principio 7 — Todo tiene un responsable

Ninguna recomendación puede quedar sin propietario.

Toda recomendación debe indicar: **Responsable · Prioridad · Impacto esperado · Estado · Fecha**.

---

# Principio 8 — La automatización es el objetivo

Si una tarea puede automatizarse de forma segura, deberá automatizarse.

La intervención humana será para: **Aprobar · Corregir · Supervisar · Decidir**.

---

# Principio 9 — Multiempresa por diseño

Nada se desarrollará pensando únicamente en EasyTech.

Todo deberá soportar: **Tenant · Empresas · Marcas · Productos · Usuarios · Permisos · Configuración independiente**.

---

# Principio 10 — Configuración antes que código

Siempre que sea posible: **configurar, no programar**.

El comportamiento deberá definirse mediante **reglas**, no mediante cambios de código.

---

# Principio 11 — Reutilización

Toda funcionalidad deberá poder reutilizarse.

No construir desarrollos exclusivos para un cliente.

Si una necesidad es específica, implementarla mediante **configuración, extensiones o módulos opcionales**.

---

# Principio 12 — La memoria nunca se borra

Corporate Memory representa la experiencia de la empresa.

**No debe eliminarse. Solo archivarse.**

---

# Principio 13 — El Roadmap es dinámico

El Roadmap no es una lista manual.

Es el **resultado del ciclo**:

```
Observar → Analizar → Planificar → Crear → Ejecutar → Medir → Aprender
```

Cada día el sistema debe **reconstruir automáticamente** el Roadmap.

---

# Principio 14 — La IA es reemplazable

El Marketing OS **nunca dependerá de un proveedor**.

La IA es un **componente**. No el producto.

---

# Principio 15 — La experiencia del usuario

El usuario nunca debería preguntarse: **¿Qué hago ahora?**

El sistema debe **responder automáticamente**.

---

# Principio 16 — El conocimiento pertenece a la empresa

No pertenece al modelo de IA. No pertenece al proveedor. No pertenece al desarrollador.

**Pertenece al cliente.**

Debe poder **exportarse, respaldarse y migrarse**.

---

# Principio 17 — Medir antes de opinar

Toda recomendación deberá sustentarse en **datos**, no en intuición.

---

# Principio 18 — ROI primero

El éxito de una campaña se mide por **resultados**.

No por cantidad de publicaciones, seguidores o contenido.

La pregunta final siempre será: **¿Qué produjo ventas?**

---

# Principio 19 — Desarrollo responsable

Antes de escribir una línea de código, responder:

1. ¿**Ayuda a vender más**?
2. ¿A qué **pilar** pertenece?
3. ¿Qué **entidad del dominio** afecta?
4. ¿Qué **evento** genera?
5. ¿Qué registra en **Corporate Memory**?
6. ¿Qué **KPI** mejora?
7. ¿Qué **automatización** habilita?
8. ¿Puede **reutilizarse**?
9. ¿Es **configurable**?
10. ¿**Respeta esta Constitución**?

Si alguna respuesta es negativa, el desarrollo deberá **reevaluarse**.

### Plantilla ticket / PR

```markdown
## Constitución — Principio 19

1. Vender más: …
2. Pilar: …
3. Entidad: …
4. Evento: …
5. Corporate Memory: …
6. KPI: …
7. Automatización: …
8. Reutilizable: …
9. Configurable: …
10. Respeta Constitución: Sí / No
```

---

# Principio 20 — La evolución nunca termina

El Marketing OS no es un proyecto. Es un **sistema vivo**.

Cada versión debe: observar mejor · recordar más · analizar mejor · recomendar mejor · automatizar más · aprender continuamente.

Solo así cumplirá su propósito de convertirse en el **Director de Marketing Digital** de las empresas.

---

# Cierre de fase conceptual

Con la Constitución v1.0 aprobada y commiteada:

| Acción | Estado |
|--------|--------|
| Nuevos documentos de visión / redefinición de producto | ❌ **Prohibido** |
| Documentos conceptuales adicionales | ❌ **Prohibido** |
| Sprint técnico: Domain Model v1.0 + BD conceptual | ✅ **Siguiente** |
| Arquitectura de implementación | Después de Domain Model v1.0 |
| Código de features | Después de Arquitectura |

> La visión se convierte en plataforma cuando el **Domain Model** y la **persistencia conceptual** estén cerrados y verificables.

---

## Referencias

| Documento | Capa |
|-----------|------|
| [EMACCION_PRODUCT_VISION_v2.2.md](EMACCION_PRODUCT_VISION_v2.2.md) | POR QUÉ |
| [MARKETING_OS_DOMAIN_MODEL.md](MARKETING_OS_DOMAIN_MODEL.md) | QUÉ ES |
| [MARKETING_OS_DOMAIN_EVENTS.md](MARKETING_OS_DOMAIN_EVENTS.md) | Eventos |
| [MARKETING_OS_SPRINT1_DOMAIN_MODEL.md](MARKETING_OS_SPRINT1_DOMAIN_MODEL.md) | Sprint activo |
| [ROADMAP.md](ROADMAP.md) | CUÁNDO |
