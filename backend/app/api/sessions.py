from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import CurrentUser, get_current_user
from app.core.dependencies import get_chat_message_repository, get_chat_session_repository
from app.schemas.session import MessageSchema, RenameSessionRequest, SessionSchema

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSchema])
async def list_sessions(current_user: CurrentUser = Depends(get_current_user)) -> list[dict]:
    repo = get_chat_session_repository()
    return await repo.list_for_user(current_user.user_id)


@router.post("", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
async def create_session(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    repo = get_chat_session_repository()
    return await repo.create(current_user.user_id)


@router.patch("/{session_id}", response_model=SessionSchema)
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    repo = get_chat_session_repository()
    updated = await repo.rename(session_id, current_user.user_id, body.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> None:
    repo = get_chat_session_repository()
    if not await repo.get_for_user(session_id, current_user.user_id):
        raise HTTPException(status_code=404, detail="Session not found")
    await repo.delete(session_id, current_user.user_id)


@router.get("/{session_id}/messages", response_model=list[MessageSchema])
async def get_session_messages(
    session_id: str, current_user: CurrentUser = Depends(get_current_user)
) -> list[dict]:
    session_repo = get_chat_session_repository()
    # chat_messages has no user_id column — ownership is enforced by
    # checking the parent session belongs to this user first.
    if not await session_repo.get_for_user(session_id, current_user.user_id):
        raise HTTPException(status_code=404, detail="Session not found")
    message_repo = get_chat_message_repository()
    return await message_repo.list_for_session(session_id)