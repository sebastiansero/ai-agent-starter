# 🧠 Agente de Tendencias Web

**Agente conversacional de IA** que analiza tendencias en la web, busca información actualizada y responde con fuentes citadas.

## ✨ Características

- 🤖 **Auto-web mode**: Detecta preguntas factuales y busca automáticamente en la web
- 📊 **Trend Scan**: Analiza noticias, extrae keywords y dominios principales
- 📚 **RAG**: Indexa y busca en documentos con embeddings de OpenAI
- 💬 **Memoria conversacional**: Recuerda el contexto por sesión
- 🌐 **Web search + clean reader**: Busca con DuckDuckGo y extrae texto limpio con trafilatura
- 🚀 **API REST + UI moderna**: Chat web listo para usar
- 🐳 **Docker**: Deployment con un click en Render, Railway, Fly.io

## 📋 Stack

- **Backend**: Python 3.11+ · FastAPI · Uvicorn
- **LLM**: OpenAI API (gpt-4o-mini) o Ollama local
- **Herramientas**: DuckDuckGo Search · Trafilatura · OpenAI Embeddings
- **Frontend**: HTML/CSS/JS vanilla (sin frameworks)

## 📁 Estructura

```
ai-agent-starter/
├── agent.py              # Bucle del agente + auto-web mode
├── llm_providers.py      # OpenAI + Ollama providers
├── tools.py              # Herramientas: web_search, trend_scan, RAG, memoria
├── server.py             # FastAPI server + endpoints
├── static/
│   └── index.html        # UI del chat (HTML/CSS/JS)
├── main.py               # CLI para pruebas
├── requirements.txt      # Dependencias
├── Dockerfile            # Imagen Docker para deployment
├── MEJORAS.md            # Roadmap de mejoras
└── README.md
```

## 🛠️ Requisitos

- Python 3.11+
- Cuenta OpenAI con API key (o Ollama local como alternativa)
- Git

## 🚀 Quick Start (Local)

```bash
# 1) Clonar el repo
git clone https://github.com/sebastiansero/ai-agent-starter.git
cd ai-agent-starter

# 2) Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3) Configurar OpenAI API key
export OPENAI_API_KEY="sk-proj-..."
# Opcional: cambiar modelo (por defecto gpt-4o-mini)
export OPENAI_MODEL="gpt-4o-mini"

# 4) Levantar el servidor
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# 5) Abrir en el navegador
# http://localhost:8000
```

### Alternativamente: usar Ollama (sin OpenAI)

```bash
# 1) Instalar Ollama: https://ollama.ai
# 2) Descargar modelo
ollama pull llama3.1:8b

# 3) Configurar variables
export OLLAMA_MODEL="llama3.1:8b"
export OLLAMA_HOST="http://localhost:11434"
# NO pongas OPENAI_API_KEY (el agente prioriza OpenAI si existe)

# 4) Levantar servidor
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## 🔧 Uso del agente

### Desde la UI web
1. Abre http://localhost:8000 en tu navegador
2. Escribe preguntas como:
   - "¿Qué está pasando con la inteligencia artificial?"
   - "¿Quién es Satoshi Nakamoto?"
   - "Tendencias en Python este mes"
3. El agente buscará en la web automáticamente y te dará una respuesta con fuentes

### Desde la API REST

```bash
# Pregunta simple
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task":"Hola, ¿qué puedes hacer?"}'

# Usar herramienta específica (web_trend_scan)
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task":"Usa web_trend_scan con topic FastAPI y k 5; TERMINA con 3 bullets y fuentes."}'

# Con sesión persistente
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task":"Mi nombre es Ana", "session_id":"demo123"}'

curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task":"¿Cómo me llamo?", "session_id":"demo123"}'
```

### Desde la CLI

```bash
python main.py --task "¿Qué es FastAPI?"
```

## 🐳 Docker

```bash
# Build
docker build -t ai-agent-starter .

# Run (con env vars)
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="sk-..." \
  -e OPENAI_MODEL="gpt-4o-mini" \
  ai-agent-starter

