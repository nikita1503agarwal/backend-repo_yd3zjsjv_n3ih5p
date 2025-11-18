import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx

from database import db, create_document, get_documents
from schemas import Chatmessage, Research, Plan, Roleplay

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

app = FastAPI(title="AI Tools Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: str = "llama3.1:8b"
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    created_at: datetime


@app.get("/test")
async def test_connection():
    # Database test
    _ = db.name  # Access to verify import
    return {"status": "ok", "database": True}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    user_msg = Chatmessage(session_id=payload.session_id, role="user", content=payload.message)
    await create_document("chatmessage", user_msg.model_dump())

    # Call Ollama chat
    url = f"{OLLAMA_BASE_URL}/api/generate"
    prompt = payload.message
    data = {"model": payload.model, "prompt": prompt, "stream": False}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=data)
            r.raise_for_status()
            res = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    text = res.get("response") or res.get("message", {}).get("content") or ""

    if not text:
        raise HTTPException(status_code=500, detail="No response from model")

    asst_msg = Chatmessage(session_id=payload.session_id, role="assistant", content=text)
    await create_document("chatmessage", asst_msg.model_dump())

    return ChatResponse(session_id=payload.session_id, reply=text, created_at=datetime.utcnow())


class ResearchRequest(BaseModel):
    session_id: str
    topic: str
    depth: int = 3
    model: str = "llama3.1:8b"


@app.post("/research")
async def deep_research_endpoint(payload: ResearchRequest):
    # Store research intent
    research = Research(session_id=payload.session_id, topic=payload.topic, parameters={"depth": payload.depth})
    await create_document("research", research.model_dump())

    # Very simple research draft via Ollama
    prompt = (
        "You are a meticulous research assistant. Produce a structured research brief with: "
        "Key points, Sources to check, and Next steps about the topic: '" + payload.topic + "'. "
        f"Aim for depth level {payload.depth}."
    )

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                "model": payload.model,
                "prompt": prompt,
                "stream": False
            })
            r.raise_for_status()
            res = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    text = res.get("response") or ""
    return {"session_id": payload.session_id, "result": text}


class PlannerRequest(BaseModel):
    session_id: str
    focus: Optional[str] = None
    model: str = "llama3.1:8b"


@app.post("/planner")
async def weekly_planner_endpoint(payload: PlannerRequest):
    prompt = (
        "Create a weekly plan from Monday to Sunday with 3-5 focused tasks per day. "
        "Return JSON with keys days:[{day, tasks[]}]. "
    )
    if payload.focus:
        prompt += f"Focus context: {payload.focus}. "

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                "model": payload.model,
                "prompt": prompt + "Ensure valid JSON only.",
                "stream": False
            })
            r.raise_for_status()
            res = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    text = res.get("response") or "{}"
    return {"session_id": payload.session_id, "plan": text}


class RoleplayRequest(BaseModel):
    session_id: str
    persona: str
    message: str
    model: str = "llama3.1:8b"


@app.post("/roleplay")
async def roleplay_endpoint(payload: RoleplayRequest):
    setup = f"You are role-playing as: {payload.persona}. Stay in character."
    prompt = setup + "\n\n" + payload.message

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
                "model": payload.model,
                "prompt": prompt,
                "stream": False
            })
            r.raise_for_status()
            res = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

    text = res.get("response") or ""

    # Log roleplay message
    rp = Roleplay(session_id=payload.session_id, persona=payload.persona, instructions=payload.message)
    await create_document("roleplay", rp.model_dump())

    return {"session_id": payload.session_id, "reply": text}
