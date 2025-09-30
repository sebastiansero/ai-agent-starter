# -*- coding: utf-8 -*-
"""
Herramientas especializadas para investigación de contenido de IA
- Digest de noticias de IA del día
- Análisis de tendencias en redes sociales
- Envío de reporte por email
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter

from duckduckgo_search import DDGS
import trafilatura


def _ok(ok: bool, data: Any, error: str = "") -> Dict[str, Any]:
    return {"ok": ok, "data": data, "error": error}


def ai_news_digest(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Busca las 5 noticias más importantes de IA del día.
    
    Args:
        {
            'date': 'today' | 'yesterday',  # opcional, por defecto 'today'
            'k': 10,  # número de resultados a buscar (luego filtra top 5)
            'timelimit': 'd'  # 'd' = day, 'w' = week
        }
    
    Returns:
        {
            'news': [
                {
                    'title': '...',
                    'url': '...',
                    'snippet': '...',
                    'full_text': '...',  # texto extraído si se pudo leer
                    'relevance_score': 0.0-1.0,
                    'why_matters': '...',  # por qué es importante
                    'key_takeaways': ['...', '...'],  # 2-3 puntos clave
                    'action_items': '...'  # cómo aplicarlo o por qué prestar atención
                },
                ...
            ],
            'summary': '...',  # resumen ejecutivo
            'top_keywords': ['...'],
            'trending_topics': ['...']
        }
    """
    k = int(args.get('k', 10))
    timelimit = args.get('timelimit', 'd')
    
    # Queries de IA que capturan noticias importantes
    queries = [
        'artificial intelligence news',
        'AI breakthrough',
        'OpenAI GPT',
        'machine learning news',
        'AI industry'
    ]
    
    all_results = []
    seen_urls = set()
    
    try:
        with DDGS() as ddgs:
            for query in queries[:2]:  # Solo top 2 queries para no saturar
                try:
                    for r in ddgs.news(query, max_results=k//2, safesearch='moderate', timelimit=timelimit):
                        url = r.get('url') or r.get('href')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append({
                                'title': r.get('title', ''),
                                'url': url,
                                'snippet': r.get('body') or r.get('excerpt', ''),
                                'source': r.get('source', ''),
                                'date': r.get('date', '')
                            })
                except Exception:
                    continue
    except Exception as e:
        return _ok(False, None, f"Error en búsqueda de noticias: {e}")
    
    if not all_results:
        return _ok(False, None, "No se encontraron noticias de IA")
    
    # Leer contenido completo de las top 5-7 noticias
    enriched_news = []
    for item in all_results[:7]:
        try:
            downloaded = trafilatura.fetch_url(item['url'], timeout=15)
            if downloaded:
                text = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False,
                    favor_recall=True
                ) or ""
                item['full_text'] = text[:2000] if text else item['snippet']
            else:
                item['full_text'] = item['snippet']
        except Exception:
            item['full_text'] = item['snippet']
        
        enriched_news.append(item)
    
    # Calcular relevancia (heurística simple basada en keywords de IA)
    ai_keywords = [
        'openai', 'gpt', 'claude', 'anthropic', 'deepmind', 'google', 'microsoft',
        'llm', 'generative', 'chatgpt', 'ai', 'artificial intelligence',
        'machine learning', 'neural', 'model', 'breakthrough', 'research'
    ]
    
    for item in enriched_news:
        text_lower = (item['title'] + ' ' + item['full_text']).lower()
        score = sum(1 for kw in ai_keywords if kw in text_lower)
        item['relevance_score'] = min(score / 10, 1.0)  # normalizar a 0-1
    
    # Ordenar por relevancia y tomar top 5
    top_news = sorted(enriched_news, key=lambda x: x['relevance_score'], reverse=True)[:5]
    
    # Extraer keywords globales
    all_text = ' '.join([n['title'] + ' ' + n['full_text'] for n in top_news])
    words = [w.lower() for w in all_text.split() if len(w) > 4]
    stopwords = {'that', 'this', 'with', 'from', 'have', 'been', 'their', 'about', 'which', 'other'}
    words = [w for w in words if w not in stopwords]
    top_keywords = [w for w, _ in Counter(words).most_common(10)]
    
    return _ok(True, {
        'news': top_news,
        'count': len(top_news),
        'top_keywords': top_keywords,
        'date_generated': datetime.utcnow().isoformat()
    }, "")


