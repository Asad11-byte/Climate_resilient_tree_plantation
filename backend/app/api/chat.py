from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import CurrentUser, get_current_user
from app.core.dependencies import (
    get_chat_message_repository,
    get_chat_service,
    get_chat_session_repository,
)
from app.core.exceptions import ProviderUnavailableError
from app.repositories.chat_session_repository import truncate_title
from app.schemas.chat import ChatRequest, ChatResponse, SpeciesMentionSchema
from app.schemas.retrieval import SourceSchema
from app.services.chat.service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    session_repo = get_chat_session_repository()
    message_repo = get_chat_message_repository()

    # Every chat turn needs somewhere to land: reuse the given session (only
    # if it belongs to this user — 404 either way if it doesn't exist or
    # belongs to someone else, so a session id can't be used to probe for
    # other accounts' sessions), or start a new one.
    if request.session_id:
        session = await session_repo.get_for_user(str(request.session_id), current_user.user_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = await session_repo.create(current_user.user_id)
    session_id = str(session["id"])

    await message_repo.save(session_id, role="user", content=request.query)

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

    await message_repo.save(
        session_id,
        role="assistant",
        content=result.answer,
        query_category=result.query_category,
        evidence_available=result.evidence_available,
        sources=sources_payload,
    )

    # Title the session from the first user message once; every turn after
    # that just bumps updated_at for recency ordering.
    title = truncate_title(request.query) if not session.get("title") else None
    await session_repo.touch(session_id, current_user.user_id, title=title)

    return ChatResponse(
        query=request.query,
        query_category=result.query_category,
        evidence_available=result.evidence_available,
        answer=result.answer,
        sources=[SourceSchema(**s.__dict__) for s in result.sources],
        model=result.model,
        session_id=session_id,
        # THE FIX: this conversion was missing — ChatResult.mentioned_species
        # had real data (once the dependencies.py fix above is also
        # applied), but it never made it into the actual HTTP response
        # because nothing here copied it over, same way `sources` does.
        mentioned_species=[SpeciesMentionSchema(**m.__dict__) for m in result.mentioned_species],
    )