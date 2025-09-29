# -*- coding: utf-8 -*-
"""
Sistema completo de investigación de contenido de IA
- Noticias con búsquedas avanzadas
- RSS feeds (Substacks, HN, Reddit, GitHub, arXiv)
- Análisis de tendencias
- Generación de ideas de videos
- Envío por email
"""

import os
import json
import smtplib
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List
from collections import Counter

from duckduckgo_search import DDGS
import trafilatura
import feedparser


def _ok(ok: bool, data: Any, error: str = "") -> Dict[str, Any]:
    return {"ok": ok, "data": data, "error": error}


# 📰 RSS FEEDS DE IA - Fuentes completas
RSS_SOURCES = {
    # Substacks de expertos
    'substacks': [
        {'name': 'Import AI', 'author': 'Jack Clark', 'rss': 'https://jack-clark.net/feed/'},
        {'name': 'The Batch', 'author': 'Andrew Ng', 'rss': 'https://www.deeplearning.ai/the-batch/feed/'},
        {'name': 'One Useful Thing', 'author': 'Ethan Mollick', 'rss': 'https://www.oneusefulthing.org/feed'},
        {'name': 'Nate B Jones', 'rss': 'https://natebjonesdotcom.substack.com/feed'},
        {'name': 'Sabrina Ramonov', 'rss': 'https://www.sabrina.dev/feed'},
        {'name': 'Latent Space', 'author': 'swyx', 'rss': 'https://www.latent.space/feed'},
        {'name': 'Simon Willison', 'rss': 'https://simonwillison.net/atom/everything/'},
        {'name': "Ben's Bites", 'rss': 'https://bensbites.beehiiv.com/feed'},
        {'name': 'Last Week in AI', 'rss': 'https://lastweekin.ai/feed'},
    ],
    
    # Blogs de empresas
    'company_blogs': [
        {'name': 'OpenAI Blog', 'rss': 'https://openai.com/blog/rss.xml'},
        {'name': 'Anthropic', 'rss': 'https://www.anthropic.com/news/rss.xml'},
        {'name': 'Google AI Blog', 'rss': 'https://blog.google/technology/ai/rss/'},
        {'name': 'Microsoft AI', 'rss': 'https://blogs.microsoft.com/ai/feed/'},
    ],
    
    # Comunidades tech
    'communities': [
        {'name': 'Hacker News AI', 'rss': 'https://hnrss.org/newest?q=AI+OR+GPT+OR+LLM'},
        {'name': 'Reddit r/MachineLearning', 'rss': 'https://www.reddit.com/r/MachineLearning/.rss'},
        {'name': 'Reddit r/artificial', 'rss': 'https://www.reddit.com/r/artificial/.rss'},
        {'name': 'Reddit r/LocalLLaMA', 'rss': 'https://www.reddit.com/r/LocalLLaMA/.rss'},
    ],
    
    # Research
    'research': [
        {'name': 'arXiv AI', 'rss': 'https://arxiv.org/rss/cs.AI'},
        {'name': 'arXiv ML', 'rss': 'https://arxiv.org/rss/cs.LG'},
        {'name': 'arXiv CL', 'rss': 'https://arxiv.org/rss/cs.CL'},
    ],
    
    # Medios tech
    'tech_media': [
        {'name': 'VentureBeat AI', 'rss': 'https://venturebeat.com/category/ai/feed/'},
        {'name': 'TechCrunch AI', 'rss': 'https://techcrunch.com/category/artificial-intelligence/feed/'},
        {'name': 'The Verge AI', 'rss': 'https://www.theverge.com/ai-artificial-intelligence/rss/index.xml'},
    ],
    
    # GitHub Trending (via servicio externo)
    'github': [
        {'name': 'GitHub Trending Python', 'rss': 'https://mshibanami.github.io/GitHubTrendingRSS/daily/python.xml'},
        {'name': 'GitHub Trending Jupyter', 'rss': 'https://mshibanami.github.io/GitHubTrendingRSS/daily/jupyter-notebook.xml'},
    ]
}


