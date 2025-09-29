import json
from typing import List, Dict, Any, Optional
from llm_providers import get_default_llm
from tools import tool_catalog_text, call_tool
from tools import TOOLS  # para validar nombres de herramientas

SYSTEM_PROMPT = """Eres un agente que resuelve tareas usando herramientas cuando es necesario.
Responde SIEMPRE con un único objeto JSON y nada más, sin comentarios ni texto extra.
Formatos válidos (usa EXACTAMENTE estos):
- Para usar una herramienta: {{"tool": "<nombre>", "args": {{ ... }} }}
- Para finalizar con respuesta al usuario: {{"final": "<texto>"}}

NUNCA devuelvas formatos alternativos como {{"<herramienta>": {{...}}}} ni listas/strings sueltos.
Si una herramienta falla una o dos veces, evita bucles: finaliza con una explicación breve del problema.
Si la instrucción contiene "TERMINA", prioriza finalizar en ≤ 3 pasos.
Para consultas del tipo "¿qué está pasando con <tema>?", "tendencias", "últimas noticias" o "estado actual de <tema>":
- PRIORIZA usar la herramienta web_trend_scan con argumentos razonables (topic, k, max_articles).
- Luego FINALIZA con 3-6 viñetas claras en español con insights, e incluye al final una sección "Fuentes:" listando 3-5 URLs.

Herramientas disponibles:
{tool_catalog}

No expliques el JSON, solo devuélvelo.
"""

class Agent:
    def __init__(self, max_steps: int = 5):
        self.llm = get_default_llm()
        self.max_steps = max_steps

    def _messages(self, task: str, observations: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        tool_catalog = tool_catalog_text()
        sys = SYSTEM_PROMPT.format(tool_catalog=tool_catalog)
        msgs = [{"role": "system", "content": sys}]
        user_content = f"Tarea: {task}\n\nObservaciones previas:\n"
        if observations:
            for i, obs in enumerate(observations, start=1):
                snippet = json.dumps(obs["result"], ensure_ascii=False)
                if len(snippet) > 1200:
                    snippet = snippet[:1200] + "..."
                user_content += f"- obs#{i} de {obs['tool']}: {snippet}\n"
        else:
            user_content += "- (ninguna)\n"
        msgs.append({"role": "user", "content": user_content})
        return msgs

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        # Extrae el primer objeto JSON del texto
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
        except Exception:
            return None
        return None

    def _coerce_tool_call(self, parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Acepta formatos alternativos y los normaliza al esquema {'tool':..., 'args':{}}.
        - {"<tool>": {...}} → {"tool":"<tool>", "args": {...}}
        - {"tool": "<tool>"} (sin args) → args {}
        """
        if not isinstance(parsed, dict):
            return None
        # Caso 1: un único par clave/valor cuyo nombre es una herramienta
        if len(parsed) == 1:
            only_key = next(iter(parsed.keys()))
            if only_key in TOOLS:
                args = parsed.get(only_key)
                return {"tool": only_key, "args": args if isinstance(args, dict) else {}}
        # Caso 2: trae 'tool' pero sin args válidos
        if "tool" in parsed and "args" not in parsed:
            t = str(parsed.get("tool"))
            if t in TOOLS:
                return {"tool": t, "args": {}}
        return None

    def run(self, task: str) -> str:
        observations: List[Dict[str, Any]] = []
        for step in range(self.max_steps):
            messages = self._messages(task, observations)
            raw = self.llm.generate(messages)
            parsed = self._parse_json(raw)
            if not parsed:
                # Recordatorio para que devuelva JSON válido
                messages.append({"role": "user", "content": "Recuerda: solo un objeto JSON válido. Si puedes finalizar, usa {'final': '...'}."})
                raw = self.llm.generate(messages)
                parsed = self._parse_json(raw)
                if not parsed:
                    return f"[agent] No pude parsear JSON del modelo: {raw[:500]}"
            # Final directo
            if isinstance(parsed, dict) and "final" in parsed:
                return str(parsed.get("final", ""))

            # Normaliza llamadas de herramienta con formatos alternativos
            if not (isinstance(parsed, dict) and "tool" in parsed and "args" in parsed):
                coerced = self._coerce_tool_call(parsed if isinstance(parsed, dict) else {})
                if coerced:
                    parsed = coerced

            # Llamada a herramienta
            if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                tool_name = str(parsed["tool"]) if parsed.get("tool") is not None else ""
                args = parsed["args"] if isinstance(parsed["args"], dict) else {}
                try:
                    result = call_tool(tool_name, args)
                except Exception as e:
                    result = {"ok": False, "data": None, "error": str(e)}

                # Autocierre para herramientas rápidas
                if result.get("ok") and tool_name in ("memory_set", "memory_get"):
                    if tool_name == "memory_set":
                        return f"OK: guardado {args.get('key')}"
                    else:
                        val = result.get("data", {}).get("value")
                        return "" if val is None else str(val)

                observations.append({"tool": tool_name, "result": result})

                # Si la herramienta falló con un error claro, evita bucles innecesarios
                if not result.get("ok"):
                    err = str(result.get("error", ""))
                    # Errores típicos de dependencias externas (e.g., embeddings)
                    if any(tok in err for tok in ("OpenAI", "embeder", "SDK no disponible")):
                        return f"No pude completar la tarea por un error de dependencia: {err}"

                # Si repetimos demasiadas veces con errores, forzar cierre útil
                recent = observations[-3:]
                if len(recent) >= 2 and all(not obs.get("result", {}).get("ok") for obs in recent):
                    # Finaliza con mensaje claro para evitar loops
                    return f"No pude completar la tarea por errores de herramientas: {recent[-1]['result'].get('error','desconocido')}"
                continue

            # Formato no reconocido: añade observación y reintenta, no abortes al instante
            observations.append({"tool": "(parser)", "result": {"ok": False, "data": None, "error": f"Formato no reconocido: {parsed}"}})
            # En el último paso, devuelve el error
            if step == self.max_steps - 1:
                return f"[agent] Formato no reconocido: {parsed}"
            continue
        return "[agent] Se alcanzó el máximo de pasos sin respuesta final."
