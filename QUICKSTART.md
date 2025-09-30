# 🚀 Quick Start - Sistema de Investigación de Contenido IA

## ⚡ Start Here

### **1. Instalación Rápida**

```bash
# Clonar/navegar al proyecto
cd ai-agent-starter

# Instalar dependencias
pip install -r requirements.txt

# Configurar API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### **2. Prueba Rápida (30 segundos)**

```bash
# Test de features avanzadas
python advanced_features.py
```

**Output esperado:** Análisis completo de un tema de ejemplo con score, títulos y recomendaciones.

### **3. Ejemplos Interactivos**

```bash
# Ejecutar ejemplos guiados
python example_usage.py

# Opciones:
# 1. Quick Hype Check - Detecta si un tema es hype o sustancia
# 2. Find Content Gaps - Encuentra oportunidades no cubiertas
# 3. Generate Viral Titles - Genera títulos optimizados
# 4. Intelligent Scoring - Compara múltiples temas
# 5. Comprehensive Analysis - Análisis completo de un tema
# 6. Batch Workflow - Procesa múltiples temas
# 7. Run ALL - Ejecuta todos los ejemplos
```

### **4. Generar Digest Diario**

```bash
# Modo rápido (30-60 seg, sin batch)
python daily_digest_optimized.py --no-batch --hours 24

# Modo completo (5-10 min, con análisis avanzado)
python daily_digest_optimized.py

# Output: digests/digest_YYYYMMDD.md
```

---

## 📊 ¿Qué Obtengo?

### **Por cada tema analizado:**

```
### 1. 🔥 Topic Title Here
**Score:** 87.3/100 | **Novelty:** 0.95 | **Priority:** HIGH

💡 🔥 Tema excelente - Crear video ASAP

[Análisis detallado del contenido...]

**📊 Hype Analysis:**
- Substance: 8.5/10
- Verdict: substance
- ✅ Green flags: data-driven, technical details

**✏️ Video Title Ideas:**
1. "California Just Changed AI Forever" (viral: 9/10)
2. "What AI Companies Must Know Now" (viral: 8/10)

**🎨 Thumbnail Ideas:** 
- California flag with AI symbols
- Split screen before/after comparison
```

---

## 🎯 Casos de Uso Comunes

### **Creador de YouTube**
```python
from daily_digest_optimized import generate_daily_digest

# Genera digest del día
result = generate_daily_digest(hours_back=24)

# Encuentra temas HIGH priority
high_priority = [
    t for t in result['stats']['novel_topics'] 
    if t.get('priority') == 'high'
]

# Usa los títulos generados
for topic in high_priority[:3]:
    print(topic['video_titles'][0]['title'])
```

### **Investigador/Newsletter**
```python
# Digest semanal completo
result = generate_daily_digest(
    hours_back=168,  # 7 días
    max_topics=50,
    use_advanced_features=True
)

# Markdown listo para publicar
newsletter = open(result['filepath']).read()
```

### **Análisis de un Tema Específico**
```python
from advanced_features import comprehensive_topic_analysis

result = comprehensive_topic_analysis(
    topic="GPT-5 Release",
    content="OpenAI announced...",
    novelty_score=0.95,
    analyze_all=True
)

print(f"Score: {result['score']['final_score']}/100")
print(f"Best Title: {result['titles']['titles'][0]['title']}")
```

---

## 🎨 Sistema de Scoring

**Score Final (0-100) = Promedio Ponderado:**
- **35%** Novelty - ¿Qué tan nuevo es el tema?
- **30%** Substance - ¿Tiene contenido real o solo hype?
- **25%** Opportunity - ¿Está saturado el mercado?
- **10%** Timing - ¿Es el momento adecuado?

**Prioridades:**
- 🔥 **HIGH** (75-100): Crear contenido ASAP
- 👍 **MEDIUM** (50-74): Considerar para próximos videos
- ⏸️ **LOW** (0-49): Buscar alternativas mejores

---

## ⚙️ Configuración Avanzada

### **Ajustar Pesos del Scoring**

Edita `advanced_features.py` línea 342:

```python
weights = {
    'novelty': 0.35,      # Aumenta si valoras novedad
    'substance': 0.30,    # Aumenta si evitas hype
    'opportunity': 0.25,  # Aumenta si evitas temas saturados
    'timing': 0.10        # Aumenta si timing es crítico
}
```

### **Ajustar Threshold de Novelty**

Edita `daily_digest_optimized.py` línea 84:

```python
threshold=0.75  # 0.5 = más permisivo, 0.9 = más estricto
```

### **Personalizar Títulos**

Edita `advanced_features.py` línea 210-211:

```python
target_audience = "desarrolladores y entusiastas de IA"
style = "informativo y atractivo"
```

---

## 💰 Costos y Optimización

### **Costos Aproximados:**
- Digest sin batch: ~$0.10-0.20 (rápido)
- Digest con batch: ~$0.05-0.10 (tarda más)
- Con advanced features: +$0.02-0.05

### **Optimizaciones Activas:**
- ✅ Cache: 70-80% ahorro
- ✅ Batch API: 50% ahorro
- ✅ Novelty filter: Evita duplicados

### **Recomendaciones:**
```bash
# Desarrollo/Testing (rápido y barato)
python daily_digest_optimized.py --no-batch --no-advanced

