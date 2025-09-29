from fastapi import FastAPI
from pydantic import BaseModel
from agent import Agent

app = FastAPI(title="AI Agent Starter API", version="0.1.0")
agent = Agent(max_steps=8)

class RunReq(BaseModel):
    task: str

class RunResp(BaseModel):
    result: str

@app.post("/run", response_model=RunResp)
def run(req: RunReq):
    result = agent.run(req.task)
    return RunResp(result=result)