def fetch_all_rss_feeds(hours=48, categories=None):
    """
    Obtiene posts de todos los RSS feeds
    
    Args:
        hours: Filtrar últimas N horas
        categories: ['substacks', 'communities', ...] o None para todas
    
    Returns:
        {
            'all_posts': [...],
            'by_category': {'substacks': [...], ...},
            'stats': {...}
        }
    """
    if categories is None:
        categories = list(RSS_SOURCES.keys())
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    all_posts = []
    by_category = {cat: [] for cat in categories}
    stats = {'total': 0, 'by_source': {}, 'errors': []}
    
    for category in categories:
        if category not in RSS_SOURCES:
            continue
            
        for source in RSS_SOURCES[category]:
            try:
                feed = feedparser.parse(source['rss'])
                source_name = source.get('name', source['rss'])
                
                for entry in feed.entries[:10]:  # Max 10 por feed
                    # Parse fecha
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6])
                    else:
                        pub_date = datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    # Extraer contenido
                    summary = entry.get('summary', entry.get('description', ''))
                    if '<' in summary:
                        from bs4 import BeautifulSoup
                        summary = BeautifulSoup(summary, 'html.parser').get_text()
                    
                    post = {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': summary[:300],
                        'published': pub_date.isoformat(),
                        'source_name': source_name,
                        'author': source.get('author', ''),
                        'category': category
                    }
                    
                    all_posts.append(post)
                    by_category[category].append(post)
                    stats['total'] += 1
                
                stats['by_source'][source_name] = len(by_category[category])
                time.sleep(0.1)  # Rate limiting cortés
                
            except Exception as e:
                stats['errors'].append({'source': source.get('name', '?'), 'error': str(e)})
                continue
    
    # Ordenar por fecha
    all_posts.sort(key=lambda x: x['published'], reverse=True)
    
    return {
        'all_posts': all_posts,
        'by_category': by_category,
        'stats': stats
    }


