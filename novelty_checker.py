# -*- coding: utf-8 -*-
"""
Sistema de verificación de novedad para evitar contenido repetido
Usa embeddings + similitud coseno para detectar temas ya cubiertos
"""

import json
import os
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HISTORY_DIR = os.getenv("NOVELTY_HISTORY_DIR", "content_history")
os.makedirs(HISTORY_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(HISTORY_DIR, "topics_history.json")


def get_embedding(text: str, model="text-embedding-3-small") -> List[float]:
    """
    Obtiene embedding de OpenAI
    
    Args:
        text: Texto a embedir
        model: Modelo de embeddings (small es 10x más barato)
        
    Returns:
        Vector embedding
    """
    text = text.replace("\n", " ").strip()
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calcula similitud coseno entre dos vectores
    
    Returns:
        Float entre 0 (diferentes) y 1 (idénticos)
    """
    v1_arr = np.array(v1)
    v2_arr = np.array(v2)
    
    dot = np.dot(v1_arr, v2_arr)
    norm1 = np.linalg.norm(v1_arr)
    norm2 = np.linalg.norm(v2_arr)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot / (norm1 * norm2))


def load_history() -> List[Dict[str, Any]]:
    """
    Carga historial de temas cubiertos
    
    Returns:
        [
            {
                'topic': str,
                'embedding': List[float],
                'covered_date': str,
                'video_title': str (optional)
            },
            ...
        ]
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_history(history: List[Dict[str, Any]]) -> None:
    """
    Guarda historial
    """
    # Mantener solo últimos 6 meses de historia
    cutoff = (datetime.now() - timedelta(days=180)).isoformat()
    history = [
        h for h in history 
        if h.get('covered_date', '') >= cutoff
    ]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def check_novelty(
    topic: str,
    threshold: float = 0.75,
    max_history: int = 100
) -> Dict[str, Any]:
    """
    Verifica si un tema es novedoso comparándolo con historial
    
    Args:
        topic: Tema a verificar (título, descripción, etc)
        threshold: Umbral de similitud (>= threshold = repetido)
        max_history: Máximo de items de historial a comparar
        
    Returns:
        {
            'is_novel': bool,
            'novelty_score': float (0-1, 1=completamente nuevo),
            'similar_topics': [
                {
                    'topic': str,
                    'similarity': float,
                    'covered_date': str
                },
                ...
            ]
        }
    """
    history = load_history()
    
    if not history:
        return {
            'is_novel': True,
            'novelty_score': 1.0,
            'similar_topics': []
        }
    
    # Generar embedding del nuevo tema
    try:
        topic_embedding = get_embedding(topic)
    except Exception as e:
        # Si falla embedding, asumimos que es nuevo
        return {
            'is_novel': True,
            'novelty_score': 1.0,
            'similar_topics': [],
            'error': str(e)
        }
    
    # Comparar con histórico (solo los más recientes)
    recent_history = history[-max_history:]
    similarities = []
    
    for hist_item in recent_history:
        if 'embedding' not in hist_item:
            continue
        
        sim = cosine_similarity(topic_embedding, hist_item['embedding'])
        
        similarities.append({
            'topic': hist_item.get('topic', ''),
            'similarity': sim,
            'covered_date': hist_item.get('covered_date', ''),
            'video_title': hist_item.get('video_title', '')
        })
    
    # Ordenar por similitud
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Calcular novelty score (inverso de la máxima similitud)
    max_similarity = similarities[0]['similarity'] if similarities else 0.0
    novelty_score = 1.0 - max_similarity
    
    is_novel = max_similarity < threshold
    
    return {
        'is_novel': is_novel,
        'novelty_score': novelty_score,
        'similar_topics': similarities[:5]  # Top 5 más similares
    }


def add_to_history(
    topic: str,
    video_title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Agrega un tema al historial (después de cubrir en video)
    
    Args:
        topic: Tema cubierto
        video_title: Título del video (opcional)
        metadata: Metadata adicional
    """
    try:
        embedding = get_embedding(topic)
    except Exception as e:
        print(f"Warning: Could not generate embedding: {e}")
        return
    
    history = load_history()
    
    entry = {
        'topic': topic,
        'embedding': embedding,
        'covered_date': datetime.now().isoformat(),
        'video_title': video_title or '',
        'metadata': metadata or {}
    }
    
    history.append(entry)
    save_history(history)
    
    print(f"✅ Added to history: {topic}")


def filter_novel_topics(
    topics: List[str],
    threshold: float = 0.75,
    return_details: bool = False
) -> List[Any]:
    """
    Filtra lista de temas para obtener solo los novedosos
    
    Args:
        topics: Lista de temas/títulos
        threshold: Umbral de novedad
        return_details: Si True, retorna dict con detalles
        
    Returns:
        Lista de temas novedosos (str) o detalles completos
    """
    results = []
    
    for topic in topics:
        check = check_novelty(topic, threshold)
        
        if check['is_novel']:
            if return_details:
                results.append({
                    'topic': topic,
                    'novelty_score': check['novelty_score'],
                    'similar_topics': check['similar_topics']
                })
            else:
                results.append(topic)
    
    return results


def get_history_stats() -> Dict[str, Any]:
    """
    Estadísticas del historial
    """
    history = load_history()
    
    if not history:
        return {
            'total_topics': 0,
            'date_range': None
        }
    
    dates = [h.get('covered_date', '') for h in history if h.get('covered_date')]
    dates = sorted(dates)
    
    return {
        'total_topics': len(history),
        'oldest_entry': dates[0] if dates else None,
        'newest_entry': dates[-1] if dates else None,
        'date_range_days': (
            (datetime.fromisoformat(dates[-1]) - datetime.fromisoformat(dates[0])).days
            if len(dates) >= 2 else 0
        )
    }


if __name__ == '__main__':
    print("🧪 Testing Novelty Checker...\n")
    
    # Test 1: Nuevo tema
    test_topic = "Nueva arquitectura de transformers llamada Mamba2"
    result = check_novelty(test_topic)
    
    print(f"Topic: {test_topic}")
    print(f"Is novel: {result['is_novel']}")
    print(f"Novelty score: {result['novelty_score']:.2f}")
    
    if result['similar_topics']:
        print("\nMost similar topics:")
        for sim in result['similar_topics'][:3]:
            print(f"  - {sim['topic'][:50]}... (sim: {sim['similarity']:.2f})")
    
    # Test 2: Agregar al historial
    print("\n\nAdding to history...")
    add_to_history(
        test_topic,
        video_title="Explicación de Mamba2",
        metadata={'views': 0, 'date': datetime.now().isoformat()}
    )
    
    # Test 3: Verificar repetición
    similar_topic = "Mamba2: nueva arquitectura transformer"
    result2 = check_novelty(similar_topic)
    
    print(f"\n\nSimilar topic: {similar_topic}")
    print(f"Is novel: {result2['is_novel']}")
    print(f"Novelty score: {result2['novelty_score']:.2f}")
    
    # Test 4: Stats
    stats = get_history_stats()
    print(f"\n\n📊 History stats:")
    print(f"   Total topics: {stats['total_topics']}")
    print(f"   Date range: {stats.get('date_range_days', 0)} days")
    
    print("\n✅ Novelty checker ready!")
    print("\n💡 Usage:")
    print("   1. Before creating content, check_novelty(topic)")
    print("   2. After publishing video, add_to_history(topic, video_title)")
    print("   3. Filter ideas: filter_novel_topics([topic1, topic2, ...])")