#!/bin/bash
# Script para actualizar API key de forma segura

echo "🔐 Actualización segura de API Key"
echo "===================================="
echo ""
echo "Por favor pega tu nueva OPENAI_API_KEY:"
echo "(no se mostrará en pantalla mientras escribes)"
read -s NEW_API_KEY
echo ""

if [ -z "$NEW_API_KEY" ]; then
    echo "❌ Error: API Key no puede estar vacío"
    exit 1
fi

# Actualizar .env
cat > .env << EOF
# Usa OpenAI o Ollama (elige uno). Si defines ambos, se prioriza OpenAI.

# --- OpenAI ---
OPENAI_API_KEY=$NEW_API_KEY
OPENAI_MODEL=gpt-4o-mini

# --- Ollama ---
OLLAMA_MODEL=llama3.1:8b
OLLAMA_HOST=http://localhost:11434

# --- Cache & Optimization ---
CACHE_DIR=cache
BATCH_DIR=batches
NOVELTY_HISTORY_DIR=content_history

# --- Agent Config ---
AGENT_AUTO_WEB=1
MAX_STEPS=5

# --- Email (opcional para digest diario) ---
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=tu_email@gmail.com
# SMTP_PASSWORD=tu_password
# EMAIL_TO=destinatario@email.com
EOF

# Permisos restrictivos
chmod 600 .env

echo "✅ API Key actualizado en .env con permisos seguros (600)"
echo ""
echo "🧪 Verificando..."
if grep -q "sk-" .env 2>/dev/null; then
    echo "✅ API Key guardado correctamente"
else
    echo "⚠️ Advertencia: formato de API Key no detectado (puede ser normal)"
fi

echo ""
echo "🔒 El archivo .env está protegido y no se subirá a git"
echo ""
echo "📝 Próximo paso: ejecuta los tests"
echo "   python cache_manager.py"
echo "   python novelty_checker.py"