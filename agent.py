import json
from typing import List, Dict, Any, Optional
from llm_providers import get_default_llm
from tools import tool_catalog_text, call_tool

SYSTEM_PROMPT = """Eres un agente que resuelve tareas usando herramientas cuando es necesario.
Responde SIEMPRE con un único objeto JSON y nada más, sin comentarios ni texto extra.
Formatos válidos:
- Para usar una herramienta: {{"tool": "<nombre>", "args": {{...}}}}
- Para finalizar con respuesta al usuario: {{"final": "<texto>"}}

Herramientas disponibles:
{tool_catalog}

Si una herramienta falla, puedes intentar otra o reformular los argumentos.
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

    def run(self, task: str) -> str:
        observations: List[Dict[str, Any]] = []
        for _ in range(self.max_steps):
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
            if "final" in parsed:
                return str(parsed["final"])
            if "tool" in parsed and "args" in parsed:
                tool_name = str(parsed["tool"])
                args = parsed["args"] if isinstance(parsed["args"], dict) else {}
                try:
                    result = call_tool(tool_name, args)

                # --- Autocierre para herramientas rápidas ---
                if result.get("ok") and tool_name in ("memory_set", "memory_get"):
                    if tool_name == "memory_set":
                        return f"OK: guardado {args.get('key')}"
                    else:
                        val = result.get("data", {}).get("value")
                        return "" if val is None else str(val)
                # --- fin autocierre ---
                except Exception as e:
                    result = {"ok": False, "data": None, "error": str(e)}
                observations.append({"tool": tool_name, "result": result})
                continue
            return f"[agent] Formato no reconocido: {parsed}"
        return "[agent] Se alcanzó el máximo de pasos sin respuesta final."
