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
