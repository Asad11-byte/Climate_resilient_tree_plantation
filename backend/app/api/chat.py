from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_chat_service
from app.core.exceptions import ProviderUnavailableError
from app.repositories import chat_repository as sessions_repo
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.retrieval import SourceSchema
from app.services.chat.service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    # Every chat turn needs somewhere to land: reuse the given session, or
    # start a new one so the sidebar has something to show immediately.
    if request.session_id:
        session = sessions_repo.get_session(str(request.session_id))
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = sessions_repo.create_session()
    session_id = str(session["id"])

    sessions_repo.save_message(session_id, role="user", content=request.query)

    try:
        result = await chat_service.chat(
            query=request.query,
            latitude=request.latitude,
            longitude=request.longitude,
            top_k=request.top_k,
        )
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sources_payload = [s.__dict__ for s in result.sources]

    sessions_repo.save_message(
        session_id,
        role="assistant",
        content=result.answer,
        query_category=result.query_category,
        evidence_available=result.evidence_available,
        sources=sources_payload,
    )

    # Title the session from the first user message the first time only;
    # every turn after that just bumps updated_at for recency ordering.
    title = sessions_repo.truncate_title(request.query) if not session.get("title") else None
    sessions_repo.touch_session(session_id, title=title)

    return ChatResponse(
        query=request.query,
        query_category=result.query_category,
        evidence_available=result.evidence_available,
        answer=result.answer,
        sources=[SourceSchema(**s.__dict__) for s in result.sources],
        model=result.model,
        session_id=session_id,
    )