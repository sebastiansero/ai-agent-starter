import re, os, json, requests
from datetime import datetime, timezone

# ----------------- Utilidades -----------------
class ToolError(Exception):
    pass

def _ok(status, data, error=""):
    return {"ok": status, "data": data, "error": error}

# ----------------- Herramientas base -----------------
def calculator(args):
    """Calculadora segura: (+,-,*,/,**,(),.)"""
    expr = str(args.get("expression", ""))
    if not expr:
        return _ok(False, None, "Falta 'expression'")
    if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s]+", expr):
        return _ok(False, None, "Caracteres no permitidos")
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        return _ok(True, result, "")
    except Exception as e:
        return _ok(False, None, f"Error de cálculo: {e}")

def now(args):
    return _ok(True, datetime.now(timezone.utc).isoformat(), "")

def read_url(args):
    url = args.get("url")
    max_chars = int(args.get("max_chars", 2000))
    if not url or not isinstance(url, str):
        return _ok(False, None, "Falta 'url'")
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return _ok(True, r.text[:max_chars], "")
    except Exception as e:
        return _ok(False, None, f"Error al leer URL: {e}")

# ----------------- Memoria (archivo JSON) -----------------
MEMORY_PATH = "memory.json"

def _mem_load():
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _mem_save(data):
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def memory_set(args):
    key = str(args.get("key", "")).strip()
    value = args.get("value", None)
    if not key:
        return _ok(False, None, "Falta 'key'")
    data = _mem_load()
    data[key] = value
    _mem_save(data)
    return _ok(True, {"saved": {key: value}}, "")

def memory_get(args):
    key = str(args.get("key", "")).strip()
    if not key:
        return _ok(False, None, "Falta 'key'")
    data = _mem_load()
    return _ok(True, {"value": data.get(key)}, "")

# ----------------- Registro de herramientas -----------------
TOOLS = {
    "calculator": ("Evalúa una expresión aritmética. Args: {'expression':'3*7+2'}", calculator),
    "now": ("Devuelve la hora actual en ISO-8601 UTC. Args: {}", now),
    "read_url": ("Lee texto de una URL. Args: {'url':'https://...','max_chars':2000}", read_url),
    "memory_set": ("Guarda un par clave/valor. Args: {'key':'k','value':<json>}", memory_set),
    "memory_get": ("Lee un valor por clave. Args: {'key':'k'}", memory_get),
}

def tool_catalog_text():
    return "\n".join([f"- {n}: {d}" for n,(d,_) in TOOLS.items()])

def call_tool(name, args):
    if name not in TOOLS:
        raise ToolError(f"Herramienta desconocida: {name}")
    _, fn = TOOLS[name]
    return fn(args)


 

