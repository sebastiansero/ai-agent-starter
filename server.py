# server.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()  # si usas variables de entorno como OPENAI_API_KEY

from agent import Agent  # importa después de load_dotenv

app = FastAPI(title="AI Agent Starter API", version="0.1.0")
agent = Agent(max_steps=8)

class RunReq(BaseModel):
    task: str

class RunResp(BaseModel):
    result: str

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" 
content="width=device-width,initial-scale=1">
<title>Mi primer agente</title>
<style>
  body{font-family:system-ui,-apple-system,Segoe 
UI,Roboto;max-width:720px;margin:40px auto;padding:0 16px}
  textarea{width:100%;padding:10px}
  button{padding:10px 
14px;border:0;border-radius:10px;background:#111;color:#fff;cursor:pointer}
  
pre{background:#0b1020;color:#bde4a8;padding:12px;border-radius:10px;white-space:pre-wrap}
</style>
</head>
<body>
  <h1>🧠 Mi primer agente</h1>
  <p>Escribe una tarea y presiona <b>Ejecutar</b>. Ejemplo: 
<code>Usa calculator con expression "123*45+7" y TERMINA con el 
número.</code></p>
  <textarea id="task" rows="4">Usa calculator con expression 
"123*45+7" y TERMINA con el número.</textarea><br><br>
  <button id="run">Ejecutar</button>
  <h3>Salida</h3>
  <pre id="out">—</pre>
<script>
document.getElementById('run').onclick = async () => {
  const task = document.getElementById('task').value;
  const out = document.getElementById('out');
  out.textContent = 'Ejecutando...';
  try {
    const r = await fetch('/run', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ task })
    });
    const j = await r.json();
    out.textContent = JSON.stringify(j, null, 2);
  } catch(e){
    out.textContent = 'Error: ' + e;
  }
};
</script>
</body></html>
"""

@app.get("/health")
def health():
    return {"ok": True, "service": "ai-agent-starter", "version": 
"0.1.0"}

@app.post("/run", response_model=RunResp)
def run(req: RunReq):
    result = agent.run(req.task)
    return RunResp(result=result)

