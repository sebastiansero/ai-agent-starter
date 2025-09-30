#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fase 3 - Features Avanzados para Investigación de Contenido de IA

1. Análisis de Hype vs Sustancia
2. Análisis de Competencia
3. Generación de Títulos y Thumbnails
4. Sistema de Scoring Inteligente
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==========================================
# 1. ANÁLISIS DE HYPE VS SUSTANCIA
# ==========================================

def analyze_hype_vs_substance(
    title: str,
    content: str,
    sources: List[str] = None
) -> Dict[str, Any]:
    """
    Detecta si un tema tiene contenido real o es solo hype/ruido
    
    Args:
        title: Título del artículo/tema
        content: Contenido del artículo
        sources: Lista de URLs fuente (opcional)
        
    Returns:
        {
            'substance_score': float (0-10),
            'hype_score': float (0-10),
            'verdict': 'substance' | 'hype' | 'mixed',
            'reasoning': str,
            'red_flags': [str],
            'green_flags': [str]
        }
    """
    # Red flags típicos de hype sin sustancia
    hype_indicators = [
        r'\b(revolucion|revolucionar|cambiar el mundo|game changer)\b',
        r'\b(nunca antes visto|histórico|sin precedentes)\b',
        r'\b(pronto|muy pronto|inminente)\b',
        r'\b(rumor|se dice|podría|posiblemente)\b',
        r'[!]{2,}',  # Múltiples signos de exclamación
    ]
    
    # Green flags de contenido sustancial
    substance_indicators = [
        r'\b(paper|estudio|investigación|research)\b',
        r'\b(benchmark|resultado|métrica|performance)\b',
        r'\b(código|github|open source|implementación)\b',
        r'\b(técnica|arquitectura|algoritmo|método)\b',
        r'\d+%',  # Porcentajes (datos concretos)
    ]
    
    combined_text = (title + " " + content).lower()
    
    # Contar indicadores
    hype_count = sum(1 for pattern in hype_indicators if re.search(pattern, combined_text, re.IGNORECASE))
    substance_count = sum(1 for pattern in substance_indicators if re.search(pattern, combined_text, re.IGNORECASE))
    
    # Scoring simple basado en indicadores
    hype_score_simple = min(10, hype_count * 2)
    substance_score_simple = min(10, substance_count * 2)
    
    # Análisis con LLM para más precisión
    prompt = f"""Analiza este tema de IA y determina si tiene contenido sustancial o es principalmente hype:

Título: {title}

Contenido: {content[:1500]}

Evalúa:
1. ¿Tiene datos concretos, benchmarks, papers, código?
2. ¿Hay afirmaciones verificables o solo especulación?
3. ¿Es información nueva y útil o ruido mediático?

Responde en JSON:
{{
    "substance_score": <0-10>,
    "hype_score": <0-10>,
    "verdict": "substance|hype|mixed",
    "reasoning": "<explicación breve>",
    "red_flags": ["flag1", "flag2"],
    "green_flags": ["flag1", "flag2"]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista experto en detectar hype vs contenido sustancial en noticias de IA."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        # Combinar con scoring simple
        result['substance_score'] = (result['substance_score'] + substance_score_simple) / 2
        result['hype_score'] = (result['hype_score'] + hype_score_simple) / 2
        
        return result
        
    except Exception as e:
        # Fallback a scoring simple
        return {
            'substance_score': substance_score_simple,
            'hype_score': hype_score_simple,
            'verdict': 'substance' if substance_score_simple > hype_score_simple else 'hype',
            'reasoning': f'Análisis basado en indicadores textuales (LLM error: {e})',
            'red_flags': ['Múltiples indicadores de hype'] if hype_count > 3 else [],
            'green_flags': ['Contiene datos concretos'] if substance_count > 3 else []
        }


# ==========================================
# 2. ANÁLISIS DE COMPETENCIA
# ==========================================

def analyze_competition(
    topic: str,
    your_channel_themes: List[str] = None
) -> Dict[str, Any]:
    """
    Analiza qué están cubriendo otros creadores de contenido
    y encuentra gaps/oportunidades
    
    Args:
        topic: Tema a analizar
        your_channel_themes: Temas que ya cubres (opcional)
        
    Returns:
        {
            'saturation_level': 'low' | 'medium' | 'high',
            'competition_score': float (0-10),
            'unique_angles': [str],
            'gap_opportunities': [str],
            'recommendation': str
        }
    """
    # Simular búsqueda de competencia (en producción usarías YouTube API, etc)
    prompt = f"""Analiza el nivel de competencia y saturación para este tema de IA:

