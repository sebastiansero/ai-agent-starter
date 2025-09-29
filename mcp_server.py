#!/usr/bin/env python3
import asyncio, json, sys
from typing import Any, Dict

# Importa tus herramientas del proyecto (asegúrate de ejecutar desde la carpeta del proyecto)
try:
    from tools import (
        memory_get,
        memory_set,
        rag_search,
        rag_upsert_url,
    )
except Exception as e:
    print(json.dumps({"ok": False, "error": f"cannot import tools: {e}"}))
    sys.exit(1)

async def handle(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Router simple:
      - method: nombre del método
      - params: dict con argumentos
    Devuelve un dict JSON serializable.
    """
    method = req.get("method")
    params = req.get("params") or {}

    if method == "memory.get":
        return memory_get({"key": params.get("key")})

    if method == "memory.set":
        return memory_set({"key": params.get("key"), "value": params.get("value")})

    if method == "rag.search":
        return rag_search({"query": params.get("query"), "k": params.get("k", 3)})

    if method == "rag.upsert_url":
        return rag_upsert_url({"url": params.get("url"), "max_chars": params.get("max_chars", 6000)})

    return {"ok": False, "error": f"unknown method: {method}"}

async def main() -> None:
    """
    Bucle stdio:
      - Lee 1 línea por stdin (JSON)
      - Responde 1 línea por stdout (JSON)
    """
    print("MCP-like stdio server ready", flush=True)
    loop = asyncio.get_event_loop()

    while True:
        try:
            # Lee una línea; si es EOF, salimos
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            # Parseo del JSON de entrada
            try:
                req = json.loads(line)
            except json.JSONDecodeError as e:
                print(json.dumps({"ok": False, "error": f"bad json: {e}"}), flush=True)
                continue

            # Despacho al handler
            try:
                res = await handle(req)
            except Exception as e:
                res = {"ok": False, "error": f"handler error: {e}"}

            # Respuesta en 1 línea
            print(json.dumps(res, ensure_ascii=False), flush=True)

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(main())

