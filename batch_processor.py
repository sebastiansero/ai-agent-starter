# -*- coding: utf-8 -*-
"""
Sistema de procesamiento por lotes (Batch API) de OpenAI
Ahorro: 50% en costos API
Ideal para: digest diario, análisis batch de múltiples artículos
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BATCH_DIR = os.getenv("BATCH_DIR", "batches")
os.makedirs(BATCH_DIR, exist_ok=True)


def create_batch_request(
    prompts: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 500
) -> str:
    """
    Crea un archivo JSONL para batch processing
    
    Args:
        prompts: Lista de dicts con {'id': str, 'system': str, 'user': str}
        model: Modelo a usar
        temperature: Temperatura
        max_tokens: Máximo de tokens
        
    Returns:
        Path al archivo JSONL creado
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_file = os.path.join(BATCH_DIR, f"batch_{timestamp}.jsonl")
    
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for idx, prompt in enumerate(prompts):
            request = {
                "custom_id": prompt.get('id', f"request-{idx}"),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": prompt.get('system', '')},
                        {"role": "user", "content": prompt['user']}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            }
            f.write(json.dumps(request) + '\n')
    
    print(f"📝 Created batch file: {jsonl_file} with {len(prompts)} requests")
    return jsonl_file


def submit_batch(jsonl_file: str, description: str = "AI Content Research Batch") -> str:
    """
    Envía el batch a OpenAI
    
    Args:
        jsonl_file: Path al archivo JSONL
        description: Descripción del batch
        
    Returns:
        Batch ID
    """
    # Subir archivo
    with open(jsonl_file, 'rb') as f:
        batch_input_file = client.files.create(
            file=f,
            purpose="batch"
        )
    
    print(f"📤 Uploaded file: {batch_input_file.id}")
    
    # Crear batch
    batch = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": description
        }
    )
    
    print(f"🚀 Batch submitted: {batch.id}")
    print(f"   Status: {batch.status}")
    
    # Guardar info del batch
    batch_info_file = jsonl_file.replace('.jsonl', '_info.json')
    with open(batch_info_file, 'w', encoding='utf-8') as f:
        json.dump({
            'batch_id': batch.id,
            'file_id': batch_input_file.id,
            'submitted_at': datetime.now().isoformat(),
            'status': batch.status
        }, f, indent=2)
    
    return batch.id


def check_batch_status(batch_id: str) -> dict:
    """
    Verifica el estado del batch
    
    Args:
        batch_id: ID del batch
        
    Returns:
        Dict con status info
    """
    batch = client.batches.retrieve(batch_id)
    
    return {
        'id': batch.id,
        'status': batch.status,
        'created_at': batch.created_at,
        'completed_at': batch.completed_at,
        'failed_at': batch.failed_at,
        'request_counts': {
            'total': batch.request_counts.total,
            'completed': batch.request_counts.completed,
            'failed': batch.request_counts.failed
        }
    }


def retrieve_batch_results(batch_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Recupera los resultados de un batch completado
    
    Args:
        batch_id: ID del batch
        
    Returns:
        Lista de resultados o None si no está listo
    """
    batch = client.batches.retrieve(batch_id)
    
    if batch.status != "completed":
        print(f"⏳ Batch not ready yet. Status: {batch.status}")
        return None
    
    if not batch.output_file_id:
        print(f"❌ No output file available")
        return None
    
    # Descargar resultados
    file_response = client.files.content(batch.output_file_id)
    
    # Parsear JSONL
    results = []
    for line in file_response.text.strip().split('\n'):
        result = json.loads(line)
        results.append({
            'id': result['custom_id'],
            'content': result['response']['body']['choices'][0]['message']['content'],
            'usage': result['response']['body']['usage']
        })
    
    print(f"✅ Retrieved {len(results)} results from batch {batch_id}")
    
    # Guardar resultados localmente
    results_file = os.path.join(BATCH_DIR, f"results_{batch_id}.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results


def wait_for_batch(batch_id: str, check_interval: int = 60, max_wait: int = 3600) -> Optional[List[Dict[str, Any]]]:
    """
    Espera a que un batch se complete y retorna resultados
    
    Args:
        batch_id: ID del batch
        check_interval: Segundos entre checks
        max_wait: Máximo tiempo de espera en segundos
        
    Returns:
        Resultados o None si timeout
    """
    start_time = time.time()
    
    while (time.time() - start_time) < max_wait:
        status = check_batch_status(batch_id)
        print(f"⏳ Batch {batch_id}: {status['status']} - {status['request_counts']['completed']}/{status['request_counts']['total']} completed")
        
        if status['status'] == 'completed':
            return retrieve_batch_results(batch_id)
        
        if status['status'] in ['failed', 'expired', 'cancelled']:
            print(f"❌ Batch failed with status: {status['status']}")
            return None
        
        time.sleep(check_interval)
    
    print(f"⏰ Timeout waiting for batch {batch_id}")
    return None


def list_batches() -> List[dict]:
    """
    Lista todos los batches
    
    Returns:
        Lista de batch info
    """
    batches = client.batches.list(limit=100)
    return [
        {
            'id': batch.id,
            'status': batch.status,
            'created_at': batch.created_at,
            'completed_at': batch.completed_at
        }
        for batch in batches.data
    ]


# Helper para crear batch de análisis de artículos
def analyze_articles_batch(articles: List[Dict[str, str]], focus: str = "AI trends") -> str:
    """
    Crea un batch para analizar múltiples artículos
    
    Args:
        articles: Lista de dicts con {'url': str, 'title': str, 'content': str}
        focus: Enfoque del análisis
        
    Returns:
        Batch ID
    """
    prompts = []
    
    for idx, article in enumerate(articles):
        prompts.append({
            'id': f"article-{idx}-{article.get('url', 'unknown')[:20]}",
            'system': f"""Eres un analista experto en {focus}. 
Tu trabajo es analizar artículos y extraer:
1. Temas principales (keywords)
2. Nivel de novedad (1-10)
3. Potencial para video (1-10)
4. Resumen en 2-3 frases""",
            'user': f"""Título: {article['title']}

Contenido:
{article['content'][:2000]}

Analiza este artículo siguiendo el formato solicitado."""
        })
    
    jsonl_file = create_batch_request(prompts, model="gpt-4o-mini", max_tokens=300)
    batch_id = submit_batch(jsonl_file, f"Article Analysis: {focus}")
    
    return batch_id


if __name__ == '__main__':
    print("🧪 Testing Batch API System...\n")
    
    # Test simple
    test_prompts = [
        {
            'id': 'test-1',
            'system': 'Eres un asistente útil.',
            'user': '¿Qué es inteligencia artificial en una frase?'
        },
        {
            'id': 'test-2',
            'system': 'Eres un asistente útil.',
            'user': '¿Qué es machine learning en una frase?'
        }
    ]
    
    print("Creating test batch...")
    jsonl_file = create_batch_request(test_prompts, max_tokens=50)
    
    print("\n📋 To submit this batch, run:")
    print(f"   batch_id = submit_batch('{jsonl_file}')")
    print("\n📋 To check status:")
    print("   check_batch_status(batch_id)")
    print("\n📋 To retrieve results:")
    print("   results = retrieve_batch_results(batch_id)")
    
    print("\n💡 Tip: Batches usually complete in minutes to hours")
    print("   Cost: 50% cheaper than regular API!")