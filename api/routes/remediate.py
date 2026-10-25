from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json
import uuid
from typing import Dict, Any, AsyncGenerator

from api.models import RemediateRequest
from core.orchestrator import AutoFixOrchestrator, RemediationSession
from core.parsers import parse_ci_logs
from core.client import llm_client

router = APIRouter(prefix="/api/remediate", tags=["Remediation"])

# Event queues for active sessions: {session_id: asyncio.Queue}
SESSION_QUEUES: Dict[str, asyncio.Queue] = {}
PAST_SESSIONS: Dict[str, RemediationSession] = {}


@router.post("", response_model=RemediationSession)
def remediate_incident(req: RemediateRequest):
    """Synchronous remediation endpoint."""
    repo_dir = req.repo_dir or "."
    orchestrator = AutoFixOrchestrator(
        repo_dir=repo_dir,
        test_command=req.test_command,
        max_iterations=req.max_iterations,
    )
    session = orchestrator.remediate(req.raw_logs)
    PAST_SESSIONS[session.session_id] = session
    return session


@router.post("/async")
async def start_async_remediation(req: RemediateRequest, background_tasks: BackgroundTasks):
    """
    Starts an asynchronous remediation session that streams events via SSE.
    Returns session_id.
    """
    session_id = f"inc_{uuid.uuid4().hex[:8]}"
    queue = asyncio.Queue()
    SESSION_QUEUES[session_id] = queue

    def event_emitter(event_type: str, data: Dict[str, Any]):
        payload = json.dumps({"event": event_type, "data": data})
        # Put into queue safely
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(queue.put_nowait, payload)
        except Exception:
            pass

    def run_worker():
        orchestrator = AutoFixOrchestrator(
            repo_dir=req.repo_dir or ".",
            test_command=req.test_command,
            max_iterations=req.max_iterations,
            event_callback=event_emitter,
        )
        session = orchestrator.remediate(req.raw_logs)
        PAST_SESSIONS[session_id] = session
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(queue.put_nowait, "[DONE]")
        except Exception:
            pass

    background_tasks.add_task(run_worker)
    return {"session_id": session_id, "status": "started"}


@router.get("/stream/{session_id}")
async def stream_remediation(session_id: str):
    """Server-Sent Events endpoint streaming live agent thought and execution logs."""
    if session_id not in SESSION_QUEUES:
        # If session already finished, return past timeline
        if session_id in PAST_SESSIONS:
            sess = PAST_SESSIONS[session_id]
            async def event_generator_past():
                for item in sess.timeline:
                    yield f"data: {json.dumps({'event': item['step'], 'data': item['details']})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(event_generator_past(), media_type="text/event-stream")
        raise HTTPException(status_code=404, detail="Active session not found.")

    queue = SESSION_QUEUES[session_id]

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                item = await asyncio.wait_for(queue.get(), timeout=90.0)
                if item == "[DONE]":
                    yield "data: [DONE]\n\n"
                    break
                yield f"data: {item}\n\n"
        except asyncio.TimeoutError:
            yield "data: [TIMEOUT]\n\n"
        finally:
            SESSION_QUEUES.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/session/{session_id}", response_model=RemediationSession)
def get_session(session_id: str):
    if session_id not in PAST_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    return PAST_SESSIONS[session_id]
