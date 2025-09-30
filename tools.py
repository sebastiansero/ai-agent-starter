# -*- coding: utf-8 -*-
# Herramientas del agente y del servidor MCP
# - Memoria simple en proceso
# - RAG simple basado en JSONL + embeddings de OpenAI (opcional)

import os
import json
import math
from typing import Any, Dict, Tuple
from datetime import datetime

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
        from ai_content_research import fetch_all_rss_feeds, search_ai_news_advanced
        
        hours = int(args.get('hours', 24))
        max_topics = int(args.get('max_topics', 15))  # Reducido para más detalle
        
        # Obtener contenido con contexto
        print(f"🔍 Buscando noticias de las últimas {hours} horas...")
        print("   • RSS feeds (Substacks, Tech Media, Research, Company Blogs)...")
        rss_data = fetch_all_rss_feeds(
            hours=hours, 
            categories=['substacks', 'tech_media', 'research', 'company_blogs', 'communities']
        )
        print(f"   ✓ {len(rss_data['all_posts'])} posts encontrados en RSS")
        
        print("   • Búsqueda web avanzada...")
        web_articles = search_ai_news_advanced(hours=hours, k=10)
        print(f"   ✓ {len(web_articles)} artículos web encontrados")
        
        # Combinar y formatear elegantemente
        all_content = []
        
        # Priorizar contenido por fuente
        # 1. Substacks (alta prioridad - contenido curado)
        substacks = [p for p in rss_data['all_posts'] if p.get('category') == 'substacks']
        for post in substacks[:6]:  # Top 6 de Substacks
            all_content.append({
                'title': post.get('title', ''),
                'summary': post.get('summary', '')[:300],
                'source': f"📝 {post.get('source_name', 'Substack')}",
                'url': post.get('link', ''),
                'priority': 'high'
            })
        
        # 2. Otros RSS (company blogs, tech media)
        other_rss = [p for p in rss_data['all_posts'] if p.get('category') != 'substacks']
        for post in other_rss[:6]:  # Top 6 de otros RSS
            all_content.append({
                'title': post.get('title', ''),
                'summary': post.get('summary', '')[:300],
                'source': f"📰 {post.get('source_name', 'RSS')}",
                'url': post.get('link', ''),
                'priority': 'medium'
            })
        
        # 3. Web search (complementario)
        for article in web_articles[:3]:  # Solo top 3 de web
            all_content.append({
                'title': article.get('title', ''),
                'summary': article.get('snippet', article.get('full_text', ''))[:300],
                'source': '🌐 Web',
                'url': article.get('url', ''),
                'priority': 'low'
            })
        
        # Formatear elegantemente
        output = "🤖 Digest Diario de IA\n"
        output += "═" * 60 + "\n\n"
        output += f"📊 Análisis de las últimas {hours} horas\n"
        output += f"📰 {len(all_content)} noticias encontradas\n"
        
        # Mostrar breakdown de fuentes
        substack_count = len([c for c in all_content if 'Substack' in c.get('source', '') or '📝' in c.get('source', '')])
        rss_count = len([c for c in all_content if '📰' in c.get('source', '')])
        web_count = len([c for c in all_content if '🌐' in c.get('source', '')])
        
        output += f"   📝 Substacks: {substack_count} | 📰 Tech Media: {rss_count} | 🌐 Web: {web_count}\n"
        output += f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        output += "─" * 60 + "\n\n"
        
        for i, item in enumerate(all_content[:max_topics], 1):
            # Emoji según el índice
            emoji = "🔥" if i <= 3 else "✨" if i <= 7 else "📌"
            
            output += f"{emoji} {i}. {item['title']}\n\n"
            
            # Agregar contexto/resumen
            if item['summary']:
                summary_clean = item['summary'].replace('\n', ' ').strip()
                if len(summary_clean) > 250:
                    summary_clean = summary_clean[:247] + "..."
                output += f"   {summary_clean}\n\n"
            
            # Fuente y URL
            output += f"   📍 Fuente: {item['source']}\n"
            if item['url']:
                # Mostrar dominio en lugar de URL completa
                from urllib.parse import urlparse
                domain = urlparse(item['url']).netloc or item['url']
                output += f"   🔗 {domain}\n"
            
            output += "\n" + "─" * 60 + "\n\n"
        
        output += "\n💡 Tip: Usa 'analiza el tema [título]' para análisis profundo de cualquier noticia\n"
        
        return _ok(True, {
            'formatted_digest': output,
            'count': len(all_content)
        }, "")
        
    except Exception as e:
        import traceback
        return _ok(False, None, f"Error generando digest: {e}\n{traceback.format_exc()[:500]}")

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
        analyze_all = args.get('analyze_all', True)  # Cambiar a True por defecto para análisis completo
        
        # Si no hay contenido, buscar en web para tener contexto
        if not content:
            print(f"🔍 Buscando información sobre: {topic}")
            try:
                # Buscar contenido relacionado
                search_result = web_search({'query': topic, 'k': 3})
                if search_result.get('ok') and search_result.get('data', {}).get('results'):
                    results = search_result['data']['results']
                    # Obtener snippet del primer resultado
                    if results:
                        first_url = results[0].get('url')
                        if first_url:
                            url_content = read_url_clean({'url': first_url, 'max_chars': 2000})
                            if url_content.get('ok'):
                                content = url_content.get('data', {}).get('text', '')
                        
                        # Si no hay contenido de URL, usar snippets
                        if not content:
                            content = ' '.join(r.get('snippet', '') for r in results[:2])[:1500]
            except Exception as e:
                print(f"⚠️ No se pudo buscar contenido: {e}")
                content = topic  # Fallback al tema
        
        # Calcular novelty score basado en keywords comunes vs únicos
        novelty_score = 0.85  # Default alto pero no máximo
        
        # Ajustar novelty según keywords en el título
        title_lower = topic.lower()
        
        # Temas muy comunes/saturados
        if any(kw in title_lower for kw in ['chatgpt', 'tutorial', 'beginner', 'guide', 'how to']):
            novelty_score = 0.4
        # Temas medianamente comunes
        elif any(kw in title_lower for kw in ['ai', 'gpt', 'llm', 'openai', 'google']):
            novelty_score = 0.65
        # Temas con releases/anuncios importantes
        elif any(kw in title_lower for kw in ['release', 'launch', 'announce', 'breakthrough', 'new model']):
            novelty_score = 0.9
        # Temas muy específicos/técnicos
        elif any(kw in title_lower for kw in ['benchmark', 'architecture', 'research', 'paper', 'study']):
            novelty_score = 0.85
        
        result = comprehensive_topic_analysis(
            topic=topic,
            content=content,
            novelty_score=novelty_score,
            analyze_all=analyze_all
        )
        
        # Formatear elegantemente sin markdown
        priority_emoji = {'🔥': 'high', '👍': 'medium', '⏸️': 'low'}
        priority = result['score']['priority']
        emoji = '🔥' if priority == 'high' else '👍' if priority == 'medium' else '⏸️'
        
        output = f"🎯 Análisis Completo: {topic}\n"
        output += "═" * 60 + "\n\n"
        
        # Score y prioridad
        output += f"📊 Score General: {result['score']['final_score']:.1f}/100\n"
        output += f"{emoji} Prioridad: {priority.upper()}\n\n"
        
        # Breakdown de scores
        breakdown = result['score']['breakdown']
        output += "📊 Desglose de Factores:\n"
        output += f"   • Novedad: {breakdown['novelty']:.1f}/10\n"
        output += f"   • Sustancia: {breakdown['substance']:.1f}/10\n"
        output += f"   • Oportunidad: {breakdown['opportunity']:.1f}/10\n"
        output += f"   • Timing: {breakdown['timing']:.1f}/10\n\n"
        
        # Recomendación
        output += f"💡 Recomendación: {result['score']['recommendation']}\n\n"
        output += "─" * 60 + "\n\n"
        
        # Títulos sugeridos
        if result.get('titles') and result['titles']['titles']:
            output += "✏️ Títulos Sugeridos para Video:\n\n"
            for i, t in enumerate(result['titles']['titles'][:3], 1):
                output += f"{i}. {t['title']}\n"
                output += f"   ⭐ Potencial Viral: {t['viral_potential']}/10\n"
                output += f"   🎯 Hook: {t['hook']}\n\n"
        
        return _ok(True, {
            'formatted_analysis': output,
            'score': result['score']['final_score'],
            'priority': priority
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
        
        # Formatear elegantemente sin markdown
        output = f"✏️ Títulos Virales para: {topic}\n"
        output += "═" * 60 + "\n\n"
        
        for i, t in enumerate(result['titles'], 1):
            # Emoji según potencial viral
            viral = t['viral_potential']
            emoji = "🔥" if viral >= 8 else "✨" if viral >= 6 else "📌"
            
            output += f"{emoji} {i}. {t['title']}\n\n"
            output += f"   ⭐ Potencial Viral: {viral}/10\n"
            output += f"   🎯 Hook: {t['hook']}\n"
            output += f"   🧠 Por qué funciona: {t['reasoning'][:150]}...\n\n"
            output += "─" * 60 + "\n\n"
        
        if result.get('thumbnail_ideas'):
            output += "🎨 Ideas para Thumbnail:\n\n"
            for i, idea in enumerate(result['thumbnail_ideas'], 1):
                output += f"  {i}. {idea}\n"
        
        return _ok(True, {
            'formatted_titles': output,
            'count': len(result['titles'])
        }, "")
        
    except Exception as e:
        return _ok(False, None, f"Error generando títulos: {e}")

def deep_analysis_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análisis profundo de una noticia con estructura completa:
    - Resumen (500 palabras)
    - Por qué importa
    - Cómo aplicarlo
    - Calificaciones
    Args: {'topic': '...'}
    """
    try:
        from advanced_features import analyze_hype_vs_substance, generate_video_titles, calculate_content_score
        
        topic = args.get('topic')
        if not topic:
            return _ok(False, None, "Falta 'topic'")
        
        print(f"🔍 Realizando análisis profundo de: {topic}")
        
        # 1. Buscar contenido completo
        print("   • Buscando información...")
        search_result = web_search({'query': topic, 'k': 5})
        
        content = ""
        url = ""
        if search_result.get('ok') and search_result.get('data', {}).get('results'):
            results = search_result['data']['results']
            if results:
                url = results[0].get('url', '')
                # Obtener contenido completo
                url_content = read_url_clean({'url': url, 'max_chars': 4000})
                if url_content.get('ok'):
                    content = url_content.get('data', {}).get('text', '')
                
                # Si no hay contenido, usar snippets
                if not content:
                    content = ' '.join(r.get('snippet', '') for r in results[:3])
        
        if not content:
            content = topic
        
        print("   ✓ Información recopilada")
        
        # 2. Generar análisis con LLM
        print("   • Generando análisis profundo...")
        
        from openai import OpenAI
        client = OpenAI()
        
        prompt = f"""Analiza profundamente esta noticia de IA:

Título: {topic}

Contenido: {content[:3000]}

Genera un análisis estructurado siguiendo este formato EXACTO:

1. RESUMEN (400-500 palabras)
   - ¿Qué es esto exactamente?
   - ¿Qué hace diferente o especial?
   - Detalles técnicos clave
   - Contexto de la industria

2. POR QUÉ IMPORTA
   - Impacto en la industria
   - Implicaciones para desarrolladores/usuarios
   - Cambios que trae al mercado

3. CÓMO APLICARLO
   - Pasos prácticos concretos
   - Casos de uso específicos
   - Cómo empezar hoy mismo

4. CALIFICACIONES
   - Novedad: X/10
   - Impacto: X/10
   - Aplicabilidad: X/10
   - Prioridad: ALTA/MEDIA/BAJA

Se claro, práctico y accionable. Evita fluff."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista experto de IA que genera reportes profundos, prácticos y accionables. Sigues estructuras exactas y das información concreta."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1500
        )
        
        analysis = response.choices[0].message.content
        print("   ✓ Análisis completado")
        
        # 3. Formatear elegantemente
        output = "📊 ANÁLISIS PROFUNDO\n"
        output += "═" * 70 + "\n\n"
        output += f"🎯 Tema: {topic}\n\n"
        
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            output += f"🔗 Fuente: {domain}\n\n"
        
        output += "─" * 70 + "\n\n"
        output += analysis
        output += "\n\n" + "─" * 70 + "\n\n"
        output += "💡 Tip: Usa 'genera títulos para [tema]' para ideas de contenido\n"
        
        return _ok(True, {
            'formatted_deep_analysis': output,
            'raw_analysis': analysis
        }, "")
        
    except Exception as e:
        import traceback
        return _ok(False, None, f"Error en análisis profundo: {e}\n{traceback.format_exc()[:500]}")

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
        
        # Formatear elegantemente sin markdown
        verdict = result['verdict'].upper()
        verdict_emoji = "✅" if verdict == "SUBSTANCE" else "⚠️" if verdict == "MIXED" else "🚨"
        
        output = f"🎭 Análisis de Hype vs Sustancia\n"
        output += "═" * 60 + "\n\n"
        
        output += f"{verdict_emoji} Veredicto: {verdict}\n\n"
        output += f"📊 Scores:\n"
        output += f"   • Sustancia: {result['substance_score']:.1f}/10\n"
        output += f"   • Hype: {result['hype_score']:.1f}/10\n\n"
        
        output += f"🧠 Razonamiento:\n   {result['reasoning']}\n\n"
        output += "─" * 60 + "\n\n"
        
        if result.get('green_flags'):
            output += "✅ Señales Positivas:\n"
            for flag in result['green_flags']:
                output += f"   • {flag}\n"
            output += "\n"
        
        if result.get('red_flags'):
            output += "🚩 Señales de Alerta:\n"
            for flag in result['red_flags']:
                output += f"   • {flag}\n"
        
        return _ok(True, {
            'formatted_hype_analysis': output,
            'verdict': verdict
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
TOOLS["deep_analysis"] = ("Análisis profundo de noticia: resumen 500 palabras + por qué importa + cómo aplicarlo + calificaciones. Args: {'topic':'...'}", deep_analysis_tool)

