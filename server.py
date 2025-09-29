# server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os, json

# 1) Carga variables de entorno (.env en local, Environment en Render)
load_dotenv()

from agent import Agent  # importa después de load_dotenv

app = FastAPI(title="AI Agent Starter API", version="0.1.0")
# CORS permisivo por si la UI se sirve desde otro origen en Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)
agent = Agent(max_steps=8)

# ----------------- Memoria de chat (archivos JSONL) 
# -----------------
# CHAT_DIR es la carpeta donde guardamos los historiales. En 
# Render será /data/chats
CHAT_DIR = os.getenv("CHAT_DIR", "chats")
os.makedirs(CHAT_DIR, exist_ok=True)

def _chat_path(sid: str) -> str:
    return os.path.join(CHAT_DIR, f"{sid}.jsonl")

def chat_load(sid: str):
    """Lee el historial (lista de dicts: {'role': 
'user'|'assistant', 'content': str})"""
    if not sid: return []
    p = _chat_path(sid)
    if not os.path.exists(p): return []
    with open(p, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def chat_append(sid: str, role: str, content: str):
    """Agrega una línea al historial"""
    if not sid: return
    p = _chat_path(sid)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps({"role": role, "content": content}, 
ensure_ascii=False) + "\n")

def chat_reset(sid: str):
    """Borra el historial de una sesión"""
    if not sid: return
    p = _chat_path(sid)
    if os.path.exists(p): os.remove(p)

# ----------------- API: /run con memoria -----------------
class RunReq(BaseModel):
    task: str                # lo que le pides al agente
    session_id: str | None = None  # id de conversación (lo manda el front)
    reset: bool = False      # si true, borra la conversación

class RunResp(BaseModel):
    result: str

@app.post("/run", response_model=RunResp)
def run(req: RunReq):
    # 1) ¿pidieron reset?
    if req.reset and req.session_id:
        chat_reset(req.session_id)

    # 2) Cargar últimos turnos para dar contexto (memoria corta)
    history = chat_load(req.session_id)[-8:] if req.session_id else []
    context = "\n".join(f"{m['role']}: {m['content']}" for m in 
history)

    # 3) Inyectar contexto al prompt actual solo si existe
    if context.strip():
        aug_task = (
            "Usa el contexto de conversación (si ayuda) para responder.\n"
            "Contexto (turnos recientes):\n" + context + "\n\n"
            "Tarea actual:\n" + req.task
        )
    else:
        aug_task = req.task

# 4) Ejecutar el agente
    try:
        out = agent.run(aug_task)
    except Exception as e:
        # Nunca devolvemos 500 al front: mejor un mensaje legible
        out = f"Error al ejecutar el agente: {str(e)}"

    # 5) Guardar turno actual
    if req.session_id:
        chat_append(req.session_id, "user", req.task)
        chat_append(req.session_id, "assistant", out)

    return RunResp(result=out)

# ----------------- Servir archivos estáticos -----------------
# Montar la carpeta static para servir el HTML/CSS/JS
try:
    app.mount("/assets", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass  # Si no existe la carpeta, continuar sin ella

@app.get("/")
async def home():
    """Sirve el archivo index.html desde la carpeta static"""
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_path):
        return FileResponse(static_path)
    # Fallback si no existe el archivo
    return {"message": "UI not found. API available at /docs"}

