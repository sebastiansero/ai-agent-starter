# 🚀 Guía de Producción - Sistema Optimizado

**Sistema validado y listo para despliegue**

---

## ✅ Pre-requisitos Completados

- [x] Todos los tests pasando
- [x] Agente funcionando con CoT prompts
- [x] Cache operacional (3 archivos activos)
- [x] Novelty checker listo
- [x] Batch processing disponible
- [x] Scripts de automatización creados

---

## 🎯 Opción A: Automatización con Cron

### 1. Configurar Cron Job

```bash
# Editar crontab
crontab -e

# Agregar una de estas opciones:

# Opción 1: Cada 6 horas (recomendado)
0 */6 * * * /Users/sebastianr/Downloads/ai-agent-starter/run_daily_digest.sh >> /Users/sebastianr/Downloads/ai-agent-starter/logs/cron.log 2>&1

# Opción 2: 4 veces al día (específico)
0 6,12,18,0 * * * /Users/sebastianr/Downloads/ai-agent-starter/run_daily_digest.sh >> /Users/sebastianr/Downloads/ai-agent-starter/logs/cron.log 2>&1

# Opción 3: Una vez al día (8am)
0 8 * * * /Users/sebastianr/Downloads/ai-agent-starter/run_daily_digest.sh >> /Users/sebastianr/Downloads/ai-agent-starter/logs/cron.log 2>&1
```

### 2. Verificar Configuración

```bash
# Ver cron jobs activos
crontab -l

# Test manual del script
cd /Users/sebastianr/Downloads/ai-agent-starter
./run_daily_digest.sh
```

### 3. Monitorear Ejecución

```bash
# Ver logs en tiempo real
tail -f /Users/sebastianr/Downloads/ai-agent-starter/logs/cron.log

# Ver digests generados
ls -lht /Users/sebastianr/Downloads/ai-agent-starter/digests/

# Ver último digest
cat digests/digest_$(date +%Y%m%d).md
```

---

## 📊 Uso del Agente en Tu Workflow

### Integración en Python

```python
#!/usr/bin/env python
# tu_script.py

from dotenv import load_dotenv
load_dotenv()

from agent import Agent
from novelty_checker import check_novelty, add_to_history

# 1. Investigar un tema
agent = Agent(max_steps=5)
result = agent.run("¿Qué está pasando con GPT-5?")
print(result)

# 2. Verificar si es novedoso
topic = "GPT-5 lanzamiento oficial"
novelty = check_novelty(topic)

if novelty['is_novel'] and novelty['novelty_score'] > 0.8:
    print(f"✅ Tema nuevo con score {novelty['novelty_score']:.2f}")
    # Crear tu video aquí
    
    # 3. Marcar como cubierto
    add_to_history(topic, "Mi Video Sobre GPT-5")
else:
    print(f"⚠️ Tema ya cubierto (similarity: {1 - novelty['novelty_score']:.2f})")
```

### Integración en Bash

```bash
#!/bin/bash
# research_topic.sh

TOPIC="$1"

cd /Users/sebastianr/Downloads/ai-agent-starter
source .venv/bin/activate

# Investigar tema
python -c "
from agent import Agent
agent = Agent()
print(agent.run('$TOPIC'))
" > "research_${TOPIC// /_}.md"

echo "Research saved to research_${TOPIC// /_}.md"
```

---

## 🔄 Workflow Recomendado

### Daily Routine

**Mañana (8am):**
1. Cron ejecuta digest automático
2. Revisa digest en `digests/digest_YYYYMMDD.md`
3. Identifica 3-5 temas más prometedores

**Día:**
4. Para cada tema prometedor:
   - Verifica novelty: `check_novelty(topic)`
   - Si es novel (>0.75): investigar más con agente
   - Decidir si crear video

**Después de grabar:**
5. Marcar tema como cubierto: `add_to_history(topic, video_title)`

**Noche:**
6. Revisar métricas de ahorro
7. Limpiar cache viejo

---

## 📈 Trackear Ahorros

### Script de Métricas

```python
# track_savings.py

from cache_manager import cache_stats
from novelty_checker import get_history_stats
import json
from datetime import datetime

stats = {
    'date': datetime.now().isoformat(),
    'cache': cache_stats(),
    'novelty': get_history_stats(),
}

# Guardar métricas
with open('metrics/daily_stats.json', 'a') as f:
    f.write(json.dumps(stats) + '\n')

print(f"Cache files: {stats['cache']['total_files']}")
print(f"Topics covered: {stats['novelty']['total_topics']}")
```

### Agregar al Cron

```bash
# Cada noche a las 23:00
0 23 * * * cd /Users/sebastianr/Downloads/ai-agent-starter && python track_savings.py
```

---

## 🔔 Notificaciones (Opcional)

### Slack/Discord Webhook

```python
# notify.py

import requests
import os

WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def notify_digest_ready(digest_path):
    with open(digest_path, 'r') as f:
        preview = f.read()[:500]
    
    payload = {
        "text": f"🤖 New AI Digest Ready!\n\n{preview}..."
    }
    
    requests.post(WEBHOOK_URL, json=payload)

# Uso en run_daily_digest.sh:
# python notify.py "$LATEST_DIGEST"
```

### Email Notifications

```python
# send_digest_email.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys

def send_digest(digest_file):
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    to_email = os.getenv('EMAIL_TO')
    
    with open(digest_file, 'r') as f:
        content = f.read()
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = f"AI Digest - {digest_file.split('_')[1].split('.')[0]}"
    
    msg.attach(MIMEText(content, 'plain'))
    
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    
    print(f"✅ Email sent to {to_email}")

if __name__ == '__main__':
    send_digest(sys.argv[1])
```

