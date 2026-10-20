# mcp/navegador

Servidor **MCP** (Model Context Protocol) que da a los agentes de IA un **navegador real**
(Chromium con Playwright): abrir páginas, leer contenido, pulsar por texto, escribir y
capturar pantalla.

Vive en `Proyectos/mcp/navegador/`: bajo `mcp/` habrá un servidor por carpeta, cada uno
con su entorno, su `.env` y sus registros. Independiente de `../../Publicaciones/`.

---

## Arquitectura

```
Agente
  │  Authorization: Bearer <MCP_TOKEN>
  ▼
DNS de Cloudflare  →  nginx del servidor
  │  proxy_pass a 127.0.0.1:8931
  ▼
proxy.py en oficina-2 (valida token, 401 si falta)
  │
  ▼
127.0.0.1:8930            ← Playwright MCP (no expuesto)
```

- Todo corre en **oficina-2** (8 GB, siempre encendida): nginx, el proxy y el MCP.
- **El MCP nunca escucha fuera de `127.0.0.1`.**
- El proxy escucha en `0.0.0.0:8931`, pero en el servidor solo lo alcanza nginx por
  `127.0.0.1`: el cortafuegos no necesita ninguna regla.
- El cobro por uso (x402) irá **delante** de todo esto, con Nodit Agent PayGate.
- El Dell queda como **copia de desarrollo**: mismo proyecto y mismo `.env`, servicio de
  usuario de systemd, pero no sirve la puerta pública.

## Arrancar

Corre en **oficina-2** como servicio **del sistema**
(`sistema/mcp-navegador.sistema.service`): arranca al encender y se reinicia si muere.

```bash
sudo systemctl start mcp-navegador
sudo systemctl stop mcp-navegador
sudo systemctl status mcp-navegador
journalctl -u mcp-navegador -f      # registros del arranque
```

Si se cambia la unidad en el repo:

```bash
sudo cp ~/Nextcloud/Proyectos/mcp/navegador/sistema/mcp-navegador.sistema.service \
        /etc/systemd/system/mcp-navegador.service
sudo systemctl daemon-reload && sudo systemctl restart mcp-navegador
```

Arranque a mano (para depurar): primero `sudo systemctl stop mcp-navegador`, luego

```bash
export PATH=$HOME/.local/node/bin:$PATH
./arrancar.sh          # Ctrl+C o ./parar.sh para cerrar
```

> **Ojo:** con el servicio activo, `./parar.sh` no sirve para apagarlo — systemd lo
> resucita a los 5 s. Se para con `systemctl stop mcp-navegador`.

`arrancar.sh` fija la versión de Playwright (`0.0.83`) a propósito: `@latest` puede
traer una versión nueva y romper lo que ya está probado. Si sale con error (falta el
`.env`, puerto ocupado), systemd no se queda reintentando sin fin: 5 intentos y para.

## Qué necesita la máquina

| Pieza | Cómo está en `oficina-2` |
|---|---|
| Node 22 | en `~/.local/node` (tarball oficial, sin `sudo`) |
| MCP | `npx @playwright/mcp@0.0.83`, fijado en `arrancar.sh` y en `package.json` |
| Chromium | `~/.cache/ms-playwright/chromium-1247` (`npx playwright install chromium`) |
| Python | `.venv` con `aiohttp` (`requirements.txt`; creado con `--without-pip` + `get-pip.py`, sin `python3-venv`) |
| Modo | `--headless --no-sandbox --executable-path …` cuando no hay pantalla |

The Dell, para desarrollo, usa el Chrome del sistema y abre ventana normal.

## Abrir el proyecto desde oficina-2

La copia que **está en marcha** es la del servidor:
`/home/oficina-2/Nextcloud/Proyectos/mcp/navegador` (27 MB).

**Ya está allí:** el servicio activo, `.venv` con `aiohttp`, Node 22 en `~/.local/node`,
Chromium de Playwright en `~/.cache/ms-playwright` (674 MB), `git` 2.43 y `curl`.

**Lo que falta para editarlo desde esa máquina:**

| Falta | Qué hacer |
|---|---|
| **Editor** | no hay ninguno instalado: ni `code`, ni `codium`, ni `code-server` |
| **Escritorio** | no hay sesión gráfica: un VS Code normal no se podría abrir ahí |
| **Node en el PATH** | `~/.local/node/bin` no está en `~/.bashrc`; a mano: `export PATH=$HOME/.local/node/bin:$PATH` |
| **Permisos** | `sudo` pide contraseña (solo `/usr/bin/rsync` va sin ella) |

La forma recomendada, sin instalar nada allí: **VS Code Remote-SSH** desde otro equipo
(el Dell) contra `oficina-2`. El servidor se instala solo el VS Code Server en
`~/.vscode-server` y no hace falta `sudo`.

Si se quiere un editor *dentro* del servidor y sin escritorio, la opción es `code-server`
(IDE en el navegador): binario en `~/.local`, escucha en `127.0.0.1:8080` y se abre con un
túnel SSH (`ssh -L 8080:127.0.0.1:8080 oficina-2`). Tampoco necesita `sudo`.

**Trabajar entre las dos máquinas** — el Dell edita, el servidor ejecuta:

**[EN EL DELL]**

```bash
rsync -a --exclude='.venv/' --exclude='__pycache__/' --exclude='logs/*.txt' \
  ~/Nextcloud/Proyectos/mcp/navegador/ \
  oficina-2:~/Nextcloud/Proyectos/mcp/navegador/
```