Tema: {topic}

Evalúa:
1. ¿Cuántos creadores ya cubren este tema? (low/medium/high saturation)
2. ¿Qué ángulos únicos quedan por explorar?
3. ¿Hay gaps u oportunidades no cubiertas?
4. ¿Vale la pena crear contenido sobre esto?

Responde en JSON:
{{
    "saturation_level": "low|medium|high",
    "competition_score": <0-10, donde 10 es muy competido>,
    "unique_angles": ["ángulo1", "ángulo2", "ángulo3"],
    "gap_opportunities": ["gap1", "gap2"],
    "recommendation": "<tu recomendación>"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un analista de contenido de YouTube especializado en IA."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {
            'saturation_level': 'medium',
            'competition_score': 5.0,
            'unique_angles': ['Enfoque técnico', 'Aplicaciones prácticas'],
            'gap_opportunities': ['Tutorial paso a paso', 'Comparativa detallada'],
            'recommendation': f'Análisis no disponible: {e}'
        }


# ==========================================
# 3. GENERACIÓN DE TÍTULOS Y THUMBNAILS
# ==========================================

def generate_video_titles(
    topic: str,
    target_audience: str = "desarrolladores y entusiastas de IA",
    style: str = "informativo y atractivo"
) -> Dict[str, Any]:
    """
    Genera títulos atractivos para videos de YouTube
    
    Args:
        topic: Tema del video
        target_audience: Audiencia objetivo
        style: Estilo del título
        
    Returns:
        {
            'titles': [
                {
                    'title': str,
                    'hook': str,
                    'viral_potential': float (0-10),
                    'reasoning': str
                }
            ],
            'thumbnail_ideas': [str]
        }
    """
    prompt = f"""Genera 5 títulos atractivos para un video de YouTube sobre:

Tema: {topic}
Audiencia: {target_audience}
Estilo: {style}

Los títulos deben:
- Ser claros y específicos
- Generar curiosidad
- Tener potencial viral
- Ser honestos (no clickbait excesivo)

También sugiere 3 ideas para thumbnails.

Responde en JSON:
{{
    "titles": [
        {{
            "title": "<título>",
            "hook": "<qué lo hace atractivo>",
            "viral_potential": <1-10>,
            "reasoning": "<por qué funcionará>"
        }}
    ],
    "thumbnail_ideas": ["idea1", "idea2", "idea3"]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un experto en títulos virales para YouTube especializado en contenido tech/IA."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        import json
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        return {
            'titles': [
                {
                    'title': f'{topic}: Lo Que Necesitas Saber',
                    'hook': 'Título genérico de respaldo',
                    'viral_potential': 5.0,
                    'reasoning': f'Error en generación: {e}'
                }
            ],
            'thumbnail_ideas': ['Imagen del logo', 'Diagrama explicativo', 'Código en pantalla']
        }


# ==========================================
# 4. SISTEMA DE SCORING INTELIGENTE
# ==========================================

def calculate_content_score(
    topic: str,
    novelty_score: float,
    hype_analysis: Dict[str, Any] = None,
    competition_analysis: Dict[str, Any] = None,
    timing_factor: float = 1.0
) -> Dict[str, Any]:
    """
    Sistema de scoring inteligente que combina múltiples factores
    
    Args:
        topic: Tema a evaluar
        novelty_score: Score de novedad (0-1) del novelty_checker
        hype_analysis: Resultado de analyze_hype_vs_substance
        competition_analysis: Resultado de analyze_competition
        timing_factor: Factor de timing (1.0 = óptimo)
        
    Returns:
        {
            'final_score': float (0-100),
            'priority': 'high' | 'medium' | 'low',
            'breakdown': {
                'novelty': float,
                'substance': float,
                'opportunity': float,
                'timing': float
            },
            'recommendation': str
        }
    """
    scores = {
        'novelty': novelty_score * 10,  # 0-10
        'substance': 5.0,  # Default
        'opportunity': 5.0,  # Default
        'timing': timing_factor * 10  # 0-10
    }
    
    # Incorporar análisis de hype
    if hype_analysis:
        scores['substance'] = hype_analysis.get('substance_score', 5.0)
    
    # Incorporar análisis de competencia
    if competition_analysis:
        comp_score = competition_analysis.get('competition_score', 5.0)
        # Invertir: menos competencia = más oportunidad
        scores['opportunity'] = 10 - comp_score
    
    # Pesos para cada factor
    weights = {
        'novelty': 0.35,      # 35% - Lo más importante
        'substance': 0.30,     # 30% - Contenido real
        'opportunity': 0.25,   # 25% - Poca competencia
        'timing': 0.10         # 10% - Momento adecuado
    }
    
    # Calcular score final (0-100)
    final_score = sum(scores[k] * weights[k] for k in scores.keys()) * 10
    
    # Determinar prioridad
    if final_score >= 75:
        priority = 'high'
        recommendation = '🔥 Tema excelente - Crear video ASAP'
    elif final_score >= 50:
        priority = 'medium'
        recommendation = '👍 Buen tema - Considerar para próximos videos'
    else:
        priority = 'low'
        recommendation = '⏸️ Tema mediocre - Buscar alternativas mejores'
    
    return {
        'final_score': round(final_score, 2),
        'priority': priority,
        'breakdown': {k: round(v, 2) for k, v in scores.items()},
        'recommendation': recommendation
    }


# ==========================================
# FUNCIÓN COMPLETA DE ANÁLISIS
# ==========================================

def comprehensive_topic_analysis(
    topic: str,
    content: str = "",
    novelty_score: float = 1.0,
    analyze_all: bool = True
) -> Dict[str, Any]:
    """
    Análisis completo de un tema combinando todos los features avanzados
    
    Args:
        topic: Tema a analizar
        content: Contenido/descripción del tema
        novelty_score: Score de novedad del novelty_checker
        analyze_all: Si True, ejecuta todos los análisis (más lento pero completo)
        
    Returns:
        Dict completo con todos los análisis
    """
    print(f"\n🔍 Analizando: {topic}")
    print("="*60)
    
    result = {
        'topic': topic,
        'timestamp': datetime.now().isoformat()
    }
    
    # 1. Hype vs Sustancia
    if analyze_all and content:
        print("📊 Análisis de Hype vs Sustancia...")
        result['hype_analysis'] = analyze_hype_vs_substance(topic, content)
        print(f"   Sustancia: {result['hype_analysis']['substance_score']:.1f}/10")
        print(f"   Veredicto: {result['hype_analysis']['verdict']}")
    
    # 2. Competencia
    if analyze_all:
        print("\n🎯 Análisis de Competencia...")
        result['competition'] = analyze_competition(topic)
        print(f"   Saturación: {result['competition']['saturation_level']}")
        print(f"   Oportunidad: {10 - result['competition']['competition_score']:.1f}/10")
    
    # 3. Títulos
    print("\n✏️ Generando Títulos...")
    result['titles'] = generate_video_titles(topic)
    print(f"   Generados: {len(result['titles']['titles'])} títulos")
    if result['titles']['titles']:
        print(f"   Top: {result['titles']['titles'][0]['title']}")
    
    # 4. Scoring Final
    print("\n🎯 Calculando Score Final...")
    result['score'] = calculate_content_score(
        topic,
        novelty_score,
        result.get('hype_analysis'),
        result.get('competition')
    )
    print(f"   Score: {result['score']['final_score']:.1f}/100")
    print(f"   Prioridad: {result['score']['priority'].upper()}")
    print(f"   {result['score']['recommendation']}")
    
    print("="*60)
    
    return result


if __name__ == '__main__':
    print("🚀 Testing Advanced Features\n")
    
    # Test con un tema de ejemplo
    test_topic = "GPT-5 Multimodal Release"
    test_content = """OpenAI announced GPT-5 with breakthrough multimodal capabilities. 
    The new model shows 40% improvement on benchmarks and includes native video understanding. 
    Research paper and technical details available."""
    
    result = comprehensive_topic_analysis(
        topic=test_topic,
        content=test_content,
        novelty_score=0.95,
        analyze_all=True
    )
    
    # Mostrar resultado completo
    print("\n📄 RESULTADO COMPLETO:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))