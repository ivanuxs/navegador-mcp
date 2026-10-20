# Alta en Nodit · Agent PayGate (x402)

El cobro va **delante** de todo: Nodit recibe la petición del agente, cobra en USDC y
reenvía a nuestro upstream con el token. El proxy y el MCP no cambian.

Es un **alta por contacto**, no autoservicio: se envía la configuración y Nodit la monta.

## Estado

- **2026-10-19**: alta enviada por el formulario de Contact Sales
  (https://www.nodit.io/contact-us), con envío confirmado («The inquiry was sent
  successfully»).
- Pendiente: respuesta de Nodit, entrega de `MCP_TOKEN_NODIT` por un canal seguro, KYC
  con el DNI y pruebas contra su configuración.

> El formulario falla si el navegador lleva VPN o bloqueadores (Brave Shields). Se envió
> desde un navegador limpio, sin escudos y sin VPN.

## Configuración que hay que darles

```yaml
upstream:    https://mcp.hlquantlabs.trade      # el MCP vive en /mcp
auth:        Bearer <MCP_TOKEN_NODIT>           # token exclusivo; el valor está en el .env
price:       <X402_PRECIO_USD> USDC / call      # también en el .env
settles on:  Base
settlement:  <X402_CARTERA>                     # el valor real está en el .env
modes:       Credit + Pay-Per-Use
```

La cartera se comprobó contra la red Base: es una **EOA** (no un contrato) y hoy está
vacía, que es lo normal porque solo recibe liquidaciones. Ni la dirección ni el DNI se
versionan aquí: la cartera vive en el `.env` y el DNI se entrega en el formulario de
alta.

Comprobado el 2026-10-19: el upstream responde `401` sin token y `200` con token, y
`browser_navigate` abre una página real.

## Comprobaciones previas

- [x] Precio por llamada (`X402_PRECIO_USD`): definido y válido en el `.env`.
- [x] Cartera de liquidación en Base: `X402_CARTERA` en el `.env` (EOA comprobada en
      la red).
- [x] Contacto: Ivan Medina Soto, propietario, `ivanuxs@gmail.com`, Perú.
- [ ] DNI: se entrega en el KYC que indique Nodit; no se versiona aquí.
- [x] Token dedicado `MCP_TOKEN_NODIT` creado en el `.env`; el token general sigue
      valiendo para los agentes actuales. Se revoca quitando esa línea y reiniciando.

## Preguntas que hay que hacerles

Son las que pueden cambiar el diseño del cobro:

1. **Qué cuenta como «llamada» en MCP.** Una sesión hace varios POST (`initialize`,
   `notifications/initialized`, `tools/list`, cada `tools/call`) y puede dejar un GET
   SSE abierto minutos. ¿Cobran por petición HTTP, por mensaje JSON-RPC o por `tools/call`?
2. **SSE:** un flujo abierto, ¿se factura una vez o por evento?
3. **Modo Credit:** su sesión firmada dura 1 hora. ¿Convive con `Mcp-Session-Id`? ¿Qué
   pasa si el agente encadena sesiones?
4. **IPs de reenvío:** ¿desde qué direcciones nos llegan sus peticiones? (por si algún día
   hay que restringir el 8931 a esas IPs en vez de fiarse solo del token).
5. **Descubrimiento:** ¿cómo encuentran los agentes nuestro servicio? ¿hay catálogo x402
   o algún `/.well-known/` que debamos publicar?
6. **Latencia:** su FAQ dice que Pay-Per-Use añade un pago por llamada. Para MCP, que
   hace varias por sesión, ¿recomiendan Credit como modo principal?

## Mensaje para enviar

> Hello,
>
> We run a remote MCP server (Model Context Protocol over Streamable HTTP) that gives AI
> agents a real Chromium browser through Playwright: open pages, read content, click by
> text, type and take screenshots. It is live at https://mcp.hlquantlabs.trade/mcp.
>
> We would like to monetize it with Agent PayGate, using **Credit** and
> **Pay-Per-Use**, settling in **USDC on Base**.
>
> Configuration:
>
> - upstream: `https://mcp.hlquantlabs.trade` (MCP endpoint: `/mcp`)
> - auth: `Authorization: Bearer <token>` (dedicated token, provided privately)
> - price: `<price>` USDC per call
> - settlement: `<X402_CARTERA>` (USDC on Base)
> - contact: Ivan Medina Soto, owner, `ivanuxs@gmail.com` (Peru)
>
> A few things we need to clarify before going live:
>
> 1. An MCP session is not a single HTTP request: it sends `initialize`,
>    `notifications/initialized`, `tools/list` and one POST per `tools/call`, and may keep
>    an SSE stream open. What do you count as a billable call?
> 2. How is an open SSE stream billed?
> 3. In Credit mode, how does your one-hour signed session interact with `Mcp-Session-Id`?
> 4. Which IPs will forward requests to our upstream?
> 5. How do agents discover our service (x402 catalog, well-known metadata)?
>
> We can provide a test token and the DNI for KYC if needed.
>
> Thanks.