def search_ai_news_advanced(hours=24, k=15):
    """
    Búsqueda avanzada de noticias de IA con queries optimizados
    
    Returns:
        [
            {
                'title': '...',
                'url': '...',
                'snippet': '...',
                'full_text': '...',
                'relevance_score': 0.0-1.0,
                'source': 'DDG News'
            },
            ...
        ]
    """
    # Queries avanzados por categoría
    query_sets = {
        'breakthrough': [
            'AI breakthrough OR "artificial intelligence breakthrough"',
            '"GPT-5" OR "GPT-4o" OR "Claude 4" OR "Gemini Pro" OR "new AI model"',
        ],
        'companies': [
            '(OpenAI OR Anthropic OR "Google DeepMind") (announcement OR launch)',
            '"AI startup" (funding OR "series A")',
        ],
        'applications': [
            '"AI agents" OR "autonomous agents"',
            '"generative AI" (enterprise OR productivity)',
        ],
        'technology': [
            '"RAG" OR "retrieval augmented generation"',
            '"multimodal AI" OR "vision language model"',
        ],
    }
    
    all_results = []
    seen_urls = set()
    
    # Seleccionar top 2 queries por categoría
    selected_queries = []
    for cat, qs in query_sets.items():
        selected_queries.extend(qs[:1])
    
    try:
        with DDGS() as ddgs:
            for query in selected_queries:
                try:
                    for r in ddgs.news(query, max_results=k//len(selected_queries), safesearch='moderate', timelimit='d'):
                        url = r.get('url') or r.get('href')
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            
                            # Intentar leer contenido completo
                            full_text = ''
                            try:
                                downloaded = trafilatura.fetch_url(url, timeout=10)
                                if downloaded:
                                    full_text = trafilatura.extract(
                                        downloaded,
                                        include_comments=False,
                                        include_tables=False
                                    ) or ''
                            except:
                                pass
                            
                            all_results.append({
                                'title': r.get('title', ''),
                                'url': url,
                                'snippet': r.get('body', '')[:300],
                                'full_text': full_text[:2000] if full_text else r.get('body', ''),
                                'source': 'DDG News',
                                'date': r.get('date', '')
                            })
                    
                    time.sleep(0.5)  # Rate limiting
                except Exception:
                    continue
    except Exception as e:
        return []
    
    # Calcular relevancia con scoring ponderado
    tier1 = {'gpt-5', 'claude 4', 'breakthrough', 'agi', 'open source'}
    tier2 = {'openai', 'anthropic', 'deepmind', 'launch', 'funding', 'gpt-4'}
    tier3 = {'ai', 'llm', 'generative', 'machine learning', 'chatgpt'}
    
    for item in all_results:
        text_lower = (item['title'] + ' ' + item['full_text']).lower()
        title_lower = item['title'].lower()
        
        score = 0
        for kw in tier1:
            if kw in text_lower:
                score += 3
                if kw in title_lower:
                    score += 2
        for kw in tier2:
            if kw in text_lower:
                score += 2
                if kw in title_lower:
                    score += 1
        for kw in tier3:
            if kw in text_lower:
                score += 1
        
        item['relevance_score'] = min(score / 30, 1.0)
    
    # Ordenar por relevancia
    all_results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return all_results[:10]  # Top 10


def analyze_trends(rss_posts, news_articles):
    """
    Analiza tendencias combinando RSS feeds y noticias
    
    Returns:
        {
            'trending_topics': [{topic, mentions, sources}, ...],
            'hot_companies': [...],
            'hot_models': [...],
            'research_areas': [...],
            'tools_mentioned': [...],
            'emerging_topics': [...]
        }
    """
    # Combinar todo el texto
    all_text = ""
    for post in rss_posts:
        all_text += " " + post['title'] + " " + post.get('summary', '')
    for article in news_articles:
        all_text += " " + article['title'] + " " + article.get('full_text', '')
    
    text_lower = all_text.lower()
    
    # Detectar entidades
    companies = re.findall(
        r'\b(OpenAI|Anthropic|Google|Microsoft|Meta|DeepMind|Mistral|Cohere|'
        r'Hugging\s*Face|Stability\s*AI|Midjourney|Perplexity)\b',
        all_text, re.IGNORECASE
    )
    
    models = re.findall(
        r'\b(GPT-[0-9o]+|Claude\s*[0-9.]*|Gemini|LLaMA|Llama|Mistral|'
        r'DALL-E|Stable\s*Diffusion|Midjourney)\b',
        all_text, re.IGNORECASE
    )
    
    research_terms = re.findall(
        r'\b(RAG|fine-tuning|RLHF|prompt\s*engineering|multimodal|'
        r'alignment|reasoning|agents?|transformers?|embeddings?)\b',
        all_text, re.IGNORECASE
    )
    
    tools = re.findall(
        r'\b(LangChain|LlamaIndex|Ollama|AutoGPT|Cursor|Copilot|'
        r'Pinecone|Weaviate|Chroma|FAISS)\b',
        all_text, re.IGNORECASE
    )
    
    # Contar menciones
    company_counts = Counter([c.lower() for c in companies])
    model_counts = Counter([m.lower() for m in models])
    research_counts = Counter([r.lower() for r in research_terms])
    tool_counts = Counter([t.lower() for t in tools])
    
    return {
        'hot_companies': [
            {'name': c[0].title(), 'mentions': c[1]} 
            for c in company_counts.most_common(8)
        ],
        'hot_models': [
            {'name': m[0].title(), 'mentions': m[1]}
            for m in model_counts.most_common(8)
        ],
        'research_areas': [
            {'topic': r[0].upper(), 'mentions': r[1]}
            for r in research_counts.most_common(10)
        ],
        'tools_mentioned': [
            {'tool': t[0].title(), 'mentions': t[1]}
            for t in tool_counts.most_common(8)
        ],
        'emerging_topics': [
            t[0] for t in research_counts.most_common(15)
            if t[1] >= 2 and t[1] <= 5  # Mencionados pero no saturados
        ][:5]
    }


def generate_video_ideas(trends, top_posts, top_news):
    """
    Genera 5-7 ideas de videos basadas en el análisis
    
    Returns:
        [
            {
                'title': '...',
                'reason': '...',
                'difficulty': 'beginner|intermediate|advanced',
                'format': '...',
                'angle': '...',
                'sources': [...]
            },
            ...
        ]
    """
    ideas = []
    
    # Idea 1: Noticia principal
    if top_news:
        main_news = top_news[0]
        ideas.append({
            'title': f"🔥 {main_news['title'][:60]}...",
            'reason': f"Noticia más relevante del día (score: {main_news['relevance_score']:.2f})",
            'difficulty': 'beginner',
            'format': 'news + analysis',
            'angle': 'Explica qué significa para developers y usuarios',
            'sources': [main_news['url']]
        })
    
    # Idea 2: Modelo/herramienta trending
    if trends['hot_models']:
        model = trends['hot_models'][0]
        ideas.append({
            'title': f"Tutorial: Cómo usar {model['name']} en tus proyectos",
            'reason': f"{model['mentions']} menciones - alto interés de la comunidad",
            'difficulty': 'intermediate',
            'format': 'hands-on tutorial',
            'angle': 'Live coding + casos de uso prácticos',
            'sources': []
        })
    
    # Idea 3: Comparativa
    if len(trends['tools_mentioned']) >= 2:
        tool1, tool2 = trends['tools_mentioned'][0], trends['tools_mentioned'][1]
        ideas.append({
            'title': f"{tool1['tool']} vs {tool2['tool']}: ¿Cuál elegir?",
            'reason': "Ambas herramientas trending - gente busca comparativas",
            'difficulty': 'intermediate',
            'format': 'comparison + demo',
            'angle': 'Testing side-by-side con métricas reales',
            'sources': []
        })
    
    # Idea 4: Tema de investigación
    if trends['research_areas']:
        research = trends['research_areas'][0]
        ideas.append({
            'title': f"Guía práctica de {research['topic']} para developers",
            'reason': f"Trending en research ({research['mentions']} menciones)",
            'difficulty': 'advanced',
            'format': 'technical deep-dive',
            'angle': 'De la teoría al código - implementación paso a paso',
            'sources': []
        })
    
    # Idea 5: Análisis de empresa
    if trends['hot_companies']:
        company = trends['hot_companies'][0]
        ideas.append({
            'title': f"¿Qué está haciendo {company['name']} y por qué debes saberlo?",
            'reason': f"Empresa más mencionada ({company['mentions']} veces)",
            'difficulty': 'beginner',
            'format': 'industry analysis',
            'angle': 'Impacto en el ecosistema + predicciones',
            'sources': []
        })
    
    # Idea 6: Contenido de Substack popular
    if top_posts:
        post = top_posts[0]
        ideas.append({
            'title': f"Reaccionando a: {post['title'][:50]}",
            'reason': f"Post viral de {post['source_name']}",
            'difficulty': 'beginner',
            'format': 'reaction + commentary',
            'angle': 'Tu opinión como expert + contexto adicional',
            'sources': [post['link']]
        })
    
    # Idea 7: Build with me
    ideas.append({
        'title': "Construyendo un agente de IA con las herramientas MÁS nuevas",
        'reason': "Formato 'build with me' tiene alto engagement",
        'difficulty': 'intermediate',
        'format': 'live project',
        'angle': f"Usar {trends['tools_mentioned'][0]['tool'] if trends['tools_mentioned'] else 'LangChain'} + {trends['hot_models'][0]['name'] if trends['hot_models'] else 'GPT-4'}",
        'sources': []
    })
    
    return ideas[:7]


def format_email_digest(news, rss_posts, trends, video_ideas):
    """
    Formatea todo en un email HTML hermoso
    
    Returns:
        {'html': '...', 'text': '...'}
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    html_parts = [
        '<html><head><meta charset="utf-8"></head>',
        '<body style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f6f8fa;">',
        f'<div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">',
        f'<h1 style="color: #0366d6; margin-top: 0;">🧠 AI Daily Digest</h1>',
        f'<p style="color: #586069; font-size: 14px;">Generado el {now}</p>',
        '<hr style="border: none; border-top: 2px solid #e1e4e8; margin: 30px 0;">',
    ]
    
    # Sección 1: Top 5 Noticias
    html_parts.append('<h2 style="color: #24292e;">📰 Top 5 Noticias de IA</h2>')
    for i, item in enumerate(news[:5], 1):
        html_parts.append(f'''
        <div style="margin-bottom: 25px; padding: 20px; background: #f6f8fa; border-left: 4px solid #0366d6; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #24292e;">{i}. {item['title']}</h3>
            <p style="color: #586069; font-size: 14px;">
                <strong>Por qué importa:</strong> Esta noticia es relevante porque destaca avances significativos en el campo de la IA 
                (Relevancia: {item.get('relevance_score', 0):.0%}).
            </p>
            <p style="color: #24292e;">{item['snippet']}</p>
            <p style="margin-bottom: 0;">
                <a href="{item['url']}" style="color: #0366d6; text-decoration: none; font-weight: 500;">
                    Leer artículo completo →
                </a>
            </p>
        </div>
        ''')
    
    # Sección 2: Highlights de Substacks
    html_parts.append('<hr style="border: none; border-top: 2px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<h2 style="color: #24292e;">✍️ Highlights de Substacks</h2>')
    for post in rss_posts[:5]:
        html_parts.append(f'''
        <div style="margin-bottom: 15px; padding: 15px; background: #fffbea; border-left: 4px solid #f9cf00; border-radius: 6px;">
            <strong style="color: #24292e;">{post['title']}</strong><br>
            <span style="color: #586069; font-size: 13px;">📝 {post['source_name']}</span><br>
            <a href="{post['link']}" style="color: #0366d6; font-size: 14px;">Leer post →</a>
        </div>
        ''')
    
    # Sección 3: Tendencias
    html_parts.append('<hr style="border: none; border-top: 2px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<h2 style="color: #24292e;">📊 Análisis de Tendencias</h2>')
    
    html_parts.append('<h3 style="color: #0366d6; font-size: 18px;">🔥 Modelos más mencionados</h3><ul>')
    for m in trends['hot_models'][:5]:
        html_parts.append(f'<li><strong>{m["name"]}</strong>: {m["mentions"]} menciones</li>')
    html_parts.append('</ul>')
    
    html_parts.append('<h3 style="color: #0366d6; font-size: 18px;">🏢 Empresas trending</h3><ul>')
    for c in trends['hot_companies'][:5]:
        html_parts.append(f'<li><strong>{c["name"]}</strong>: {c["mentions"]} menciones</li>')
    html_parts.append('</ul>')
    
    html_parts.append('<h3 style="color: #0366d6; font-size: 18px;">🔬 Áreas de investigación</h3><ul>')
    for r in trends['research_areas'][:6]:
        html_parts.append(f'<li><strong>{r["topic"]}</strong>: {r["mentions"]} menciones</li>')
    html_parts.append('</ul>')
    
    # Sección 4: Ideas de videos
    html_parts.append('<hr style="border: none; border-top: 2px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<h2 style="color: #24292e;">🎬 Ideas de Videos (Listas para grabar)</h2>')
    
    for i, idea in enumerate(video_ideas, 1):
        html_parts.append(f'''
        <div style="margin-bottom: 20px; padding: 20px; background: #e6f7ff; border-left: 4px solid #1890ff; border-radius: 6px;">
            <h3 style="margin-top: 0; color: #0050b3;">{i}. {idea['title']}</h3>
            <p style="margin: 8px 0;"><strong>💡 Por qué:</strong> {idea['reason']}</p>
            <p style="margin: 8px 0;"><strong>🎯 Formato:</strong> {idea['format']} ({idea['difficulty']})</p>
            <p style="margin: 8px 0;"><strong>📐 Ángulo:</strong> {idea['angle']}</p>
        </div>
        ''')
    
    html_parts.append('<hr style="border: none; border-top: 2px solid #e1e4e8; margin: 30px 0;">')
    html_parts.append('<p style="color: #586069; font-size: 12px; text-align: center;">Este reporte fue generado automáticamente por tu AI Content Research Agent 🤖</p>')
    html_parts.append('</div></body></html>')
    
    html_content = ''.join(html_parts)
    
    # Versión texto (simple)
    text_parts = [
        f'🧠 AI DAILY DIGEST\n',
        f'Generado: {now}\n\n',
        '=' * 60 + '\n\n',
        '📰 TOP 5 NOTICIAS\n\n'
    ]
    
    for i, item in enumerate(news[:5], 1):
        text_parts.append(f"{i}. {item['title']}\n")
        text_parts.append(f"   {item['url']}\n\n")
    
    text_parts.append('\n📊 TENDENCIAS\n\n')
    for m in trends['hot_models'][:5]:
        text_parts.append(f"• {m['name']}: {m['mentions']} menciones\n")
    
    text_parts.append('\n🎬 IDEAS DE VIDEOS\n\n')
    for i, idea in enumerate(video_ideas, 1):
        text_parts.append(f"{i}. {idea['title']}\n")
        text_parts.append(f"   {idea['reason']}\n\n")
    
    text_content = ''.join(text_parts)
    
    return {'html': html_content, 'text': text_content}


def send_email_report(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía el reporte por email (mismo código que antes)
    """
    to_email = args.get('to_email')
    subject = args.get('subject', 'AI Daily Digest')
    body_html = args.get('body_html')
    body_text = args.get('body_text', '')
    
    if not to_email:
        return _ok(False, None, "Falta 'to_email'")
    
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_user)
    
    if not smtp_user or not smtp_password:
        return _ok(False, None, "Faltan credenciales SMTP")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        if body_text:
            part1 = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(part1)
        
        if body_html:
            part2 = MIMEText(body_html, 'html', 'utf-8')
            msg.attach(part2)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return _ok(True, {'sent': True, 'to': to_email}, "")
    
    except Exception as e:
        return _ok(False, None, f"Error al enviar email: {e}")


