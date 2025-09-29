# -*- coding: utf-8 -*-
# Herramientas del agente y del servidor MCP
# - Memoria simple en proceso
# - RAG simple basado en JSONL + embeddings de OpenAI (opcional)

import os
import json
import math
from typing import Any, Dict, Tuple

import requests

# ---------- Utilidades comunes ----------

def _ok(ok: bool, data: Any, error: str) -> Dict[str, Any]:
    return {"ok": ok, "data": data, "error": error}

# Memoria efímera en proceso
_MEM: Dict[str, Any] = {}


def memory_set(args: Dict[str, Any]) -> Dict[str, Any]:
    key = args.get("key")
    if not key:
        return _ok(False, None, "Falta 'key'")
    _MEM[key] = args.get("value")
    return _ok(True, {"key": key}, "")


def memory_get(args: Dict[str, Any]) -> Dict[str, Any]:
    key = args.get("key")
    if not key:
        return _ok(False, None, "Falta 'key'")
    return _ok(True, {"value": _MEM.get(key)}, "")

# ---------- RAG (opcional) ----------

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
RAG_PATH = os.getenv("RAG_PATH", "rag_store.jsonl")
_client = None


def _get_client():
    """Crea el cliente de OpenAI de forma diferida para no romper si no está instalado."""
    global _client
    if _client is None:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise RuntimeError(f"OpenAI SDK no disponible: {e}")
        _client = OpenAI()  # usa OPENAI_API_KEY del entorno
    return _client


def _embed(text: str):
    client = _get_client()
    emb = client.embeddings.create(model=EMBED_MODEL, input=text)
    return emb.data[0].embedding


def _rag_load():
    items = []
    if not os.path.exists(RAG_PATH):
        return items
    with open(RAG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except Exception:
                pass
    return items


def _rag_append(item: dict):
    with open(RAG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def rag_upsert_url(args: Dict[str, Any]) -> Dict[str, Any]:
    url = args.get("url")
    max_chars = int(args.get("max_chars", 6000))
    if not url:
        return _ok(False, None, "Falta 'url'")
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status()
        text = r.text[:max_chars]
    except Exception as e:
        return _ok(False, None, f"Error al leer URL: {e}")

    try:
        vec = _embed(text)
        _rag_append({"id": url, "text": text, "embedding": vec})
        return _ok(True, {"upserted": url}, "")
    except Exception as e:
        return _ok(False, None, f"Error al embeder: {e}")


def rag_search(args: Dict[str, Any]) -> Dict[str, Any]:
    q = args.get("query")
    k = int(args.get("k", 3))
    if not q:
        return _ok(False, None, "Falta 'query'")
    items = _rag_load()
    if not items:
        return _ok(True, {"matches": []}, "")
    qv = _embed(q)

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return 0.0 if na == 0 or nb == 0 else dot / (na * nb)

    scored = []
    for it in items:
        s = cosine(qv, it["embedding"])
        scored.append({"id": it["id"], "score": s, "text": it["text"][:500]})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return _ok(True, {"matches": scored[:k]}, "")

# ---------- Catálogo y dispatcher ----------

TOOLS: Dict[str, Tuple[str, callable]] = {
    "memory_set": (
        "Guarda un valor en memoria efímera. Args: {'key': '...', 'value': <any>}",
        memory_set,
    ),
    "memory_get": (
        "Lee un valor de memoria por clave. Args: {'key': '...'}",
        memory_get,
    ),
    "rag_upsert_url": (
        "Indexa el texto de una URL en la base vectorial. Args: {'url': 'https://...', 'max_chars': 6000}",
        rag_upsert_url,
    ),
    "rag_search": (
        "Busca en la base vectorial y devuelve top-k trozos. Args: {'query': '...', 'k': 3}",
        rag_search,
    ),
}


def tool_catalog_text() -> str:
    lines = []
    for name in sorted(TOOLS.keys()):
        desc = TOOLS[name][0]
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)


def call_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    tool = TOOLS.get(tool_name)
    if not tool:
        return _ok(False, None, f"unknown tool: {tool_name}")
    _, fn = tool
    try:
        return fn(args if isinstance(args, dict) else {})
    except Exception as e:
        return _ok(False, None, f"tool error: {e}")

# --- BÚSQUEDA WEB + EXTRACCIÓN DE TEXTO LIMPIO ---

from duckduckgo_search import DDGS
import trafilatura

def web_search(args):
    """
    Busca en la web usando DuckDuckGo.
    Args:
      {'query':'...', 'k': 5}
    Devuelve:
      {'results': [{'title':..., 'url':..., 'snippet':...}, ...]}
    """
    q = args.get("query")
    k = int(args.get("k", 5))
    if not q:
        return _ok(False, None, "Falta 'query'")
    try:
        results = []
        # safesearch: "moderate" para resultados limpios
        with DDGS() as ddgs:
            for r in ddgs.text(q, max_results=k, safesearch="moderate"):
                results.append({
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "snippet": r.get("body")
                })
        return _ok(True, {"results": results}, "")
    except Exception as e:
        return _ok(False, None, f"Error en búsqueda: {e}")

def read_url_clean(args):
    """
    Descarga una URL y extrae el contenido principal (texto) con trafilatura.
    Args:
      {'url':'https://...', 'max_chars': 4000}
    Devuelve:
      {'text': '...'}
    """
    url = args.get("url")
    max_chars = int(args.get("max_chars", 4000))
    if not url:
        return _ok(False, None, "Falta 'url'")
    try:
        downloaded = trafilatura.fetch_url(url, timeout=25)
        if not downloaded:
            return _ok(False, None, "No se pudo descargar la URL")
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_recall=True
        ) or ""
        text = text.strip()
        if not text:
            return _ok(False, None, "No se pudo extraer texto")
        return _ok(True, {"text": text[:max_chars]}, "")
    except Exception as e:
        return _ok(False, None, f"Error al extraer: {e}")

# Registrar herramientas nuevas
TOOLS["web_search"] = ("Busca en la web. Args: {'query':'...','k':5}", web_search)
TOOLS["read_url_clean"] = ("Lee y limpia texto de una URL. Args: {'url':'https://...','max_chars':4000}", read_url_clean)

