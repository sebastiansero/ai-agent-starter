#!/bin/bash
# Script de automatización para digest diario
# Configurar con cron: 0 */6 * * * /path/to/run_daily_digest.sh

# Colors para output
GREEN='\033[0.32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🤖 AI Daily Digest - Automated Run${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Started: $(date)"
echo ""

# Cambiar al directorio del proyecto
PROJECT_DIR="/Users/sebastianr/Downloads/ai-agent-starter"
cd "$PROJECT_DIR" || exit 1

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Verificar que existe .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    exit 1
fi

# Crear directorio de logs si no existe
mkdir -p logs

# Generar timestamp para el log
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/digest_${TIMESTAMP}.log"

# Ejecutar digest diario
echo "Running daily digest..."
python daily_digest_optimized.py > "$LOG_FILE" 2>&1

# Verificar resultado
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Digest generated successfully${NC}"
    
    # Obtener el archivo generado más reciente
    LATEST_DIGEST=$(ls -t digests/digest_*.md 2>/dev/null | head -1)
    
    if [ -n "$LATEST_DIGEST" ]; then
        echo -e "${GREEN}📄 Saved to: $LATEST_DIGEST${NC}"
        
        # Mostrar preview
        echo ""
        echo -e "${BLUE}Preview:${NC}"
        head -20 "$LATEST_DIGEST"
        echo "..."
        
        # Opcional: enviar por email (descomentar si configuras SMTP)
        # python send_digest_email.py "$LATEST_DIGEST"
    fi
else
    echo -e "${RED}❌ Error generating digest${NC}"
    echo "Check log: $LOG_FILE"
    exit 1
fi

echo ""
echo -e "${BLUE}Completed: $(date)${NC}"
echo -e "${BLUE}======================================${NC}"

# Limpiar cache viejo (> 3 días)
echo "Cleaning old cache..."
python -c "from cache_manager import clear_cache; deleted = clear_cache(72); print(f'Deleted {deleted} old cache files')" 2>/dev/null

# Limpiar logs viejos (> 7 días)
find logs/ -name "digest_*.log" -mtime +7 -delete 2>/dev/null

# Limpiar digests viejos (> 30 días)
find digests/ -name "digest_*.md" -mtime +30 -delete 2>/dev/null

echo ""
echo -e "${GREEN}✅ All done!${NC}"