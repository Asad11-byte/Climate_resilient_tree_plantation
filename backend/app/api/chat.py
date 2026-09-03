from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_chat_service
from app.core.exceptions import ProviderUnavailableError
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.retrieval import SourceSchema
from app.services.chat.service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        result = await chat_service.chat(
            query=request.query,
            latitude=request.latitude,
            longitude=request.longitude,
            top_k=request.top_k,
        )
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(
        query=request.query,
        query_category=result.query_category,
        evidence_available=result.evidence_available,
        answer=result.answer,
        sources=[SourceSchema(**s.__dict__) for s in result.sources],
        model=result.model,
    )