**[EN OFICINA-2]**

```bash
sudo systemctl restart mcp-navegador
```

> Si algún día se sincroniza esa carpeta con Nextcloud, excluir `.venv/`, `.env` y
> `logs/*.txt`: el `.env` lleva el token y Nextcloud rompe los entornos virtuales.

## Probar

```bash
./pruebas/prueba_mcp.sh                      # proxy: 401 sin token / 200 con token
.venv/bin/python pruebas/prueba_completa.py  # navegación real, concurrencia y SSE
```

La primera prueba debe dar **401** sin token y **200** con él. La segunda abre
`example.com` con Chromium, comprueba que `tools/list` incluye `browser_navigate`,
lanza **dos sesiones a la vez** y verifica que las respuestas viajan como SSE sin
`Content-Length` (sin bufferizar). Tarda unos segundos porque abre navegadores reales.

Comprobado el 2026-10-19, de punta a punta:

```
127.0.0.1:8930                ← interno, solo local (oficina-2)
127.0.0.1:8931                ← proxy con token (solo lo alcanza nginx)
nginx de oficina-2            ← 401 sin token · 200 con token
https://mcp.hlquantlabs.trade ← 401 sin token · 200 con token (DNS-only)
navegación real               ← example.com abierta con Chromium headless
dos sesiones a la vez         ← cada una con su propio navegador
SSE                           ← text/event-stream, sin Content-Length
```

Para probarlo desde el propio servidor:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://127.0.0.1:8931/mcp \
  -H "Authorization: Bearer <MCP_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"prueba","version":"1"}}}'
```

Desde otra máquina se prueba contra `https://mcp.hlquantlabs.trade`, no contra el 8931:
el proxy ya no está expuesto a la red, solo a nginx.

## Configuración (`.env`, permisos 600)

| Clave | Para qué |
|---|---|
| `MCP_INTERNO_PUERTO` | Puerto del Playwright MCP (127.0.0.1) |
| `MCP_PROXY_PUERTO` | Puerto del proxy con token (escucha en 0.0.0.0) |
| `MCP_TOKEN` | Token que deben enviar los clientes |
| `MCP_TOKEN_NODIT` | Token exclusivo de Nodit; se revoca quitando su línea y reiniciando |
| `MCP_TOKEN_AUDITORIA` | Token exclusivo del servicio de auditoría; se revoca igual |
| `MCP_DOMINIO` | `mcp.hlquantlabs.trade` |
| `X402_PRECIO_USD` | Precio por llamada, para el alta en Nodit |
| `X402_RED` | `base` o `solana` |

La plantilla está en `.env.example`:

```bash
cp .env.example .env && chmod 600 .env
openssl rand -hex 32        # valor para MCP_TOKEN
```

**Ningún valor del `.env` se imprime**: `proxy.py` los enmascara todos antes de registrar,
y `pruebas/prueba_mcp.sh` comprueba que el token no aparezca en claro en `logs/`.

## Repositorio

El proyecto es un repositorio git local (rama `main`). El `.env`, el `.venv`, los
registros y los artefactos de Playwright están en `.gitignore`: nunca se versionan.

```bash
git log --oneline
git status
```

La identidad es local al repositorio (`MCP Navegador <mcp-navegador@localhost>`), no
toca la configuración global. Como la carpeta se sincroniza con Nextcloud, evita
`git` en las dos máquinas a la vez: edita y confirma en una y sincroniza después.

## Lo que falta

1. **Nodit Agent PayGate**: el alta se envió el **2026-10-19** por el formulario de
   Contact Sales y quedó confirmada. El token dedicado (`MCP_TOKEN_NODIT`) ya existe.
   Pendiente: respuesta de Nodit, entrega del token por un canal seguro, KYC con el DNI y
   pruebas contra su configuración.
2. **Cloudflare**: el registro `mcp.` está en modo **solo-DNS**, sin proxy. Mientras
   siga así, la IP de origen queda expuesta; el proxy se reactivará cuando toque la
   monetización. Si al reactivarlo vuelve la redirección a `app.alimentosxms.com`, es la
   Redirect Rule de `mcp.`: hay que quitarla.

## Publicación

- `LISTADO.md` reúne los metadatos para Glama, MCP.so, MCP Market y MCPize: nombre,
  descripciones en español e inglés, categoría, etiquetas, herramientas y límites.
- `logo.png` (512×512) y `logo.svg` son el icono del listado.
- **Antes de hacer público este repositorio**, quitar el DNI de `NODIT.md`: hoy está
  escrito en claro y no debe salir de aquí. El `.env` ya queda fuera por `.gitignore`.

## Avisos

- `utils_logging.py` escribe **sin `\n`**: todo va en una línea partida por `\r`. Para
  leer los registros hay que normalizar.
- En `oficina-2` no hay pantalla: Chromium corre `--headless` y con `--no-sandbox`
  (Ubuntu 24.04 no permite los espacios de nombres sin privilegios y el sandbox falla).
- Cada sesión abre **su propio** navegador (`--isolated`). Sin eso el perfil es compartido
  y la segunda sesión falla con «Browser is already in use»: con varios agentes a la vez
  pasaría siempre.
- La configuración de nginx se versiona aquí, en `nginx/mcp.hlquantlabs.trade.conf`.
  Incluye el bloque 443 y la redirección a HTTPS que generó certbot, y es copia exacta
  de la del servidor salvo los comentarios. Si se cambia la de aquí, hay que volver a
  copiarla a `oficina-2` y recargar nginx.