---

## 🔧 Mantenimiento

### Semanal

```bash
# Limpiar cache viejo
python -c "from cache_manager import clear_cache; print(f'Deleted {clear_cache(168)} files')"

# Ver estadísticas
python -c "from cache_manager import cache_stats; print(cache_stats())"

# Revisar logs
tail -100 logs/cron.log
```

### Mensual

```bash
# Backup de historial de novelty
cp content_history/topics_history.json backups/topics_$(date +%Y%m).json

# Analizar métricas
python analyze_metrics.py

# Actualizar fuentes RSS si es necesario
# Editar ai_content_research.py
```

---

## 📱 Dashboard Simple (Opcional)

### HTML Dashboard

```python
# generate_dashboard.py

from cache_manager import cache_stats
from novelty_checker import get_history_stats
import os

stats = cache_stats()
novelty = get_history_stats()

html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Agent Dashboard</title>
    <style>
        body {{ font-family: Arial; max-width: 800px; margin: 50px auto; }}
        .stat {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>🤖 AI Agent Dashboard</h1>
    
    <div class="stat">
        <h2>💾 Cache</h2>
        <p>Total files: {stats['total_files']}</p>
        <p>Size: {stats['total_size_mb']} MB</p>
    </div>
    
    <div class="stat">
        <h2>🎯 Novelty</h2>
        <p>Topics tracked: {novelty['total_topics']}</p>
        <p>Date range: {novelty.get('date_range_days', 0)} days</p>
    </div>
    
    <div class="stat">
        <h2>📰 Recent Digests</h2>
        <ul>
"""

# Agregar últimos 5 digests
digests = sorted(os.listdir('digests'), reverse=True)[:5]
for d in digests:
    html += f'<li><a href="digests/{d}">{d}</a></li>\n'

html += """
        </ul>
    </div>
</body>
</html>
"""

with open('dashboard.html', 'w') as f:
    f.write(html)

print("✅ Dashboard generado: dashboard.html")
```

---

## 🚨 Troubleshooting Producción

### Problema: Cron no ejecuta

```bash
# Verificar permisos
ls -la run_daily_digest.sh
# Debe ser executable (chmod +x)

# Verificar paths absolutos
# Usa paths completos en crontab

# Ver errores de cron
grep CRON /var/log/syslog  # Linux
tail -f /var/log/system.log | grep cron  # Mac
```

### Problema: API key errors

```bash
# Verificar .env
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Problema: Digests vacíos

```bash
# Verificar fuentes RSS
python -c "from ai_content_research import fetch_all_rss_feeds; r = fetch_all_rss_feeds(48); print(f'Posts: {len(r[\"all_posts\"])}')"

# Ajustar threshold de novelty
# En daily_digest_optimized.py, línea 82:
# novel_topics = filter_novel_topics(topics, threshold=0.60)  # Más permisivo
```

---

## 💡 Best Practices

### DO ✅

1. **Revisar digests diariamente** - No automatices sin revisar
2. **Trackear métricas semanalmente** - Ver ahorro real
3. **Backup historial mensualmente** - Evitar pérdida de datos
4. **Ajustar threshold según necesidad** - Más/menos estricto
5. **Limpiar cache regularmente** - Evitar acumulación

### DON'T ❌

1. **No subir .env a git** - Ya está en .gitignore
2. **No borrar todo el historial** - Perderás track de temas cubiertos
3. **No ejecutar batch sin supervisión inicial** - Test primero
4. **No ignorar warnings de API** - Pueden indicar problemas
5. **No cambiar umbral sin testing** - Prueba antes en dev

---

## 📊 KPIs a Monitorear

### Diarios
- Digests generados correctamente
- Temas novedosos encontrados
- Errores en logs

### Semanales
- Cache hit rate
- Ahorro estimado vs real
- Temas cubiertos vs disponibles

### Mensuales
- Costo total de API
- Ahorros acumulados
- Calidad de contenido generado

---

## 🎯 Próximos Pasos

### Semana 1
- [x] Sistema probado y validado
- [x] Scripts de automatización creados
- [ ] Cron configurado
- [ ] Primer digest automático ejecutado

### Semana 2-4
- [ ] 7+ digests automáticos ejecutados
- [ ] Métricas de ahorro validadas
- [ ] Workflow integrado en proceso de videos
- [ ] Ajustes de threshold si necesario

### Mes 2+
- [ ] Fase 3: Features avanzados
- [ ] Dashboard de métricas
- [ ] Notificaciones automáticas
- [ ] Posible expansión a otros temas

---

## 📞 Soporte y Recursos

### Documentación
- `README_OPTIMIZATIONS.md` - Índice maestro
- `FINAL_SUMMARY.md` - Resumen completo
- `TEST_RESULTS.md` - Resultados de tests
- `QUICK_WINS_README.md` - Guía de optimizaciones

### Comandos Útiles
```bash
# Ver todo el sistema
ls -lah *.py *.sh *.md

# Test rápido
python test_integration.py

# Generar digest manual
python daily_digest_optimized.py --no-batch

# Ver estadísticas
python -c "from cache_manager import cache_stats; print(cache_stats())"
```

---

**🎉 ¡Sistema listo para producción!**

**Status:** ✅ PRODUCTION READY  
**Siguiente acción:** Configurar cron job y ejecutar primer digest automático  
**Soporte:** Revisa documentación o logs en caso de problemas