"""Natural-language questions about the cafe."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import schemas
from app.api.deps import get_current_owner, get_db
from app.ask.llm import OpenAIRouter
from app.ask.router import Router, RouterDecision
from app.ask.service import AskResponse, ask
from app.core.config import settings

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    # From the previous response, so "and last month?" keeps its context.
    previous: RouterDecision | None = None
    previous_question: str | None = Field(default=None, max_length=500)


def get_router() -> Router:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ask is not configured on this server",
        )
    return OpenAIRouter()


@router.post("", response_model=AskResponse)
def ask_question(
    body: AskRequest,
    db: Session = Depends(get_db),
    llm: Router = Depends(get_router),
    current_user: schemas.TokenData = Depends(get_current_owner),
):
    """Answer a question with a fixed report. Owner only — the reports cover
    the full financial history, as the analytics endpoints do."""
    return ask(
        db,
        body.question,
        llm,
        previous=body.previous,
        previous_question=body.previous_question,
    )