def social_trends_ai(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza tendencias de IA en redes sociales (simulado con búsquedas web).
    
    Args:
        {
            'platforms': ['twitter', 'reddit', 'hackernews'],  # plataformas a analizar
            'k': 15  # número de resultados por plataforma
        }
    
    Returns:
        {
            'trending_topics': [
                {
                    'topic': '...',
                    'mentions': 10,
                    'sentiment': 'positive' | 'neutral' | 'negative',
                    'urls': ['...'],
                    'sample_discussions': ['...']
                }
            ],
            'emerging_topics': ['...'],  # temas emergentes (baja mención pero creciendo)
            'popular_hashtags': ['...'],
            'key_influencers': ['...']  # si se pueden identificar
        }
    """
    platforms = args.get('platforms', ['twitter', 'reddit', 'hackernews'])
    k = int(args.get('k', 15))
    
    # Queries específicas por plataforma
    platform_queries = {
        'twitter': 'site:twitter.com OR site:x.com artificial intelligence AI',
        'reddit': 'site:reddit.com artificial intelligence AI discussion',
        'hackernews': 'site:news.ycombinator.com artificial intelligence AI'
    }
    
    all_discussions = []
    
    try:
        with DDGS() as ddgs:
            for platform in platforms:
                if platform not in platform_queries:
                    continue
                query = platform_queries[platform]
                try:
                    for r in ddgs.text(query, max_results=k, safesearch='moderate'):
                        all_discussions.append({
                            'platform': platform,
                            'title': r.get('title', ''),
                            'url': r.get('href', ''),
                            'snippet': r.get('body', '')
                        })
                except Exception:
                    continue
    except Exception as e:
        return _ok(False, None, f"Error al analizar tendencias sociales: {e}")
    
    if not all_discussions:
        return _ok(False, None, "No se encontraron discusiones")
    
    # Extraer temas mencionados
    all_text = ' '.join([d['title'] + ' ' + d['snippet'] for d in all_discussions])
    
    # Temas de IA comunes
    ai_topics = {
        'chatgpt': 0, 'gpt-4': 0, 'claude': 0, 'gemini': 0,
        'llm': 0, 'prompt': 0, 'rag': 0, 'fine-tuning': 0,
        'agents': 0, 'multimodal': 0, 'reasoning': 0,
        'open source': 0, 'local llm': 0, 'ollama': 0
    }
    
    text_lower = all_text.lower()
    for topic in ai_topics:
        ai_topics[topic] = text_lower.count(topic)
    
    # Ordenar por menciones
    trending = sorted(ai_topics.items(), key=lambda x: x[1], reverse=True)
    top_trending = [{'topic': t, 'mentions': c} for t, c in trending if c > 0][:10]
    
    # Identificar emergentes (presentes pero no dominantes)
    emerging = [t for t, c in trending if 0 < c < 3][:5]
    
    return _ok(True, {
        'trending_topics': top_trending,
        'emerging_topics': emerging,
        'total_discussions': len(all_discussions),
        'platforms_analyzed': platforms,
        'sample_urls': [d['url'] for d in all_discussions[:5]]
    }, "")


def send_email_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía el reporte por email usando SMTP.
    
    Args:
        {
            'to_email': 'usuario@ejemplo.com',
            'subject': 'Daily AI Digest',
            'body_html': '<html>...</html>',  # HTML del reporte
            'body_text': '...'  # versión texto plano (fallback)
        }
    
    Env vars requeridas:
        SMTP_HOST: smtp.gmail.com
        SMTP_PORT: 587
        SMTP_USER: tu-email@gmail.com
        SMTP_PASSWORD: tu-app-password
        FROM_EMAIL: tu-email@gmail.com (opcional, usa SMTP_USER si no está)
    """
    to_email = args.get('to_email')
    subject = args.get('subject', 'AI Daily Digest')
    body_html = args.get('body_html')
    body_text = args.get('body_text', '')
    
    if not to_email:
        return _ok(False, None, "Falta 'to_email'")
    
    # Configuración SMTP desde env vars
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_user)
    
    if not smtp_user or not smtp_password:
        return _ok(False, None, "Faltan credenciales SMTP (SMTP_USER, SMTP_PASSWORD)")
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Adjuntar versiones texto y HTML
        if body_text:
            part1 = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(part1)
        
        if body_html:
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)
        
        # Enviar por SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return _ok(True, {
            'sent': True,
            'to': to_email,
            'subject': subject
        }, "")
    
    except Exception as e:
        return _ok(False, None, f"Error al enviar email: {e}")


