# Navegador MCP

A hosted Chromium browser for AI agents. 25 MCP tools to navigate, click, type, fill
forms, inspect network traffic and take screenshots — without installing a browser
anywhere.

**Español:** navegador Chromium alojado para agentes de IA. Navega, rellena formularios,
lee la red y toma capturas, sin instalar nada. El servicio corre en un servidor propio;
este repositorio es el código del proxy con token y de la unidad de servicio.

## Connect

| | |
|---|---|
| Endpoint | `https://mcp.hlquantlabs.trade/mcp` |
| Transport | Streamable HTTP (SSE responses) |
| Auth | `Authorization: Bearer <token>` — without it, `401` |

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

## Tools

| Group | Tools |
|---|---|
| Navigation | `browser_navigate`, `browser_navigate_back`, `browser_tabs` |
| Interaction | `browser_click`, `browser_type`, `browser_hover`, `browser_drag`, `browser_drop`, `browser_select_option`, `browser_press_key`, `browser_fill_form`, `browser_file_upload`, `browser_handle_dialog` |
| Inspection | `browser_snapshot`, `browser_find`, `browser_take_screenshot`, `browser_console_messages`, `browser_network_requests`, `browser_network_request`, `browser_evaluate` |
| Window & timing | `browser_resize`, `browser_wait_for`, `browser_emulate_media`, `browser_close` |
| Advanced | `browser_run_code_unsafe` |

## Notes and limits

- Each MCP session gets its own isolated browser, so clients never share state.
- A session uses roughly 575 MB of RAM; four concurrent sessions is the practical
  ceiling on our current host.
- Headless, no sandbox, no screen.
- Sessions close after one hour of inactivity.
- Only reaches public internet addresses.

`browser_run_code_unsafe` runs arbitrary Playwright code inside the server process.
Treat it as remote code execution and disable it for untrusted clients.

## Docs

- [`LISTADO.md`](LISTADO.md) — listing metadata for MCP directories (ES/EN), tools,
  limits and a `curl` check.
- [`LEEME.md`](LEEME.md) — operating notes in Spanish: proxy, ports, systemd, nginx.
- [`NODIT.md`](NODIT.md) — x402 payment gateway integration notes.

## License

MIT. See [LICENSE](LICENSE). The hosted service is sold separately under a token.

## Contact

`soporte@hlquantlabs.trade`
