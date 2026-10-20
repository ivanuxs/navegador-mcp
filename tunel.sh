#!/usr/bin/env bash
# RESERVADO. No se usa en la fase 1: el acceso va por nginx de oficina-2.
#
# Si algún día hace falta exponer el Dell sin tocar el router, esto abre un túnel
# saliente de Cloudflare. Ventaja: no depende de la red local ni de la IP fija.
# Inconveniente: la URL de `trycloudflare.com` cambia; con túnel con nombre hace
# falta `cloudflared tunnel login` (autorización en el navegador).
set -euo pipefail
cd "$(dirname "$0")"

PUERTO=$(grep -E '^MCP_PROXY_PUERTO=' .env | cut -d= -f2 | tr -d ' \r'); PUERTO=${PUERTO:-8931}

if ! command -v cloudflared >/dev/null; then
    echo "✘ Falta cloudflared. Instálalo en ~/.local/bin y vuelve a intentarlo."
    exit 1
fi

echo "· Túnel temporal hacia 127.0.0.1:${PUERTO} …"
exec cloudflared tunnel --url "http://127.0.0.1:${PUERTO}"