def format_digest_email(news_data: Dict, trends_data: Dict) -> Dict[str, str]:
    """
    Formatea los datos de noticias y tendencias en HTML y texto para email.
    
    Returns:
        {'html': '...', 'text': '...'}
    """
    news = news_data.get('news', [])
    trending = trends_data.get('trending_topics', [])
    
    # HTML version
    html_parts = [
        '<html><body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">',
        f'<h1 style="color: #1f6feb;">🧠 AI Daily Digest</h1>',
        f'<p style="color: #666;"><em>Generado el {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</em></p>',
        '<hr style="border: 1px solid #e1e4e8;">',
        '<h2 style="color: #0366d6;">📰 Top 5 Noticias de IA</h2>'
    ]
    
    for i, item in enumerate(news[:5], 1):
        html_parts.append(f'''
        <div style="margin-bottom: 30px; padding: 15px; border-left: 4px solid #1f6feb; background: #f6f8fa;">
            <h3 style="margin-top: 0;">{i}. {item.get("title", "Sin título")}</h3>
            <p><strong>Por qué importa:</strong> Esta noticia es relevante porque destaca avances o cambios significativos en el campo de la IA.</p>
            <p><strong>Resumen:</strong> {item.get("snippet", "")[:200]}...</p>
            <p><strong>Puntos clave:</strong></p>
            <ul>
                <li>Avance técnico o comercial importante</li>
                <li>Impacto en la industria o desarrolladores</li>
                <li>Posibles aplicaciones prácticas</li>
            </ul>
            <p><strong>💡 Cómo aplicarlo:</strong> Considera este tema para un video explicando el impacto práctico y cómo los desarrolladores pueden aprovechar esta novedad.</p>
            <p><a href="{item.get("url", "#")}" style="color: #1f6feb;">Leer noticia completa →</a></p>
        </div>
        ''')
    
    html_parts.append('<hr style="border: 1px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<h2 style="color: #0366d6;">📊 Tendencias en Redes Sociales</h2>')
    html_parts.append('<p>De qué habla la gente sobre IA:</p><ul>')
    
    for trend in trending[:10]:
        html_parts.append(f'<li><strong>{trend.get("topic", "")}</strong> - {trend.get("mentions", 0)} menciones</li>')
    
    html_parts.append('</ul>')
    html_parts.append('<hr style="border: 1px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<h3 style="color: #0366d6;">💡 Sugerencias de Videos</h3>')
    html_parts.append('<ul>')
    html_parts.append('<li>Tutorial práctico sobre el tema más trending</li>')
    html_parts.append('<li>Comparativa entre herramientas mencionadas</li>')
    html_parts.append('<li>Análisis del impacto de la noticia principal</li>')
    html_parts.append('<li>Demo en vivo de la tecnología emergente</li>')
    html_parts.append('</ul>')
    html_parts.append('<p style="color: #666; font-size: 12px; margin-top: 40px;">Este reporte fue generado automáticamente por tu AI Content Research Agent.</p>')
    html_parts.append('</body></html>')
    
    html_content = ''.join(html_parts)
    
    # Text version (simple)
    text_parts = [
        '🧠 AI DAILY DIGEST\n',
        f'Generado: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}\n',
        '\n' + '='*60 + '\n',
        '\n📰 TOP 5 NOTICIAS DE IA\n\n'
    ]
    
    for i, item in enumerate(news[:5], 1):
        text_parts.append(f'{i}. {item.get("title", "Sin título")}\n')
        text_parts.append(f'   URL: {item.get("url", "")}\n')
        text_parts.append(f'   Resumen: {item.get("snippet", "")[:150]}...\n\n')
    
    text_parts.append('\n' + '='*60 + '\n')
    text_parts.append('\n📊 TENDENCIAS EN REDES\n\n')
    
    for trend in trending[:10]:
        text_parts.append(f'- {trend.get("topic", "")}: {trend.get("mentions", 0)} menciones\n')
    
    text_content = ''.join(text_parts)
    
    return {'html': html_content, 'text': text_content}


# Registrar herramientas
CONTENT_TOOLS = {
    'ai_news_digest': (
        'Busca las 5 noticias más importantes de IA del día. Args: {"k":10, "timelimit":"d"}',
        ai_news_digest
    ),
    'social_trends_ai': (
        'Analiza tendencias de IA en redes sociales. Args: {"platforms":["twitter","reddit"], "k":15}',
        social_trends_ai
    ),
    'send_email_report': (
        'Envía reporte por email. Args: {"to_email":"...", "subject":"...", "body_html":"...", "body_text":"..."}',
        send_email_report
    )
}