#!/bin/bash
# Helper script para configurar cron job

echo "🔧 Configuración de Cron para AI Agent"
echo "======================================"
echo ""
echo "Este script te ayudará a configurar la ejecución automática del digest."
echo ""

# Path completo al script
SCRIPT_PATH="/Users/sebastianr/Downloads/ai-agent-starter/run_daily_digest.sh"
LOG_PATH="/Users/sebastianr/Downloads/ai-agent-starter/logs/cron.log"

# Verificar que el script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: Script no encontrado en $SCRIPT_PATH"
    exit 1
fi

echo "📋 Opciones de Frecuencia:"
echo ""
echo "1. Cada 6 horas (00:00, 06:00, 12:00, 18:00) - Recomendado"
echo "2. 4 veces al día (06:00, 12:00, 18:00, 00:00)"
echo "3. Una vez al día (08:00)"
echo "4. Cada hora (para testing)"
echo "5. Personalizado"
echo ""

read -p "Selecciona una opción (1-5): " option

case $option in
    1)
        CRON_SCHEDULE="0 */6 * * *"
        DESC="cada 6 horas"
        ;;
    2)
        CRON_SCHEDULE="0 6,12,18,0 * * *"
        DESC="a las 6am, 12pm, 6pm, 12am"
        ;;
    3)
        CRON_SCHEDULE="0 8 * * *"
        DESC="todos los días a las 8am"
        ;;
    4)
        CRON_SCHEDULE="0 * * * *"
        DESC="cada hora"
        ;;
    5)
        echo ""
        echo "Formato cron: minuto hora día mes día_semana"
        echo "Ejemplo: 0 8 * * * = todos los días a las 8am"
        read -p "Introduce tu schedule: " CRON_SCHEDULE
        DESC="personalizado: $CRON_SCHEDULE"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

# Crear el cron job
CRON_JOB="$CRON_SCHEDULE $SCRIPT_PATH >> $LOG_PATH 2>&1"

echo ""
echo "📝 Cron job a crear:"
echo "   $CRON_JOB"
echo ""
echo "   Descripción: Se ejecutará $DESC"
echo ""

read -p "¿Confirmas la configuración? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ Cancelado"
    exit 0
fi

# Agregar al crontab
(crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH"; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cron job configurado exitosamente!"
    echo ""
    echo "📊 Cron jobs activos:"
    crontab -l | grep "$SCRIPT_PATH"
    echo ""
    echo "💡 Comandos útiles:"
    echo "   Ver cron jobs: crontab -l"
    echo "   Editar cron: crontab -e"
    echo "   Eliminar cron: crontab -r"
    echo "   Ver logs: tail -f $LOG_PATH"
    echo ""
    echo "🎉 ¡Todo listo! El digest se generará automáticamente $DESC"
else
    echo "❌ Error al configurar cron"
    exit 1
fi