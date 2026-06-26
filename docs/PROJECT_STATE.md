# ARROZCONPOLLO — PROJECT_STATE.md

Servidor: ARROZCONPOLLO  
IP pública: 95.111.244.137  
Proveedor: Hetzner  
Uso principal: EasyMarketingOne / EMAcción / Accio Marketing Engine  
Ruta base: /opt/easytech_marketing  
Fecha de referencia: junio 2026  

---

## 1. Objetivo del servidor

Este servidor existe para ejecutar el motor de marketing de EasyTech.

Su función es centralizar:

- Accio / EMAcción
- Motor de publicaciones
- Cola de tareas de marketing
- Integraciones con redes sociales
- Dashboard de control
- Archivos de campañas
- Automatizaciones de contenido

No es servidor de EN1, Odoo, EPOSOne ni EPayroll.

---

## 2. Regla principal de trabajo

Antes de modificar cualquier cosa, el programador debe:

1. Leer este archivo.
2. Verificar estado real del servidor.
3. Generar diagnóstico.
4. Presentar plan.
5. Esperar GO del dueño.
6. Ejecutar solo lo aprobado.
7. Dejar evidencia y actualizar este archivo.

No avanzar directo a implementación.

---

## 3. Estado conocido del servidor

Ruta principal:

```bash
/opt/easytech_marketing
```

Servicio systemd conocido:

- `easytech-accio-engine`

Dashboard conocido:

- https://n8n.etsrv.site/accio/
- https://n8n.etsrv.site/accio/dashboard

Endpoints conocidos:

- `/accio/tasks`
- `/accio/files/tree`
- `/accio/files/read`
- `/accio/cron/process`
- `/accio/post/force`

---

## 4. Contexto histórico

Este servidor tuvo confusión porque inicialmente se preparó para Accio, pero no estaba completamente claro qué parte era Accio real y qué parte era motor reconstruido.

Regla actual:

- No inventar otro motor si Accio ya cubre la necesidad.
- No reconstruir desde cero sin autorización.
- No duplicar carpetas ni servicios.
- No cambiar arquitectura sin GO.

---

## 5. Qué debe verificar el programador al iniciar sesión

Ejecutar y documentar salida resumida:

```bash
hostname
whoami
pwd
date
ls -lah /opt
ls -lah /opt/easytech_marketing
systemctl status easytech-accio-engine --no-pager
systemctl list-units --type=service | grep -i accio
ss -tulpn
df -h
free -h
```

Si hay Git:

```bash
cd /opt/easytech_marketing
git status
git branch
git log --oneline -5
```

Si hay Python:

```bash
cd /opt/easytech_marketing
ls -lah
find . -maxdepth 3 -name "requirements.txt" -o -name "pyproject.toml" -o -name ".env.example"
```

Si hay Docker:

```bash
docker ps
docker compose ls
```

---

## 6. Archivos obligatorios que deben existir

Crear o actualizar:

- `/opt/easytech_marketing/docs/PROJECT_STATE.md`
- `/opt/easytech_marketing/docs/INVENTARIO_DESPLIEGUE.md`
- `/opt/easytech_marketing/docs/CHANGELOG.md`
- `/opt/easytech_marketing/docs/NEXT_STEPS.md`
- `/opt/easytech_marketing/scripts/doctor.sh`

---

## 7. doctor.sh requerido

Crear este archivo:

```bash
#!/usr/bin/env bash
set -e

echo "=== ARROZCONPOLLO / EasyMarketingOne Doctor ==="
echo "Fecha:"
date
echo

echo "=== Host ==="
hostname
whoami
pwd
echo

echo "=== Sistema ==="
uptime
free -h
df -h
echo

echo "=== Puertos ==="
ss -tulpn || true
echo

echo "=== Servicios Accio ==="
systemctl status easytech-accio-engine --no-pager || true
systemctl list-units --type=service | grep -i accio || true
echo

echo "=== Ruta proyecto ==="
ls -lah /opt/easytech_marketing || true
echo

echo "=== Git ==="
cd /opt/easytech_marketing 2>/dev/null && git status || true
cd /opt/easytech_marketing 2>/dev/null && git branch || true
cd /opt/easytech_marketing 2>/dev/null && git log --oneline -5 || true
echo

echo "=== Python ==="
cd /opt/easytech_marketing 2>/dev/null && find . -maxdepth 3 -name "requirements.txt" -o -name "pyproject.toml" -o -name ".env.example" || true
echo

echo "=== Docker ==="
docker ps 2>/dev/null || true
docker compose ls 2>/dev/null || true

echo
echo "=== FIN DOCTOR ==="
```

Permisos:

```bash
chmod +x /opt/easytech_marketing/scripts/doctor.sh
```

---

## 8. Formato obligatorio de respuesta del programador

Cada vez que trabaje en ARROZCONPOLLO debe responder así:

```markdown
# Diagnóstico ARROZCONPOLLO

## 1. Qué encontré
...

## 2. Qué está funcionando
...

## 3. Qué no está claro
...

## 4. Riesgos
...

## 5. Plan propuesto
1.
2.
3.

## 6. Confirmación requerida
Esperando GO antes de modificar.
```

---

## 9. Prohibiciones

No hacer sin GO:

- No borrar carpetas.
- No reinstalar Accio.
- No cambiar Nginx.
- No cambiar dominios.
- No tocar certificados SSL.
- No modificar systemd.
- No mover proyecto a otra ruta.
- No crear motor alterno.
- No meter Docker si no existe necesidad.
- No publicar contenido real sin aprobación.
- No tocar credenciales ni tokens.

---

## 10. Próximo objetivo operativo

El objetivo inmediato es estabilizar ARROZCONPOLLO como servidor oficial de marketing EasyTech:

- Confirmar qué motor Accio está activo.
- Confirmar dashboard.
- Confirmar endpoints.
- Confirmar cola de tareas.
- Confirmar integración LinkedIn / Meta / Instagram / Google Ads.
- Confirmar estructura de archivos.
- Subir todo a Git si todavía no está versionado.
- Crear documentación viva.
- Dejar flujo claro para operar campañas.

---

## 11. Regla final

Si el programador no entiende el estado del servidor, debe detenerse.

No debe adivinar.

Primero debe ejecutar:

```bash
/opt/easytech_marketing/scripts/doctor.sh
```

Luego debe entregar diagnóstico y esperar GO.

---

## 12. Última estabilización (2026-06-26)

**GO ejecutado.** Cambios aplicados:

| Item | Resultado |
|------|-----------|
| Motor Accio | `easytech-accio-engine` activo en :8092, multi-tenant |
| Dashboard | https://n8n.etsrv.site/accio/dashboard/easytech/ |
| Cron tick | Corregido → `/accio/easytech/tick` — OK |
| API key RBAC | Bearer key con permisos de automatización |
| Docs vivos | `INVENTARIO`, `CHANGELOG`, `NEXT_STEPS` actualizados |
| Git | Repo activo en `main` |

**Auditoría endpoints (2026-06-26):**

| Endpoint | HTTP |
|----------|------|
| `/accio/health` | 200 |
| `/accio/status` | 200 |
| `/accio/easytech/tasks` | 200 |
| `/accio/files/tree` | 200 |
| `/accio/easytech/tick` | 200 |

**Conectores OAuth:** LinkedIn/Meta/Google servicios → 200. LinkedIn configured; Meta FB/IG test OK; Google Business pendiente tokens.

**Pendiente:** flyer IIUS (#10), post #4 (2026-06-30), n8n workflows activos, push Git.
