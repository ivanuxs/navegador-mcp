# AGENTS.md — Reglas del proyecto `mcp/navegador`

Servidor **MCP** que ofrece un navegador real (Chromium con Playwright) a agentes de IA,
con cobro por uso mediante **x402** (Nodit Agent PayGate) en una fase posterior.
Proyecto **independiente**: no comparte código, entorno ni configuración con
`../../Publicaciones/`. Vive bajo `mcp/` porque habrá más servidores MCP aquí (uno por carpeta).

---

## 0. Idioma

**Háblale siempre al usuario en español** (neutro peruano, con tuteo). También los
comentarios, los docstrings y los mensajes del código.

## 1. Plan antes de tocar

Ningún cambio se hace sin que el usuario diga **«procede»**. Primero se presenta el plan
con los pasos y una recomendación; se espera. Responder preguntas **no** autoriza a
implementar.

## 2. Claves y secretos

- Las claves viven **solo** en el `.env` (permisos `600`). Nunca en el código ni en git.
- **Todo valor del `.env` se enmascara** en los registros y en la consola, no solo el
  token: `MCP_TOKEN=ab12…` se escribe como `MCP_TOKEN=ab…****`. Aplica a `MCP_TOKEN`,
  `MCP_TOKEN_NODIT`, `MCP_TOKEN_AUDITORIA` y `MCP_TOKEN_MCPIZE`.
- También se enmascaran las cabeceras sensibles de las peticiones: `Authorization`,
  `x-api-key`, `cookie`.
- No se imprime nunca el contenido del `.env`, ni completo ni por partes.

## 3. Registros

- Se usa `utils_logging.py` (copia autónoma de la de `Publicaciones/`), no `print` sueltos.
- **Ojo:** ese módulo escribe **sin `\n`**, todo en una línea partida por `\r` y con una
  marca `[funcion:linea]` al final. Para leerlo hay que normalizar.
- Los registros van en `logs/`.

## 4. El servidor no queda abierto

- El MCP escucha **solo** en `127.0.0.1`.
- Lo único expuesto es el proxy, y **exige token**: sin `Authorization: Bearer` correcto
  devuelve `401` sin ejecutar nada.
- Cualquier herramienta nueva que se añada hereda esa protección.

## 5. Reinicio sin `sudo`

La unidad corre como `oficina-2` y tiene `Restart=on-failure` con `RestartSec=5`. Para
reiniciar el servicio sin contraseña se mata el proxy; `arrancar.sh` termina con código
distinto de cero, su `trap` cierra el MCP y systemd lo levanta otra vez:

```bash
pkill -TERM -f 'venv/bin/python proxy.py'
```

- **No** se mata `npx` a secas: el proxy quedaría vivo y el puerto interno ocupado.
- **No** se usa SIGKILL sobre `arrancar.sh`: no correría su `trap` y el MCP quedaría
  huérfano ocupando el 8930.
- Tras unos segundos, comprobar `systemctl is-active mcp-navegador` y que `8930` y `8931`
  vuelvan a escuchar; si no, mirar `logs/arranque.txt`.
- `systemctl stop` sigue necesitando `sudo`; esto solo sirve para reiniciar.

## 6. Alcance

- No se añaden herramientas al MCP «por si acaso». Cada una se justifica y se prueba.
- No se toca `../../Publicaciones/` ni sus archivos: este proyecto es hermano, no hijo.
- Las pruebas se escriben cuando el cambio lo exige y se ejecutan cuando el usuario lo dice.

## 7. Cuando pase a producción

- El portátil no sirve como servidor permanente (se suspende). La fase 2 lo mueve a
  `oficina-2` (servidor local, 8 GB) o a Cloudflare Containers.
- La puerta pública será `mcp.hlquantlabs.trade`, con nginx delante y el DNS de
  Cloudflare. El proxy de Cloudflare se activará cuando toque la monetización.
