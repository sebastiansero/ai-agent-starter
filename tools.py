# -*- coding: utf-8 -*-
# Herramientas del agente y del servidor MCP
# - Memoria simple en proceso
# - RAG simple basado en JSONL + embeddings de OpenAI (opcional)

import os
import json
import math
from typing import Any, Dict, Tuple

import requests
import re
from collections import Counter
from urllib.parse import urlparse

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
from cache_manager import cacheable

# --- FASE 3: ADVANCED FEATURES ---

def generate_daily_digest_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera el digest diario de noticias de IA.
    Args: {'hours': 24, 'max_topics': 20, 'use_advanced': True}
    """
    try:
        from daily_digest_optimized import generate_daily_digest
        
        hours = int(args.get('hours', 24))
        max_topics = int(args.get('max_topics', 20))
        use_advanced = args.get('use_advanced', True)
        
        result = generate_daily_digest(
            hours_back=hours,
            max_topics=max_topics,
            use_batch=False,  # Sin batch para que sea rápido en chat
            use_advanced_features=use_advanced,
            save_to_file=False
        )
        
        # Retornar preview del digest
        digest_preview = result['digest'][:2000] + "..." if len(result['digest']) > 2000 else result['digest']
        
        return _ok(True, {
            'preview': digest_preview,
            'stats': result['stats'],
            'full_digest': result['digest']
        }, "")
        
    except Exception as e:
        return _ok(False, None, f"Error generando digest: {e}")

def analyze_topic_advanced(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un tema con las funciones avanzadas de Fase 3.
    Args: {'topic': 'GPT-5 Release', 'content': 'optional text', 'analyze_all': True}
    """
    try:
        from advanced_features import comprehensive_topic_analysis
        
        topic = args.get('topic')
        if not topic:
            return _ok(False, None, "Falta 'topic'")
        
        content = args.get('content', '')
        analyze_all = args.get('analyze_all', False)
        
        result = comprehensive_topic_analysis(
            topic=topic,
            content=content,
            novelty_score=0.9,
            analyze_all=analyze_all
        )
        
        # Formatear resultado para el chat
        summary = f"""## 🎯 Análisis de: {topic}

**Score:** {result['score']['final_score']:.1f}/100
**Prioridad:** {result['score']['priority'].upper()}
**Recomendación:** {result['score']['recommendation']}
"""
        
        if result.get('titles') and result['titles']['titles']:
            summary += "\n**Mejores Títulos:**\n"
            for i, t in enumerate(result['titles']['titles'][:3], 1):
                summary += f"{i}. \"{t['title']}\" (viral: {t['viral_potential']}/10)\n"
        
        return _ok(True, {
            'summary': summary,
            'full_result': result
        }, "")
        
    except Exception as e:
        return _ok(False, None, f"Error analizando tema: {e}")

