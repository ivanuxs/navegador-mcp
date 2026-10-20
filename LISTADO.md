# Ficha de listado — Navegador MCP

Metadatos para publicar este servidor en Glama, MCP.so, MCP Market y MCPize.
Copia y pega; no hay que reescribir nada.

## Identidad

| Campo | Valor |
|---|---|
| Nombre | Navegador MCP |
| Slug | `navegador-mcp` |
| Título | Navegador MCP — Chromium real para agentes |
| Versión | 0.0.83 (Playwright MCP) |
| Categoría | Browser Automation |
| Etiquetas | `browser`, `playwright`, `chromium`, `scraping`, `automation`, `screenshots`, `remote` |
| Icono | `logo.png` (512×512) o `logo.svg` |
| Licencia del código | MIT |
| Licencia del servicio | Uso comercial bajo token |
| Licencia del motor | Apache-2.0 (Playwright) |
| Contacto | Ivan Medina Soto — `soporte@hlquantlabs.trade` — Perú |

## Descripción corta (≤160 caracteres)

> Navegador Chromium alojado para agentes de IA. Navega, rellena formularios, inspecciona la red y toma capturas. Sin instalar nada.

English:

> Hosted Chromium browser for AI agents. Navigate, fill forms, inspect network traffic and take screenshots. Nothing to install.

## Descripción larga

> Un navegador real, alojado y listo, para agentes que necesitan ver la web tal como
> la ve una persona. Corre Chromium con Playwright sobre un servidor propio y expone
> 25 herramientas MCP: navegación, clics, escritura, formularios, arrastrar y soltar,
> pestañas, diálogos, emulación de medios, lectura de la red y capturas de pantalla.
>
> Sirve para lo que un `fetch` no alcanza: sitios con JavaScript, sesiones con
> formularios, flujos de varios pasos, verificaciones visuales y diagnóstico de
> peticiones. Cada sesión MCP abre su propio navegador aislado; lo que ocurre en una
> no afecta a las demás.
>
> Está pensado para agentes que no pueden o no quieren ejecutar un navegador en su
> propia máquina: entornos sin escritorio, servidores pequeños, contenedores
> efímeros o clientes móviles.

English:

> A real, hosted browser for agents that need to see the web the way a person does.
> It runs Chromium through Playwright on our own server and exposes 25 MCP tools:
> navigation, clicks, typing, forms, drag and drop, tabs, dialogs, media emulation,
> network inspection and screenshots.
>
> Use it for what `fetch` cannot reach: JavaScript-heavy sites, form-driven sessions,
> multi-step flows, visual checks and request-level debugging. Every MCP session gets
> its own isolated browser, so one client never sees another's state.
>
> Built for agents that cannot or will not run a browser locally: headless machines,
> small servers, ephemeral containers or mobile clients.

## Conexión

| Campo | Valor |
|---|---|
| Endpoint | `https://mcp.hlquantlabs.trade/mcp` |
| Transporte | Streamable HTTP, con respuestas SSE |
| Autenticación | Cabecera `Authorization: Bearer <token>` |
| Sin token | `401`, no se ejecuta nada |
| Red | El servidor MCP escucha solo en `127.0.0.1`; la única puerta es el proxy con TLS |

```json
{
  "mcpServers": {
    "navegador": {
      "type": "http",
      "url": "https://mcp.hlquantlabs.trade/mcp",
      "headers": { "Authorization": "Bearer <token>" }
    }
  }
}
```

## Herramientas (25)

| Grupo | Herramientas |
|---|---|
| Navegación | `browser_navigate`, `browser_navigate_back`, `browser_tabs` |
| Interacción | `browser_click`, `browser_type`, `browser_hover`, `browser_drag`, `browser_drop`, `browser_select_option`, `browser_press_key`, `browser_fill_form`, `browser_file_upload`, `browser_handle_dialog` |
| Inspección | `browser_snapshot`, `browser_find`, `browser_take_screenshot`, `browser_console_messages`, `browser_network_requests`, `browser_network_request`, `browser_evaluate` |
| Ventana y espera | `browser_resize`, `browser_wait_for`, `browser_emulate_media`, `browser_close` |
| Avanzado | `browser_run_code_unsafe` |

`browser_run_code_unsafe` ejecuta código Playwright dentro del proceso del servidor.
Es potente y equivale a ejecución remota de código: conviene desactivarla para
clientes no confiables.

## Ejemplos de uso

- «Entra a la página de precios de este competidor y dime qué planes ofrecen.»
- «Rellena el formulario de contacto de este sitio con estos datos y confirma el envío.»
- «Toma una captura de esta URL en escritorio y otra en móvil.»
- «Revisa qué peticiones hace esta página al cargar y si alguna falla.»
- «Busca en esta tabla el botón de descarga y pulsa el segundo resultado.»

## Límites conocidos

- Cada sesión abre una instancia de Chromium y ocupa cerca de 575 MB. En el equipo
  actual conviene no pasar de cuatro sesiones simultáneas.
- Corre en modo `headless` y sin sandbox dentro del contenedor del servicio.
- La sesión se cierra sola tras una hora sin actividad.
- No conserva cookies entre sesiones salvo que el cliente mantenga el identificador
  de sesión.
- Solo alcanza direcciones de internet; no sirve para la red interna del servidor.

## Verificación

```bash
# Sin token debe responder 401
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://mcp.hlquantlabs.trade/mcp

# Con token: initialize y tools/list
curl -s -X POST https://mcp.hlquantlabs.trade/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"prueba","version":"1"}}}'
```