# ----------------- Ruta de fallback legacy (comentada para referencia) -----------------
# Si necesitas volver al HTML inline, descomenta esto y comenta el código arriba
"""
@app.get("/old", response_class=HTMLResponse)
def home_legacy():
    return '''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" 
content="width=device-width,initial-scale=1">
<title>Mi primer agente</title>
<style>
  :root{
    --bg:#0b1020; --panel:#0e1429; --text:#e6e8ee;
    --assist:#111827; --user:#1f6feb; --muted:#94a3b8;
    --ring:#1f2937;
  }
  *{box-sizing:border-box}
  
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 
system-ui,-apple-system,Segoe UI,Roboto}
  .wrap{max-width:920px;margin:36px auto;padding:0 16px}
  h1{display:flex;gap:10px;align-items:center;margin:0 0 8px}
  h1 .logo{font-size:28px}
  p.sub{margin:0 0 18px;color:var(--muted)}
  .chat{background:var(--panel);border:1px solid 
var(--ring);border-radius:16px;padding:16px;height:60vh;overflow:auto;display:flex;flex-direction:column;gap:12px}
  .msg{display:flex}
  .msg.user{justify-content:flex-end}
  .bubble{max-width:75%;padding:10px 
12px;border-radius:14px;word-wrap:break-word;white-space:pre-wrap}
  .msg.assistant 
.bubble{background:var(--assist);color:#e5e7eb;border-top-left-radius:6px}
  .msg.user 
.bubble{background:var(--user);color:#fff;border-top-right-radius:6px}
  .typing 
.dot{display:inline-block;width:6px;height:6px;margin-right:4px;border-radius:50%;background:#cbd5e1;animation:b 
1.2s infinite}
  .typing .dot:nth-child(2){animation-delay:.15s}
  .typing .dot:nth-child(3){animation-delay:.3s}
  @keyframes b{0%,80%,100%{opacity:.2}40%{opacity:1}}
  .composer{display:flex;gap:8px;margin-top:12px}
  
textarea{flex:1;min-height:60px;max-height:150px;padding:10px;border-radius:12px;border:1px 
solid 
var(--ring);background:#0a0f1f;color:var(--text);outline:none}
  button{padding:10px 
14px;border:0;border-radius:12px;background:#111;color:#fff;cursor:pointer}
  button:disabled{opacity:.6;cursor:default}
  .hint{font-size:13px;color:var(--muted);margin-top:6px}
</style>
</head>
<body>
  <div class="wrap">
    <h1><span class="logo">🧠</span>Mi primer agente</h1>
    <p class="sub">Escribe tu mensaje y pulsa <b>Ejecutar</b>. 
Tip: <code>Usa calculator con expression "123*45+7" y TERMINA con 
el número.</code></p>

    <div id="chat" class="chat"></div>

    <div class="composer">
      <textarea id="task" placeholder="Escribe aquí... (Enter: 
enviar, Shift+Enter: salto de línea)"></textarea>
      <button id="send">Ejecutar</button>
    </div>
    <div class="hint">También tienes la API en 
<code>/docs</code>.</div>
  </div>

<script>
const chat = document.getElementById('chat');
const task = document.getElementById('task');
const send = document.getElementById('send');

// session id persistente en el navegador
let sid = localStorage.getItem('sid');
if(!sid){
  sid = (crypto.randomUUID ? crypto.randomUUID() : 
String(Date.now()));
  localStorage.setItem('sid', sid);
}

// botón de reset
const resetBtn = document.createElement('button');
resetBtn.textContent = 'Nueva conversación';
resetBtn.style.marginLeft = '8px';
document.querySelector('.composer').appendChild(resetBtn);

function addMsg(role, text){
  const row = document.createElement('div');
  row.className = 'msg ' + role;
  const b = document.createElement('div');
  b.className = 'bubble';
  b.textContent = text;
  row.appendChild(b);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
  return row;
}

function addTyping(){
  const row = document.createElement('div');
  row.className = 'msg assistant';
  const b = document.createElement('div');
  b.className = 'bubble typing';
  b.innerHTML = '<span class="dot"></span><span 
class="dot"></span><span class="dot"></span>';
  row.appendChild(b);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;
  return row;
}

async function sendTask(reset=false){
  const t = task.value.trim();
  if(!t && !reset) return;

  if(!reset){ addMsg('user', t); task.value = ''; }
  task.disabled = true; send.disabled = true; resetBtn.disabled = true;

  const typing = addTyping();
  try{
    const body = reset ? {task:"(reset)", session_id:sid, reset:true} : {task:t, session_id:sid, reset:false};
    const apiUrl = window.location.origin + '/run';
    const r = await fetch(apiUrl, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    let text;
    if(!r.ok){
      const raw = await r.text();
      text = 'HTTP ' + r.status + ': ' + (raw?.slice(0,300) || 'Error');
    }else{
      const ct = r.headers.get('content-type') || '';
      if(ct.includes('application/json')){
        const j = await r.json();
        text = (j && typeof j.result === 'string') ? j.result : JSON.stringify(j);
      }else{
        text = await r.text() || 'OK';
      }
    }
    typing.remove();
    if(!reset) addMsg('assistant', text);
    else addMsg('assistant', 'Conversación reiniciada ✅');
  }catch(e){
    typing.remove();
    addMsg('assistant', 'Error de red: ' + (e?.message || e));
  }finally{
    task.disabled = false; send.disabled = false; resetBtn.disabled = false; task.focus();
  }
}

send.onclick = ()=>sendTask(false);
task.addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendTask(false); }});
resetBtn.onclick = ()=>sendTask(true);
</script>
</body>
</html>'''
"""

@app.get("/health")
def health():
    return {"ok": True, "service": "ai-agent-starter", "version": 
"0.2.0"}

