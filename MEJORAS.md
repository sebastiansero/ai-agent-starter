# Mejoras del Proyecto AI Agent Starter

## ✅ Corregidas (commit actual)

### 1. **Bug crítico de UI: Saltos de línea en template strings**
- **Problema**: El JSON body tenía saltos de línea literales que rompían el JavaScript
- **Solución**: Compactar el objeto body en una línea sin template strings multilínea
- **Impacto**: Botón "Ejecutar" ahora funciona correctamente

### 2. **Deshabilitar botón Reset durante fetch**
- **Problema**: Usuario podía hacer reset mientras una petición estaba en curso
- **Solución**: `resetBtn.disabled = true` durante fetch
- **Impacto**: Mejor UX, evita estados inconsistentes

### 3. **Limpieza de template strings innecesarios**
- **Problema**: Uso de backticks para strings simples causaba problemas de parsing
- **Solución**: Usar concatenación simple con +
- **Impacto**: Código más robusto y compatible

---

## 🔧 Recomendadas (Prioridad Alta)

### 4. **Logging estructurado**
```python
# En server.py y agent.py
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# En /run endpoint:
logger.info(f"Request from session {req.session_id}: {req.task[:50]}...")
logger.info(f"Agent response: {out[:50]}...")
```
**Impacto**: Facilita debugging en producción (logs de Render)

### 5. **Timeouts configurables**
```python
# En agent.py
TOOL_TIMEOUT = int(os.getenv("TOOL_TIMEOUT", "30"))
# En tools.py para fetch_url:
timeout=TOOL_TIMEOUT
```
**Impacto**: Evita que una URL lenta bloquee el agente por minutos

### 6. **Rate limiting básico**
```python
# En server.py
from fastapi import HTTPException
from collections import defaultdict
import time

request_counts = defaultdict(list)
RATE_LIMIT = 10  # peticiones
RATE_WINDOW = 60  # segundos

@app.post("/run")
def run(req: RunReq, request: Request):
    ip = request.client.host
    now = time.time()
    request_counts[ip] = [t for t in request_counts[ip] if now - t < RATE_WINDOW]
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(429, "Rate limit exceeded")
    request_counts[ip].append(now)
    # ... resto del endpoint
```
**Impacto**: Protege contra abuso (especialmente en free tier de Render)

### 7. **Variables de entorno documentadas**
Crear `.env.example` actualizado:
```bash
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=llama3.1:8b

# Agent
AGENT_AUTO_WEB=1
AGENT_MAX_STEPS=8
TOOL_TIMEOUT=30

# Storage
CHAT_DIR=chats
RAG_PATH=rag_store.jsonl
EMBED_MODEL=text-embedding-3-small

# Render
PORT=8000
```

### 8. **Health check mejorado**
```python
@app.get("/health")
def health():
    # Verificar que el LLM responde
    try:
        agent.llm.generate([{"role":"user","content":"test"}], max_tokens=5)
        llm_ok = True
    except:
        llm_ok = False
    
    return {
        "ok": llm_ok,
        "service": "ai-agent-starter",
        "version": "0.3.0",
        "llm_status": "ok" if llm_ok else "error",
        "auto_web": getattr(agent, "auto_web", False)
    }
```
**Impacto**: Detecta problemas de API key o conectividad en health checks

---

## 📊 Recomendadas (Prioridad Media)

### 9. **Tests básicos**
```python
# tests/test_agent.py
def test_agent_basic():
    from agent import Agent
    a = Agent(max_steps=3, auto_web=False)
    # Mock LLM que devuelve {"final": "test"}
    result = a.run("test task")
    assert isinstance(result, str)

def test_tools():
    from tools import call_tool
    r = call_tool("memory_set", {"key": "test", "value": 123})
    assert r["ok"] == True
```

### 10. **Separar UI del backend**
- Crear `static/index.html` y servirlo con `app.mount("/", StaticFiles(directory="static"))`
- Ventaja: más fácil de actualizar sin tocar Python
- O mejor: frontend en React/Vue separado

### 11. **Métricas básicas**
```python
# Contador de requests exitosos/fallidos
from prometheus_client import Counter, make_asgi_app
success_counter = Counter('agent_requests_success', 'Successful requests')
error_counter = Counter('agent_requests_error', 'Failed requests')

# Montar en /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### 12. **Caché de embeddings para RAG**
```python
# tools.py
_embedding_cache = {}
def _embed(text: str):
    h = hashlib.md5(text.encode()).hexdigest()
    if h in _embedding_cache:
        return _embedding_cache[h]
    vec = client.embeddings.create(...)
    _embedding_cache[h] = vec
    return vec
```
**Impacto**: Ahorra llamadas (y $$) a OpenAI embeddings API

---

## 🚀 Recomendadas (Prioridad Baja / Nice-to-have)

### 13. **WebSocket para streaming**
- Usar SSE (Server-Sent Events) o WebSocket para respuestas progresivas
- Mostrar "pensando..." + resultados parciales de herramientas

### 14. **Persistencia real**
- SQLite o PostgreSQL en lugar de JSONL
- Ventaja: búsquedas más rápidas, transacciones, backups

### 15. **Multi-agente**
- Crear roles: "analyst" (web_trend_scan), "researcher" (RAG), "coder"
- Endpoint `/run` con parámetro `agent_type`

### 16. **UI mejorada**
- Markdown rendering (si el agente responde con `**bold**` o listas)
- Copy button para respuestas
- Dark/Light mode toggle
- Exportar conversación a JSON/TXT

### 17. **CI/CD**
- GitHub Actions que corra tests antes de merge
- Deploy automático a Render en push a `main`

---

## 📝 Resumen de próximos pasos

1. ✅ Fix UI (ya aplicado)
2. Agregar logging básico (15 min)
3. Documentar .env.example completo (10 min)
4. Crear 2-3 tests smoke (30 min)
5. Mejorar /health con check de LLM (10 min)
6. README actualizado con sección Auto-web y Trend Scan (15 min)

**Total estimado para prioridad alta: ~1.5 horas**

---

© 2025 Mejoras sugeridas por análisis del proyecto ai-agent-starter