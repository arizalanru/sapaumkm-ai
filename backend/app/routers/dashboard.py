from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Conversation, Message
from ..schemas import (
    AdminMessageRequest,
    ConversationResponse,
    DashboardStats,
    HandoffRequest,
    MessageResponse,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


def _get_conversation(db: Session, conversation_id: int) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Percakapan tidak ditemukan")
    return conversation


def _set_state(
    db: Session, conversation_id: int, new_status: str, requires_human: bool
) -> Conversation:
    conversation = _get_conversation(db, conversation_id)
    conversation.status = new_status
    conversation.requires_human = requires_human
    db.commit()
    return conversation


@router.get("/conversations", response_model=list[ConversationResponse])
def conversations(db: Session = Depends(get_db)):
    return db.scalars(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.started_at.desc(), Conversation.id.desc())
    ).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def conversation_detail(conversation_id: int, db: Session = Depends(get_db)):
    return _get_conversation(db, conversation_id)


@router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageResponse]
)
def conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    _get_conversation(db, conversation_id)
    return db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at, Message.id)
    ).all()


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_message(
    conversation_id: int,
    payload: AdminMessageRequest,
    db: Session = Depends(get_db),
):
    conversation = _get_conversation(db, conversation_id)
    if conversation.status != "admin_active":
        raise HTTPException(
            status_code=409,
            detail="Admin hanya dapat mengirim pesan setelah mengambil alih percakapan",
        )
    message = Message(
        conversation_id=conversation.id,
        sender="admin",
        content=payload.content,
        intent="human_support",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.patch(
    "/conversations/{conversation_id}/takeover", response_model=ConversationResponse
)
def takeover_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = _get_conversation(db, conversation_id)
    if conversation.status not in {"waiting_admin", "admin_active"}:
        raise HTTPException(status_code=409, detail="Percakapan tidak sedang menunggu admin")
    return _set_state(db, conversation_id, "admin_active", True)


@router.patch(
    "/conversations/{conversation_id}/resolve", response_model=ConversationResponse
)
def resolve_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = _get_conversation(db, conversation_id)
    if conversation.status != "admin_active":
        raise HTTPException(status_code=409, detail="Ambil alih percakapan sebelum menyelesaikannya")
    return _set_state(db, conversation_id, "resolved", False)


@router.patch(
    "/conversations/{conversation_id}/return-to-ai",
    response_model=ConversationResponse,
)
def return_conversation_to_ai(conversation_id: int, db: Session = Depends(get_db)):
    conversation = _get_conversation(db, conversation_id)
    if conversation.status not in {"admin_active", "resolved"}:
        raise HTTPException(status_code=409, detail="Ambil alih percakapan sebelum mengembalikannya ke AI")
    return _set_state(db, conversation_id, "ai_active", False)


# Backward-compatible endpoint for older clients. New admin clients use the
# explicit state transition endpoints above.
@router.patch(
    "/conversations/{conversation_id}/handoff", response_model=ConversationResponse
)
def update_handoff(
    conversation_id: int,
    payload: HandoffRequest,
    db: Session = Depends(get_db),
):
    return _set_state(
        db,
        conversation_id,
        "waiting_admin" if payload.requires_human else "ai_active",
        payload.requires_human,
    )


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Conversation.id))) or 0
    human = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.status.in_(["waiting_admin", "admin_active"])
        )
    ) or 0
    resolved_by_ai = db.scalar(
        select(func.count(Conversation.id)).where(Conversation.status == "ai_active")
    ) or 0
    intents = Counter(
        db.scalars(select(Message.intent).where(Message.sender == "customer")).all()
    )
    return DashboardStats(
        total_conversations=total,
        resolved_by_ai=resolved_by_ai,
        requires_human=human,
        automation_rate=round((resolved_by_ai / total * 100) if total else 0, 1),
        average_response_seconds=3.2,
        intent_distribution=dict(intents),
    )
