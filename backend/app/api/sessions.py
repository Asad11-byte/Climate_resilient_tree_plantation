from fastapi import APIRouter, HTTPException, status

from app.repositories import chat_repository as repo
from app.schemas.session import MessageSchema, RenameSessionRequest, SessionSchema

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSchema])
def list_sessions() -> list[dict]:
    return repo.list_sessions()


@router.post("", response_model=SessionSchema, status_code=status.HTTP_201_CREATED)
def create_session() -> dict:
    return repo.create_session()


@router.patch("/{session_id}", response_model=SessionSchema)
def rename_session(session_id: str, body: RenameSessionRequest) -> dict:
    if not repo.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return repo.rename_session(session_id, body.title)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str) -> None:
    if not repo.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    repo.delete_session(session_id)


@router.get("/{session_id}/messages", response_model=list[MessageSchema])
def get_session_messages(session_id: str) -> list[dict]:
    if not repo.get_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return repo.list_messages(session_id)