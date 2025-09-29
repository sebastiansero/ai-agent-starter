import os
import json
import requests
from typing import List, Dict, Optional

class BaseLLM:
    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
        raise NotImplementedError

def _env_get(key: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(key, default)
    return v if v and v.strip() else None

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or _env_get("OPENAI_API_KEY")
        self.model = model or _env_get("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurada")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

class OllamaLLM(BaseLLM):
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or _env_get("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or _env_get("OLLAMA_MODEL", "llama3.1:8b")

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        if "messages" in data and data["messages"]:
            return data["messages"][-1].get("content", "")
        return ""
        
def get_default_llm() -> BaseLLM:
    """Prioriza OpenAI si hay API key; si no, usa Ollama."""
    if _env_get("OPENAI_API_KEY"):
        return OpenAILLM()
    return OllamaLLM()