def generate_video_titles_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera títulos virales para un tema.
    Args: {'topic': 'AI Model Release'}
    """
    try:
        from advanced_features import generate_video_titles
        
        topic = args.get('topic')
        if not topic:
            return _ok(False, None, "Falta 'topic'")
        
        result = generate_video_titles(topic)
        
        # Formatear títulos
        titles_text = f"## ✏️ Títulos para: {topic}\n\n"
        for i, t in enumerate(result['titles'], 1):
            titles_text += f"{i}. **\"{t['title']}\"**\n"
            titles_text += f"   - Viral: {t['viral_potential']}/10\n"
            titles_text += f"   - Hook: {t['hook']}\n\n"
        
        if result.get('thumbnail_ideas'):
            titles_text += "**💡 Ideas de Thumbnail:**\n"
            for i, idea in enumerate(result['thumbnail_ideas'], 1):
                titles_text += f"{i}. {idea}\n"
        
        return _ok(True, {
            'formatted': titles_text,
            'titles': result['titles'],
            'thumbnails': result.get('thumbnail_ideas', [])
        }, "")
        
    except Exception as e:
        return _ok(False, None, f"Error generando títulos: {e}")

def analyze_hype_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza si un tema es hype o sustancia.
    Args: {'title': '...', 'content': '...'}
    """
    try:
        from advanced_features import analyze_hype_vs_substance
        
        title = args.get('title', '')
        content = args.get('content', '')
        
        if not title and not content:
            return _ok(False, None, "Falta 'title' o 'content'")
        
        result = analyze_hype_vs_substance(title, content)
        
        # Formatear resultado
        analysis = f"""## 🎭 Análisis de Hype

**Veredicto:** {result['verdict'].upper()}
**Sustancia:** {result['substance_score']:.1f}/10
**Hype:** {result['hype_score']:.1f}/10

**Razonamiento:** {result['reasoning']}
"""
        
        if result.get('green_flags'):
            analysis += "\n✅ **Green Flags:**\n"
            for flag in result['green_flags']:
                analysis += f"- {flag}\n"
        
        if result.get('red_flags'):
            analysis += "\n🚩 **Red Flags:**\n"
            for flag in result['red_flags']:
                analysis += f"- {flag}\n"
        
        return _ok(True, {
            'formatted': analysis,
            'verdict': result['verdict'],
            'substance_score': result['substance_score'],
            'hype_score': result['hype_score']
        }, "")
        
    except Exception as e:
        return _ok(False, None, f"Error analizando hype: {e}")

def _web_search_internal(q: str, k: int):
    """Helper interno cacheado para web_search"""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=k, safesearch="moderate"):
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "snippet": r.get("body")
            })
    return results

@cacheable(max_age_hours=2)  # Noticias: cache corto (2 horas)
def _cached_web_search(query: str, k: int):
    return _web_search_internal(query, k)

def web_search(args):
    """
    Busca en la web usando DuckDuckGo (con cache de 2 horas).
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
        results = _cached_web_search(q, k)
        return _ok(True, {"results": results}, "")
    except Exception as e:
        return _ok(False, None, f"Error en búsqueda: {e}")

@cacheable(max_age_hours=24)  # Artículos: cache largo (24 horas)
def _cached_read_url(url: str, max_chars: int):
    downloaded = trafilatura.fetch_url(url, timeout=25)
    if not downloaded:
        raise ValueError("No se pudo descargar la URL")
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        favor_recall=True
    ) or ""
    text = text.strip()
    if not text:
        raise ValueError("No se pudo extraer texto")
    return text[:max_chars]

def read_url_clean(args):
    """
    Descarga una URL y extrae el contenido principal (texto) con trafilatura (con cache de 24 horas).
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
        text = _cached_read_url(url, max_chars)
        return _ok(True, {"text": text}, "")
    except Exception as e:
        return _ok(False, None, f"Error al extraer: {e}")

# --- Escaneo de tendencias web (búsqueda + lectura + señales) ---

_ES_STOPWORDS = set(
    "a al algo algunas algunos ante antes como con contra cual cuales cuando de del desde donde dos el la las los en entre era erais eramos eran es esa esas ese esos esta estaba estabais estabamos estaban estuve estuviera estuviese esto estos estoy etc fue fui ha habeis habiamos habian hablar habia han hasta hay la lo mas me mi mis mucho muy nada ni no nos nosotras nosotros o os otra otro para pero poco por porque que quien quienes se ser si sino sobre solo somos son soy su sus tambien te tiene tienen todo todos tras tu tus un una uno y ya".split()
)


def _tokenize_es(text: str):
    text = text.lower()
    tokens = re.findall(r"[a-záéíóúñü]{3,}", text)
    return [t for t in tokens if t not in _ES_STOPWORDS]


def _top_keywords_es(texts, topn=12):
    c = Counter()
    for t in texts:
        for tok in _tokenize_es(t or ""):
            c[tok] += 1
    return [{"term": w, "count": n} for w, n in c.most_common(topn)]


def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc or ""
    except Exception:
        return ""


