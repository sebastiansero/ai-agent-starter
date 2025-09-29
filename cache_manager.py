# -*- coding: utf-8 -*-
"""
Sistema de cache para ahorrar llamadas a API (OpenAI, DuckDuckGo, etc)
Ahorro estimado: 70-80% en costos
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional


CACHE_DIR = os.getenv("CACHE_DIR", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def cache_key(data: dict) -> str:
    """
    Genera un hash único para cachear basado en los parámetros
    
    Args:
        data: Dict con parámetros de la función
        
    Returns:
        Hash MD5 como string
    """
    # Ordenar keys para consistencia
    key_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def get_cached(key: str, max_age_hours: int = 24) -> Optional[Any]:
    """
    Lee del cache si existe y no ha expirado
    
    Args:
        key: Hash del cache
        max_age_hours: Máximo tiempo de vida del cache
        
    Returns:
        Data cacheada o None si no existe/expiró
    """
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        # Verificar expiración
        cached_time = datetime.fromisoformat(cached['timestamp'])
        age = datetime.now() - cached_time
        
        if age > timedelta(hours=max_age_hours):
            # Expiró - borrar archivo
            os.remove(cache_file)
            return None
        
        # Cache válido
        return cached['data']
    
    except Exception as e:
        # Cache corrupto - borrar
        try:
            os.remove(cache_file)
        except:
            pass
        return None


def set_cache(key: str, data: Any) -> None:
    """
    Guarda data en cache
    
    Args:
        key: Hash del cache
        data: Data a guardar (debe ser JSON-serializable)
    """
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'data': data
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Si falla, no es crítico - solo no se cachea
        print(f"Warning: Could not cache data: {e}")


def clear_cache(older_than_hours: int = 72) -> int:
    """
    Limpia cache antiguo
    
    Args:
        older_than_hours: Borrar cache más antiguo que esto
        
    Returns:
        Número de archivos borrados
    """
    if not os.path.exists(CACHE_DIR):
        return 0
    
    deleted = 0
    cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
    
    for filename in os.listdir(CACHE_DIR):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(CACHE_DIR, filename)
        
        try:
            with open(filepath, 'r') as f:
                cached = json.load(f)
            
            cached_time = datetime.fromisoformat(cached['timestamp'])
            
            if cached_time < cutoff_time:
                os.remove(filepath)
                deleted += 1
        except:
            # Archivo corrupto - borrar
            try:
                os.remove(filepath)
                deleted += 1
            except:
                pass
    
    return deleted


def cache_stats() -> dict:
    """
    Estadísticas del cache
    
    Returns:
        {
            'total_files': int,
            'total_size_mb': float,
            'oldest_entry': str,
            'newest_entry': str
        }
    """
    if not os.path.exists(CACHE_DIR):
        return {'total_files': 0, 'total_size_mb': 0}
    
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
    
    if not files:
        return {'total_files': 0, 'total_size_mb': 0}
    
    total_size = sum(
        os.path.getsize(os.path.join(CACHE_DIR, f)) 
        for f in files
    )
    
    timestamps = []
    for filename in files:
        try:
            with open(os.path.join(CACHE_DIR, filename), 'r') as f:
                cached = json.load(f)
            timestamps.append(cached['timestamp'])
        except:
            continue
    
    return {
        'total_files': len(files),
        'total_size_mb': round(total_size / (1024*1024), 2),
        'oldest_entry': min(timestamps) if timestamps else None,
        'newest_entry': max(timestamps) if timestamps else None
    }


# Decorador para funciones cacheables
def cacheable(max_age_hours=24):
    """
    Decorador que agrega caching automático a una función
    
    Uso:
        @cacheable(max_age_hours=6)
        def mi_funcion_costosa(param1, param2):
            # código costoso
            return resultado
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generar cache key basado en función + argumentos
            cache_data = {
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key = cache_key(cache_data)
            
            # Intentar leer del cache
            cached_result = get_cached(key, max_age_hours)
            if cached_result is not None:
                print(f"✅ Cache hit: {func.__name__}")
                return cached_result
            
            # Cache miss - ejecutar función
            print(f"🔄 Cache miss: {func.__name__} - ejecutando...")
            result = func(*args, **kwargs)
            
            # Guardar en cache
            set_cache(key, result)
            
            return result
        
        return wrapper
    return decorator


if __name__ == '__main__':
    # Test del sistema de cache
    print("🧪 Testing cache system...\n")
    
    # Test 1: Guardar y leer
    test_key = cache_key({'test': 'data', 'number': 123})
    test_data = {'result': [1, 2, 3], 'message': 'Hello'}
    
    set_cache(test_key, test_data)
    retrieved = get_cached(test_key)
    
    assert retrieved == test_data, "Cache read/write failed"
    print("✅ Test 1 passed: Cache read/write works")
    
    # Test 2: Expiración
    old_key = cache_key({'old': 'data'})
    set_cache(old_key, {'old': True})
    
    # Simular expiración modificando el archivo
    cache_file = os.path.join(CACHE_DIR, f"{old_key}.json")
    with open(cache_file, 'r') as f:
        old_cached = json.load(f)
    
    old_cached['timestamp'] = (datetime.now() - timedelta(hours=25)).isoformat()
    
    with open(cache_file, 'w') as f:
        json.dump(old_cached, f)
    
    expired = get_cached(old_key, max_age_hours=24)
    assert expired is None, "Cache expiration failed"
    print("✅ Test 2 passed: Cache expiration works")
    
    # Test 3: Stats
    stats = cache_stats()
    print(f"\n📊 Cache stats:")
    print(f"   Files: {stats['total_files']}")
    print(f"   Size: {stats['total_size_mb']} MB")
    
    # Test 4: Decorador
    call_count = 0
    
    @cacheable(max_age_hours=1)
    def expensive_function(x, y):
        global call_count
        call_count += 1
        return x + y
    
    result1 = expensive_function(5, 3)
    result2 = expensive_function(5, 3)  # Debe usar cache
    
    assert result1 == result2 == 8, "Decorator failed"
    assert call_count == 1, "Function called twice (cache didn't work)"
    print("\n✅ Test 3 passed: Decorator works (function called only once)")
    
    # Cleanup
    deleted = clear_cache(older_than_hours=0)
    print(f"\n🧹 Cleaned up {deleted} cache files")
    
    print("\n✅ All tests passed! Cache system ready.")