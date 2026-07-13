"""
最小 LangGraph 示例 — FastAPI 入口

启动方式：
    cd struct-quest-backend
    uvicorn app.minimal_langgraph.api:app --reload --port 8001

测试：
    curl -X POST http://localhost:8001/api/learn \
         -H "Content-Type: application/json" \
         -d '{"subject": "数据结构", "goal": "掌握链表和树的基本操作"}'
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from app.minimal_langgraph.graph import run_minimal_session


app = FastAPI(title="Minimal LangGraph Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求/响应模型 ──

class LearnRequest(BaseModel):
    subject: str
    goal: str


# ── 接口 ──

@app.get("/")
async def root():
    """健康检查"""
    return {
        "service": "Minimal LangGraph Demo",
        "flow": "ProfileAgent → PlannerAgent",
        "endpoints": ["/api/learn"],
    }


@app.post("/api/learn")
async def learn(req: LearnRequest) -> Dict[str, Any]:
    """
    核心接口：运行 ProfileAgent + PlannerAgent 流水线

    返回学生画像 + 学习路径的 JSON
    """
    result = run_minimal_session(subject=req.subject, goal=req.goal)

    return {
        "subject": result.get("subject"),
        "goal": result.get("goal"),
        "profile": result.get("profile"),
        "plan": result.get("plan"),
        "agent_logs": result.get("messages"),
    }