# Abrir http://localhost:8000
```

## ☁️ Deployment en Render

1. **Fork este repo** en tu GitHub
2. **Crear nuevo Web Service** en [Render](https://render.com)
3. **Conectar tu fork** del repo
4. **Configurar**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. **Variables de entorno** (Environment):
   ```
   OPENAI_API_KEY=sk-proj-...
   OPENAI_MODEL=gpt-4o-mini
   AGENT_AUTO_WEB=1
   ```
6. **Deploy** → Espera 2-3 min
7. **Abrir tu URL** (ej: `https://tu-agente.onrender.com`)

### Otras plataformas

- **Railway**: Similar a Render, detecta Dockerfile automáticamente
- **Fly.io**: `fly launch` + configura secrets con `fly secrets set OPENAI_API_KEY=...`
- **Vercel/Netlify**: No recomendado (serverless con timeouts cortos)
- **VM/VPS**: Docker + Nginx reverse proxy

## 🧠 Cómo funciona

### Arquitectura del agente

1. **Usuario hace una pregunta** (¿Qué está pasando con X?)
2. **Auto-web mode** detecta si es pregunta factual
3. **Agente ejecuta herramientas**:
   - `web_search`: Busca en DuckDuckGo (hasta 10 resultados)
   - `read_url_clean`: Extrae texto limpio de las URLs top
   - `web_trend_scan`: Analiza noticias + extrae keywords/dominios
4. **LLM sintetiza** la información y responde con:
   - 3-6 viñetas con insights
   - Sección "Fuentes:" con URLs
5. **Memoria conversacional** persiste contexto por sesión

### Herramientas disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `web_search` | Busca en la web con DuckDuckGo |
| `read_url_clean` | Extrae texto limpio de una URL |
| `web_trend_scan` | Analiza tendencias (news + keywords + dominios) |
| `memory_set` / `memory_get` | Memoria efímera clave-valor |
| `rag_upsert_url` | Indexa URL en base vectorial |
| `rag_search` | Busca en base vectorial con embeddings |

### Bucle del agente

```python
# Pseudo-código simplificado
for step in range(max_steps):
    # LLM decide qué hacer
    response = llm.generate(messages)
    parsed = parse_json(response)
    
    if "final" in parsed:
        return parsed["final"]  # Terminar con respuesta
    
    if "tool" in parsed:
        result = call_tool(parsed["tool"], parsed["args"])
        observations.append(result)
        # Realimentar al LLM en siguiente iteración
```

## 🔧 Extender y personalizar

### Añadir nuevas herramientas

Edita `tools.py`:

```python
def mi_herramienta(args):
    """Descripción de la herramienta"""
    dato = args.get("parametro")
    # Tu lógica aquí
    return _ok(True, {"resultado": dato}, "")

# Registrar
TOOLS["mi_herramienta"] = (
    "Descripción para el LLM. Args: {'parametro':'...'}",
    mi_herramienta
)
```

### Desactivar auto-web mode

```bash
export AGENT_AUTO_WEB=0
```

### Cambiar modelo LLM

```bash
# OpenAI
export OPENAI_MODEL="gpt-4o"  # o gpt-4-turbo, etc.

# Ollama
export OLLAMA_MODEL="mixtral:8x7b"  # o llama3.1:70b, etc.
```

### Ajustar max_steps

Edita `server.py`:

```python
agent = Agent(max_steps=12)  # por defecto es 8
```

## 📊 Roadmap

Ver [MEJORAS.md](MEJORAS.md) para el roadmap completo de mejoras planificadas.

**Próximos pasos**:
- [ ] Logging estructurado
- [ ] Rate limiting
- [ ] Tests unitarios
- [ ] Health check mejorado (valida LLM)
- [ ] UI: Markdown rendering
- [ ] Persistencia en SQLite/PostgreSQL

---

© 2025-09-29 Starter creado para que practiques rápido con Warp y puedas desplegarlo sin dolor.
