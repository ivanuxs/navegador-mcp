#!/usr/bin/env bash
# Levanta el Playwright MCP (interno, 127.0.0.1) y el proxy con token (0.0.0.0).
# Uso: ./arrancar.sh        (Ctrl+C para todo)
set -euo pipefail
cd "$(dirname "$0")"

# Versión fijada a propósito: `@latest` puede traer una versión nueva y romper lo
# que ya está probado. Al subirla, se prueba y se cambia aquí.
VERSION_PLAYWRIGHT="0.0.83"

if [[ ! -f .env ]]; then
    echo "✘ Falta el .env. Créalo desde la plantilla y dale permisos 600:"
    echo "    cp .env.example .env && chmod 600 .env"
    exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
    echo "✘ Falta el entorno: no existe .venv/bin/python."
    echo "    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    echo "    (en oficina-2 no hay python3-venv: se creó con --without-pip y get-pip.py)"
    exit 1
fi

# Valores del .env (sin imprimirlos).
INTERNO=$(grep -E '^MCP_INTERNO_PUERTO=' .env | cut -d= -f2 | tr -d ' \r')
INTERNO=${INTERNO:-8930}

if (echo > "/dev/tcp/127.0.0.1/${INTERNO}") 2>/dev/null; then
    echo "✘ El puerto ${INTERNO} ya está ocupado: quedó otro MCP vivo."
    echo "    ./parar.sh   y vuelve a intentarlo."
    exit 1
fi

# Opciones del navegador según dónde corra:
# - En el portátil (con sesión gráfica) se abre una ventana normal.
# - En un servidor sin pantalla, sin ventana y sin sandbox: Ubuntu 24.04 no permite
#   los espacios de nombres sin privilegios y el sandbox de Chromium no arranca.
EXTRA_MCP=()
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    EXTRA_MCP+=(--headless --no-sandbox)
fi

# Chrome del sistema si está; si no, el Chromium que descargó Playwright.
if [[ ! -x /opt/google/chrome/chrome ]]; then
    CHROMIUM=$(ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux64/chrome 2>/dev/null | sort -V | tail -1)
    if [[ -z "$CHROMIUM" ]]; then
        echo "✘ No hay Chrome del sistema ni Chromium de Playwright."
        echo "    npx playwright install chromium"
        exit 1
    fi
    EXTRA_MCP+=(--executable-path "$CHROMIUM")
fi

echo "· Arrancando Playwright MCP en 127.0.0.1:${INTERNO} (versión ${VERSION_PLAYWRIGHT})…"
# `--allowed-hosts *`: cuando nginx haga proxy, el Host será el dominio y el MCP
# lo rechazaría. Quien protege de verdad es el proxy con token, no esta comprobación.
# `--isolated`: cada sesión abre su propio navegador. Sin esto el perfil es compartido
# y la segunda sesión falla con «Browser is already in use», que es justo lo que pasa
# cuando varios agentes lo usan a la vez.
npx -y "@playwright/mcp@${VERSION_PLAYWRIGHT}" --port "$INTERNO" --host 127.0.0.1 \
    --allowed-hosts '*' --isolated "${EXTRA_MCP[@]}" >> logs/mcp_salida.txt 2>&1 &
PID_MCP=$!

limpiar() {
    echo
    echo "· Cerrando el MCP (pid ${PID_MCP})…"
    kill "$PID_MCP" 2>/dev/null || true
}
trap limpiar EXIT
# Con `exec` el shell y su `trap` desaparecían: si el proxy moría, el npx quedaba
# huérfano ocupando el puerto interno y el siguiente arranque fallaba al bindear.
trap 'exit 130' INT TERM

# Se espera a que el interno conteste antes de abrir el proxy.
LISTO=0
for _ in $(seq 1 40); do
    if (echo > "/dev/tcp/127.0.0.1/${INTERNO}") 2>/dev/null; then
        echo "✔ MCP interno escuchando."
        LISTO=1
        break
    fi
    sleep 0.5
done
if [[ "$LISTO" -ne 1 ]]; then
    echo "✘ El MCP no abrió el puerto ${INTERNO} en 20 s. Mira logs/mcp_salida.txt."
    exit 1
fi

echo "· Arrancando el proxy con token…"
./.venv/bin/python proxy.py &
PID_PROXY=$!
wait "$PID_PROXY"
