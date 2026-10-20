#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba completa del MCP de navegador a través del proxy con token.

Uso:
    .venv/bin/python pruebas/prueba_completa.py

Comprueba, de punta a punta:
  1. Sin token, el proxy responde 401.
  2. `initialize` abre sesión y devuelve la cabecera `Mcp-Session-Id`.
  3. `tools/list` incluye `browser_navigate`.
  4. `browser_navigate` abre una página real y devuelve su contenido.
  5. Dos sesiones a la vez no se pisan (cada una abre su propio navegador).
  6. Las respuestas viajan como SSE y sin `Content-Length` (no bufferizadas).

No imprime el token ni el contenido del `.env`.
"""

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

RAIZ = Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
PROTOCOLO = "2025-06-18"
CLIENTE = {"name": "prueba-completa", "version": "1.0"}

FALLOS = 0


class Fallo(Exception):
    """Una comprobación no se cumplió."""


def comprobar(condicion: bool, descripcion: str) -> None:
    """Anota una comprobación y continúa con las demás."""
    global FALLOS
    if condicion:
        print(f"✔ {descripcion}")
    else:
        FALLOS += 1
        print(f"✘ {descripcion}")


def cargar_env(ruta: Path = ENV) -> dict:
    """Lee el `.env` sin dependencias externas."""
    datos = {}
    try:
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            datos[clave.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return datos


async def leer_jsonrpc(respuesta: aiohttp.ClientResponse) -> dict:
    """Lee una respuesta JSON o el primer evento SSE (transporte MCP)."""
    tipo = respuesta.headers.get("Content-Type", "")
    if "text/event-stream" in tipo:
        async for linea in respuesta.content:
            texto = linea.decode("utf-8", "replace").strip()
            if texto.startswith("data:"):
                return json.loads(texto[5:].strip())
        raise Fallo("respuesta SSE sin datos")
    return await respuesta.json()


def texto_resultado(datos: dict) -> str:
    """Extrae el texto de un resultado de `tools/call`."""
    contenido = (datos.get("result") or {}).get("content") or []
    return "\n".join(
        parte.get("text", "")
        for parte in contenido
        if parte.get("type") == "text"
    )


class Sesion:
    """Una sesión MCP: initialize, notificaciones y llamadas a herramientas."""

    def __init__(self, http: aiohttp.ClientSession, endpoint: str, token: str):
        self.http = http
        self.endpoint = endpoint
        self.cabeceras = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self.id = None

    async def enviar(self, cuerpo: dict, leer: bool = True):
        """Envía una petición JSON-RPC y devuelve (info, datos)."""
        cabeceras = dict(self.cabeceras)
        if self.id:
            cabeceras["Mcp-Session-Id"] = self.id
        async with self.http.post(self.endpoint, headers=cabeceras, json=cuerpo) as respuesta:
            info = {
                "estado": respuesta.status,
                "tipo": respuesta.headers.get("Content-Type", ""),
                "largo": respuesta.headers.get("Content-Length"),
                "sesion": respuesta.headers.get("Mcp-Session-Id"),
            }
            datos = await leer_jsonrpc(respuesta) if leer else None
            return info, datos

    async def abrir(self) -> dict:
        """Hace `initialize` y `notifications/initialized`. Devuelve la info del primero."""
        info, datos = await self.enviar({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOLO,
                "capabilities": {},
                "clientInfo": CLIENTE,
            },
        })
        if info["estado"] != 200:
            raise Fallo(f"initialize devolvió HTTP {info['estado']}")
        self.id = info["sesion"]
        if not self.id:
            raise Fallo("initialize no devolvió Mcp-Session-Id")
        if not (datos or {}).get("result"):
            raise Fallo("initialize no devolvió un resultado JSON-RPC")

        info_notificacion, _ = await self.enviar(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}, leer=False)
        if info_notificacion["estado"] not in (200, 202, 204):
            raise Fallo(
                f"notifications/initialized devolvió HTTP {info_notificacion['estado']}")
        return info

    async def herramientas(self) -> list:
        _, datos = await self.enviar(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        return [item.get("name") for item in (datos.get("result") or {}).get("tools", [])]

    async def llamar(self, nombre: str, argumentos: dict, id_peticion: int) -> tuple:
        """Llama a una herramienta y devuelve (texto, info)."""
        info, datos = await self.enviar({
            "jsonrpc": "2.0",
            "id": id_peticion,
            "method": "tools/call",
            "params": {"name": nombre, "arguments": argumentos},
        })
        if info["estado"] != 200:
            raise Fallo(f"{nombre} devolvió HTTP {info['estado']}")
        resultado = (datos or {}).get("result") or {}
        if resultado.get("isError"):
            raise Fallo(f"{nombre} devolvió isError: {texto_resultado(datos)[:200]}")
        return texto_resultado(datos), info

    async def cerrar(self) -> None:
        """Cierra el navegador de esta sesión, si sigue vivo."""
        try:
            await self.llamar("browser_close", {}, 9)
        except (Fallo, aiohttp.ClientError):
            pass


async def flujo_navegacion(http: aiohttp.ClientSession, endpoint: str,
                            token: str, url: str) -> str:
    """Abre una sesión nueva y navega; devuelve el texto de la página."""
    sesion = Sesion(http, endpoint, token)
    await sesion.abrir()
    try:
        texto, _ = await sesion.llamar("browser_navigate", {"url": url}, 3)
        return texto
    finally:
        await sesion.cerrar()


async def main() -> int:
    env = cargar_env()
    token = env.get("MCP_TOKEN", "").strip()
    puerto = env.get("MCP_PROXY_PUERTO", "8931").strip() or "8931"
    if not token:
        print("✘ Falta MCP_TOKEN en el .env: no se puede probar.")
        return 2

    endpoint = f"http://127.0.0.1:{puerto}/mcp"
    tiempo = aiohttp.ClientTimeout(total=240, sock_connect=15, sock_read=240)

    async with aiohttp.ClientSession(timeout=tiempo) as http:
        print("== 1) sin token (debe dar 401) ==")
        async with http.post(
            endpoint,
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                  "params": {"protocolVersion": PROTOCOLO,
                             "capabilities": {}, "clientInfo": CLIENTE}},
        ) as respuesta:
            comprobar(respuesta.status == 401,
                      f"sin token responde 401 (HTTP {respuesta.status})")

        print("== 2) initialize, tools/list y navegación ==")
        sesion = Sesion(http, endpoint, token)
        try:
            info = await sesion.abrir()
            comprobar(True, "initialize abre sesión con Mcp-Session-Id")
            comprobar("text/event-stream" in info["tipo"],
                      f"initialize viaja como SSE ({info['tipo'] or 'sin tipo'})")
            comprobar(info["largo"] is None,
                      "initialize no trae Content-Length (no bufferizado)")

            nombres = await sesion.herramientas()
            comprobar("browser_navigate" in nombres,
                      "tools/list incluye browser_navigate")

            texto, info_nav = await sesion.llamar(
                "browser_navigate", {"url": "https://example.com"}, 3)
            comprobar("Example Domain" in texto,
                      "browser_navigate abre example.com y devuelve su contenido")
            comprobar("text/event-stream" in info_nav["tipo"]
                      and info_nav["largo"] is None,
                      "tools/call viaja como SSE sin Content-Length")

            print("== 3) flujo SSE (GET) ==")
            cabeceras = {"Authorization": f"Bearer {token}",
                         "Accept": "text/event-stream",
                         "Mcp-Session-Id": sesion.id}
            async with http.get(endpoint, headers=cabeceras) as respuesta:
                estado = respuesta.status
                if estado == 200:
                    try:
                        linea = await asyncio.wait_for(respuesta.content.readline(), 5)
                        nota = (f"SSE abierto; recibió datos ({linea[:40]!r})"
                                if linea else "SSE abierto y cerrado sin datos")
                        comprobar(True, nota)
                    except asyncio.TimeoutError:
                        comprobar(True,
                                  "SSE abierto y seguía abierto a los 5 s (no bufferizado)")
                elif estado in (400, 405):
                    comprobar(True,
                              f"GET SSE no soportado por esta versión (HTTP {estado})")
                else:
                    comprobar(False, f"GET SSE inesperado: HTTP {estado}")
        finally:
            await sesion.cerrar()

        print("== 4) dos sesiones a la vez ==")
        resultados = await asyncio.gather(
            flujo_navegacion(http, endpoint, token, "https://example.com"),
            flujo_navegacion(http, endpoint, token, "https://example.org"),
            return_exceptions=True,
        )
        errores = [r for r in resultados if isinstance(r, Exception)]
        textos = [r for r in resultados if isinstance(r, str)]
        comprobar(not errores, "ninguna de las dos sesiones falló")
        for error in errores:
            print(f"  · {type(error).__name__}: {error}")
        comprobar(len(textos) == 2
                  and all("Example Domain" in texto for texto in textos),
                  "las dos sesiones concurrentes devolvieron el contenido esperado")

    print()
    if FALLOS:
        print(f"✘ {FALLOS} comprobación(es) fallida(s).")
        return 1
    print("✔ Todas las comprobaciones pasaron.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n· Prueba cancelada.")
        sys.exit(130)
