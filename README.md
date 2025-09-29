# AI Agent Starter (Python · Warp · FastAPI · Docker)

Pequeño _starter kit_ para crear un **agente de IA desde 0** con Python.
- **LLM providers**: OpenAI API o **Ollama** (local).
- **Herramientas** integradas: `calculator`, `now`, `read_url`.
- **Bucle de agente** con **tool-calling en JSON** (sin chain-of-thought).
- **REST API** con FastAPI y **Dockerfile** listo para _deployment_.

## Estructura
```
ai-agent-starter/
├─ agent.py
├─ llm_providers.py
├─ tools.py
├─ main.py
├─ server.py
├─ requirements.txt
├─ .env.example
├─ Dockerfile
└─ README.md
```

## Requisitos
- Python 3.10+
- (Opcional) Cuenta OpenAI **o** Ollama instalado localmente.
- Warp (o cualquier terminal).

## 1) Configuración rápida (local)
```bash
# 1) Clonar/descargar y entrar al folder
cd ai-agent-starter

# 2) Crear entorno y dependencias
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3a) Usar OpenAI (recomendado si tienes API Key)
export OPENAI_API_KEY="sk-..."
# (Opcional) Modelo: por defecto gpt-4o-mini
export OPENAI_MODEL="gpt-4o-mini"

# 3b) O usar Ollama local (ej. llama3.1)
# ollama serve
export OLLAMA_MODEL="llama3.1:8b"
# (si tu puerto no es el default: export OLLAMA_HOST="http://localhost:11434")

# 4) Probar el agente por CLI
python main.py --task "Resume este texto: https://www.gutenberg.org/cache/epub/84/pg84.txt"
```

## 2) Levantar API (FastAPI)
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
# En otra terminal:
curl -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d '{"task":"Qué hora es y calcula 3*7"}'
```

## 3) Docker (local)
```bash
docker build -t ai-agent-starter .
docker run -p 8000:8000 --env-file .env.example ai-agent-starter
# POST /run como arriba
```

## 4) Deployment (ejemplos)
- **Railway/Render/Fly.io**: sube este repo o conecta Git, define `OPENAI_API_KEY` (o variables de Ollama si usas un host con Ollama).
- **Hugging Face Spaces** (CPU): posible si usas OpenAI. Para Ollama, necesitas runtime con servidor Ollama.
- **VM propia** (Lightsail, Droplet, etc.): `docker build` + `docker run` + **reverse proxy** (Nginx/Caddy).

## 5) Cómo funciona el agente
- El **modelo** recibe un contexto con herramientas disponibles y **debe** responder **solo** con JSON:
  - `{"tool": "<nombre>", "args": {...}}` para invocar una herramienta.
  - `{"final": "respuesta"}` para terminar.
- El bucle ejecuta herramientas y realimenta sus **observaciones** hasta resolver la tarea o agotar `max_steps`.

## 6) Extender
- Agrega más herramientas en `tools.py` (por ejemplo: base de datos, calendarios, Slack, etc.).
- Implementa memoria (JSON/SQLite) en `agent.py`.
- Conecta Retrieval (FAISS/Chroma) y agrega una herramienta `search_docs`.
- Crea agentes multi-rol montando varios endpoints.

---

© 2025-09-29 Starter creado para que practiques rápido con Warp y puedas desplegarlo sin dolor.
