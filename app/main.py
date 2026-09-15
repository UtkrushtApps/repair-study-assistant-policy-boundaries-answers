from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.assistant import AssistantResult, StudyAssistant
from app.config import get_settings
from app.llm_client import LLMClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Study Assistant")


class TurnRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    request: str = Field(min_length=1, max_length=8000)


class TurnResponse(BaseModel):
    status: str
    text: str
    sources: list[str]


@lru_cache
def get_assistant() -> StudyAssistant:
    return StudyAssistant(LLMClient(get_settings()))


def _respond(action: str, body: TurnRequest) -> TurnResponse:
    try:
        result: AssistantResult = get_assistant().handle(body.session_id, action, body.request)
        return TurnResponse(status=result.status, text=result.text, sources=result.sources)
    except RuntimeError as exc:
        logger.warning("Assistant service is unavailable", extra={"action": action})
        if "OPENAI_API_KEY" in str(exc):
            raise HTTPException(status_code=503, detail="Model service is not configured") from exc
        raise HTTPException(status_code=503, detail="Assistant service is unavailable") from exc
    except Exception as exc:
        logger.exception("Unhandled API error", extra={"action": action})
        raise HTTPException(status_code=503, detail="Assistant service is unavailable") from exc


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    # FastAPI's default validation response can echo the rejected input.
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    # Health remains key-independent; model connectivity is checked separately by app.ping.
    return {"status": "ok"}


@app.post("/ask", response_model=TurnResponse)
def ask(body: TurnRequest) -> TurnResponse:
    return _respond("answer", body)


@app.post("/draft", response_model=TurnResponse)
def draft(body: TurnRequest) -> TurnResponse:
    return _respond("draft", body)