# 🎯 FUNCIÓN PRINCIPAL: Todo en uno
def generate_daily_digest(send_email=False, to_email=None):
    """
    Genera el digest completo: noticias + RSS + tendencias + ideas + email
    
    Args:
        send_email: Si True, envía por email
        to_email: Email destino (usa env var TO_EMAIL si no se especifica)
    
    Returns:
        {
            'news': [...],
            'rss_posts': [...],
            'trends': {...},
            'video_ideas': [...],
            'email_sent': bool
        }
    """
    print("🔍 Buscando noticias de IA...")
    news = search_ai_news_advanced(hours=24, k=15)
    
    print(f"📰 Encontradas {len(news)} noticias\n")
    print("📡 Obteniendo RSS feeds...")
    rss_data = fetch_all_rss_feeds(hours=48)
    rss_posts = rss_data['all_posts']
    
    print(f"✉️  Encontrados {len(rss_posts)} posts de {len(rss_data['stats']['by_source'])} fuentes\n")
    print("📊 Analizando tendencias...")
    trends = analyze_trends(rss_posts, news)
    
    print("💡 Generando ideas de videos...")
    video_ideas = generate_video_ideas(trends, rss_posts[:10], news[:5])
    
    result = {
        'news': news[:5],
        'rss_posts': rss_posts[:10],
        'trends': trends,
        'video_ideas': video_ideas,
        'email_sent': False
    }
    
    if send_email:
        email_body = format_email_digest(news, rss_posts, trends, video_ideas)
        email_result = send_email_report({
            'to_email': to_email or os.getenv('TO_EMAIL'),
            'subject': f'🧠 AI Daily Digest - {datetime.now().strftime("%Y-%m-%d")}',
            'body_html': email_body['html'],
            'body_text': email_body['text']
        })
        result['email_sent'] = email_result.get('ok', False)
        if email_result.get('ok'):
            print(f"\n✅ Email enviado a {email_result['data']['to']}")
        else:
            print(f"\n❌ Error enviando email: {email_result.get('error')}")
    
    return result


# Para testing
if __name__ == '__main__':
    print("🚀 Generando AI Daily Digest...\n")
    digest = generate_daily_digest(send_email=False)
    
    print(f"\n📊 RESUMEN:")
    print(f"   • Noticias: {len(digest['news'])}")
    print(f"   • Posts RSS: {len(digest['rss_posts'])}")
    print(f"   • Ideas de video: {len(digest['video_ideas'])}")
    print(f"\n🔥 Top trending:")
    for m in digest['trends']['hot_models'][:3]:
        print(f"   • {m['name']}: {m['mentions']} menciones")