def web_trend_scan(args):
    """
    Escanea tendencias web sobre un tema dado.
    Args:
      {'topic':'...', 'k': 10, 'max_articles': 5, 'timelimit': 'w', 'max_chars': 4000}
    Devuelve:
      {
        'results': [{'title','url','snippet'}...],
        'articles': [{'title','url','snippet','text'}...],
        'keywords': [{'term','count'}...],
        'top_domains': [{'domain','count'}...]
      }
    """
    from duckduckgo_search import DDGS  # import local para evitar fallos si no instalado
    import trafilatura

    topic = args.get("topic") or args.get("query") or args.get("q")
    k = int(args.get("k", 10))
    max_articles = int(args.get("max_articles", 5))
    timelimit = args.get("timelimit", "w")  # d,w,m
    max_chars = int(args.get("max_chars", 4000))

    if not topic:
        return _ok(False, None, "Falta 'topic'")

    results = []
    try:
        with DDGS() as ddgs:
            # Intentar canal de noticias primero
            try:
                for r in ddgs.news(topic, max_results=k, safesearch="moderate", timelimit=timelimit):
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("url") or r.get("href"),
                        "snippet": r.get("body") or r.get("excerpt") or ""
                    })
            except Exception:
                pass
            # Fallback a búsqueda general si no hay noticias
            if not results:
                for r in ddgs.text(topic, max_results=k, safesearch="moderate"):
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body") or ""
                    })
    except Exception as e:
        return _ok(False, None, f"Error en búsqueda: {e}")

    # Unificar y filtrar URLs válidas
    urls_seen = set()
    clean_results = []
    for r in results:
        u = r.get("url")
        if not u or u in urls_seen:
            continue
        urls_seen.add(u)
        clean_results.append(r)

    # Leer artículos (máximo max_articles)
    articles = []
    texts = []
    for r in clean_results[:max_articles]:
        u = r["url"]
        try:
            downloaded = trafilatura.fetch_url(u, timeout=25)
            if not downloaded:
                continue
            txt = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_recall=True
            ) or ""
            txt = (txt or "").strip()
            if not txt:
                continue
            txt = txt[:max_chars]
            texts.append(txt)
            snippet = (txt[:220] + "...") if len(txt) > 220 else txt
            articles.append({
                "title": r.get("title"),
                "url": u,
                "snippet": snippet,
                "text": txt
            })
        except Exception:
            continue

    # Señales: keywords y dominios
    keywords = _top_keywords_es(texts, topn=12)
    dom_counter = Counter(_domain(r.get("url") or "") for r in clean_results)
    if "" in dom_counter:
        del dom_counter[""]
    top_domains = [{"domain": d, "count": n} for d, n in dom_counter.most_common(10)]

    data = {
        "results": clean_results,
        "articles": articles,
        "keywords": keywords,
        "top_domains": top_domains,
    }
    return _ok(True, data, "")

# Registrar herramientas nuevas
TOOLS["web_search"] = ("Busca en la web. Args: {'query':'...','k':5}", web_search)
TOOLS["read_url_clean"] = ("Lee y limpia texto de una URL. Args: {'url':'https://...','max_chars':4000}", read_url_clean)
TOOLS["web_trend_scan"] = ("Escanea tendencias web de un tema. Args: {'topic':'...','k':10,'max_articles':5,'timelimit':'w','max_chars':4000}", web_trend_scan)

# Fase 3: Advanced Features
TOOLS["daily_digest"] = ("Genera digest diario de noticias IA. Args: {'hours':24,'max_topics':20,'use_advanced':True}", generate_daily_digest_tool)
TOOLS["analyze_topic"] = ("Analiza un tema con scoring avanzado. Args: {'topic':'...','content':'','analyze_all':False}", analyze_topic_advanced)
TOOLS["generate_titles"] = ("Genera títulos virales para un tema. Args: {'topic':'...'}", generate_video_titles_tool)
TOOLS["analyze_hype"] = ("Analiza si un tema es hype o sustancia. Args: {'title':'...','content':'...'}", analyze_hype_tool)

