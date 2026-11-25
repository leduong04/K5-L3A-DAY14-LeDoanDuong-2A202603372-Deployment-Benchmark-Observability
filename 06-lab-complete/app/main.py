"""Production-ready mock AI agent API."""
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import r, redis_healthy
from utils.mock_llm import ask as llm_ask


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "lvl": record.levelname,
                           "event": record.getMessage()}, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("agent")
logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False
@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("startup")
    yield
    logger.info("graceful_shutdown")
    r.close()


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not redis_healthy():
        return JSONResponse(status_code=503, content={"status": "not_ready", "redis": "unavailable"})
    return {"status": "ready", "redis": "ok"}


@app.post("/ask")
def ask(body: AskRequest, api_key: str = Depends(verify_api_key)):
    check_rate_limit(api_key)
    check_budget()
    answer = llm_ask(body.question)
    input_tokens = max(1, len(body.question) // 4)
    output_tokens = max(1, len(answer) // 4)
    cost = record_cost(input_tokens, output_tokens)
    logger.info(json.dumps({"event": "request", "path": "/ask", "status": 200,
                            "environment": settings.environment, "input_tokens": input_tokens,
                            "output_tokens": output_tokens, "cost_usd": cost}))
    return {"question": body.question, "answer": answer, "usage": {"input_tokens": input_tokens,
            "output_tokens": output_tokens, "cost_usd": cost}}