# Producción diaria (óptimo)
python daily_digest_optimized.py --hours 24

# Análisis profundo (completo pero costoso)
python daily_digest_optimized.py --hours 168
```

---

## 🔄 Automatización

### **macOS/Linux (cron):**
```bash
# Editar crontab
crontab -e

# Ejecutar cada día a las 8am
0 8 * * * cd /path/to/ai-agent-starter && python daily_digest_optimized.py
```

### **Windows (Task Scheduler):**
1. Abrir Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 8:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `daily_digest_optimized.py`
   - Start in: `C:\path\to\ai-agent-starter`

---

## 🐛 Troubleshooting

### **Error: "api_key must be set"**
```bash
# Verificar .env
cat .env

# Debe contener:
OPENAI_API_KEY=sk-...
```

### **Batch API tarda demasiado**
```bash
# Usar sin batch
python daily_digest_optimized.py --no-batch
```

### **Demasiados temas HIGH priority**
```bash
# Aumentar threshold de novelty
# Editar daily_digest_optimized.py línea 84
threshold=0.85  # Más estricto
```

### **Títulos no son relevantes**
```bash
# Personalizar en advanced_features.py
target_audience = "tu audiencia específica"
style = "tu estilo preferido"
```

---

## 📚 Documentación Completa

- **FASE3_README.md** - Documentación detallada
- **example_usage.py** - Ejemplos interactivos
- **advanced_features.py** - Código fuente comentado
- **daily_digest_optimized.py** - Sistema principal

---

## 🎓 Flujo de Trabajo Recomendado

### **1. Mañana (8:00 AM)**
```bash
# Genera digest del día
python daily_digest_optimized.py --hours 24
```

### **2. Revisión (9:00 AM)**
```bash
# Lee el digest
cat digests/digest_$(date +%Y%m%d).md

# Identifica temas HIGH priority
```

### **3. Análisis Profundo (10:00 AM)**
```python
# Analiza temas específicos
from advanced_features import comprehensive_topic_analysis

for topic in high_priority_topics:
    result = comprehensive_topic_analysis(topic, analyze_all=True)
    # Usa títulos y recomendaciones
```

### **4. Creación de Contenido (11:00 AM+)**
- Usa títulos sugeridos
- Revisa análisis de hype para validar
- Considera gaps de competencia
- Implementa ideas de thumbnails

---

## 🚀 Siguientes Pasos

1. ✅ Probar con `python example_usage.py`
2. ✅ Generar primer digest con `python daily_digest_optimized.py --no-batch`
3. ✅ Revisar output en `digests/`
4. ✅ Personalizar scoring y títulos
5. ✅ Automatizar con cron/Task Scheduler
6. ✅ Integrar en workflow diario

---

## 💡 Tips Pro

### **Maximizar ROI:**
```bash
# Usa cache agresivamente (reduce costos 70-80%)
# El cache es válido por 6 horas por defecto
```

### **Priorizar Calidad:**
```python
# Filtra solo HIGH priority
high_only = [t for t in topics if t['priority'] == 'high']
```

### **Experimentar con Títulos:**
```python
# Genera múltiples variaciones
for i in range(3):
    titles = generate_video_titles(topic)
    # Selecciona el mejor según tu estilo
```

### **Monitorear Trends:**
```bash
# Ejecuta varias veces al día
python daily_digest_optimized.py --hours 6  # Cada 6 horas
```

---

**🎉 ¡Listo! Ya puedes empezar a usar el sistema.**

Para más detalles, consulta **FASE3_README.md**