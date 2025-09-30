import json
import os
import re
from typing import List, Dict, Any, Optional
from llm_providers import get_default_llm
from tools import tool_catalog_text, call_tool
from tools import TOOLS  # para validar nombres de herramientas
from prompts_optimized import AGENT_SYSTEM_PROMPT_COT, select_prompt_for_task, add_step_counter

# Prompt optimizado con Chain of Thought - mejor razonamiento, menos pasos
SYSTEM_PROMPT = AGENT_SYSTEM_PROMPT_COT

class Agent:
    def __init__(self, max_steps: int = 5, auto_web: Optional[bool] = None):
        self.llm = get_default_llm()
        self.max_steps = max_steps
        # Auto-web activado por defecto (desactivable con AGENT_AUTO_WEB=0)
        if auto_web is None:
            env = os.getenv("AGENT_AUTO_WEB", "1").lower()
            self.auto_web = env not in ("0", "false", "off", "no")
        else:
            self.auto_web = bool(auto_web)

    def _messages(self, task: str, observations: List[Dict[str, Any]], current_step: int = 0) -> List[Dict[str, str]]:
        tool_catalog = tool_catalog_text()
        sys = SYSTEM_PROMPT.format(tool_catalog=tool_catalog)
        msgs = [{"role": "system", "content": sys}]
        
        # Añadir contador de pasos para que el LLM sepa cuándo finalizar
        step_warning = ""
        if current_step >= self.max_steps - 3:
            step_warning = f"\n\n⚠️ IMPORTANTE: Estás en el paso {current_step+1}/{self.max_steps}. Si ya tienes información, FINALIZA AHORA con {{\"final\": \"...\"}}.\n"
        
        user_content = f"Tarea: {task}{step_warning}\n\nObservaciones previas:\n"
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

    def _looks_factual(self, task: str) -> bool:
        t = task.strip().lower()
        if not t:
            return False
        # Evita activar si el usuario pide usar herramientas explícitas
        if any(x in t for x in ("usa web_search", "usa read_url_clean", "usa rag_", "usa memory_")):
            return False
        # Heurística básica para preguntas factuales o de estado actual
        patterns = [
            r"\?$",
            r"^\s*¿",
            r"\bqué es\b",
            r"\bquién es\b",
            r"\bcómo funciona\b",
            r"\bdefin(e|ición)\b",
            r"\búltimas noticias\b",
            r"\bqué está pasando\b",
            r"\bestado actual\b",
            r"\btendenc(i|ia|ias|ias)\b",
        ]
        return any(re.search(p, t) for p in patterns)

    def _auto_web_preflight(self, task: str) -> Optional[str]:
        """Intenta resolver preguntas factuales rápidamente con web_search + read_url_clean y finalizar.
        Devuelve el string final si lo logra; si no, devuelve None para continuar con el bucle normal.
        """
        # 1) Buscar
        q = task.strip()
        try:
            ws = call_tool("web_search", {"query": q, "k": 6})
        except Exception:
            ws = {"ok": False}
        if not (isinstance(ws, dict) and ws.get("ok") and ws.get("data", {}).get("results")):
            return None
        results = ws["data"]["results"]
        # 2) Leer top 2-3 URLs
        pre_obs: List[Dict[str, Any]] = [{"tool": "web_search", "result": ws}]
        urls = []
        for r in results:
            u = r.get("url")
            if u and u not in urls:
                urls.append(u)
            if len(urls) >= 3:
                break
        for u in urls:
            rr = call_tool("read_url_clean", {"url": u, "max_chars": 3000})
            pre_obs.append({"tool": "read_url_clean", "result": rr})
        # 3) Pedir respuesta final al LLM en un solo tiro
        aug_task = (
            "Pregunta factual detectada. Usa las observaciones previas para responder.\n"
            "TERMINA con 3-6 viñetas claras en español (una idea por viñeta).\n"
            "Al final añade una sección 'Fuentes:' con 3-5 URLs de las observaciones (si existen)."
        )
        messages = self._messages(f"{task}\n\n{aug_task}", pre_obs)
        raw = self.llm.generate(messages)
        parsed = self._parse_json(raw)
        if parsed and isinstance(parsed, dict) and "final" in parsed:
            return str(parsed.get("final", ""))
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
        # Intento previo: auto-web si aplica
        if getattr(self, "auto_web", False) and self._looks_factual(task):
            try:
                auto = self._auto_web_preflight(task)
                if auto:
                    return auto
            except Exception:
                pass
        observations: List[Dict[str, Any]] = []
        for step in range(self.max_steps):
            messages = self._messages(task, observations, current_step=step)
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
                if result.get("ok"):
                    # Herramientas de memoria
                    if tool_name == "memory_set":
                        return f"OK: guardado {args.get('key')}"
                    elif tool_name == "memory_get":
                        val = result.get("data", {}).get("value")
                        return "" if val is None else str(val)
                    
                    # Herramientas de Fase 3 - Retornar formato limpio directamente
                    elif tool_name == "daily_digest":
                        return result.get("data", {}).get("formatted_digest", "Digest no disponible")
                    elif tool_name == "analyze_topic":
                        return result.get("data", {}).get("formatted_analysis", "Análisis no disponible")
                    elif tool_name == "generate_titles":
                        return result.get("data", {}).get("formatted_titles", "Títulos no disponibles")
                    elif tool_name == "analyze_hype":
                        return result.get("data", {}).get("formatted_hype_analysis", "Análisis no disponible")

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
