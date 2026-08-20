import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Conversation, Message, Order
from ..schemas import ChatRequest, ChatResponse
from ..services.ai_service import ResponseMode, generate_answer, normalize_response_text
from ..services.intent_service import MEDICAL_WORDS, detect_intent, normalize_message
from ..services.knowledge_service import retrieve_knowledge

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("uvicorn.error")
HUMAN_STATES = {"waiting_admin", "admin_active"}


def _order_number(message: str) -> str | None:
    match = re.search(r"\bGM[-\s]?(\d+)\b", message, re.IGNORECASE)
    return f"GM-{match.group(1)}" if match else None


def _is_checkout_agreement(message: str, recent_messages: list[Message]) -> bool:
    normalized = normalize_message(message)
    agreed = normalized in {"ya", "iya", "yes", "setuju", "lanjut", "boleh", "mau"}
    last_assistant = next(
        (item for item in reversed(recent_messages) if item.sender == "assistant"), None
    )
    return bool(
        agreed
        and last_assistant
        and "admin membantu proses checkout" in last_assistant.content.lower()
    )


def _is_purchase_request(message: str) -> bool:
    normalized = normalize_message(message)
    return bool(re.search(r"\b(beli|belanja|checkout)\b", normalized))


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    if payload.conversation_id is not None:
        conversation = db.get(Conversation, payload.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Percakapan tidak ditemukan")
    else:
        conversation = Conversation(
            customer_name=payload.customer_name,
            status="ai_active",
            requires_human=False,
        )
        db.add(conversation)
        db.flush()

    if conversation.status == "active":
        conversation.status = "waiting_admin" if conversation.requires_human else "ai_active"

    recent_messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.id.desc())
            .limit(8)
        ).all()
    )
    recent_messages.reverse()
    recent_intents = [item.intent for item in recent_messages if item.sender == "customer"]
    intent, confidence, should_escalate = detect_intent(payload.message, recent_intents)
    checkout_agreement = _is_checkout_agreement(payload.message, recent_messages)
    if checkout_agreement:
        intent, confidence, should_escalate = "human_request", 0.99, True

    logger.info("Selected intent=%s conversation_status=%s", intent, conversation.status)
    customer_message = Message(
        conversation_id=conversation.id,
        sender="customer",
        content=normalize_response_text(payload.message.strip()),
        intent=intent,
    )
    db.add(customer_message)
    db.flush()

    if conversation.status in HUMAN_STATES | {"resolved"}:
        db.commit()
        return ChatResponse(
            conversation_id=conversation.id,
            answer="",
            intent=intent,
            confidence=confidence,
            requires_human=conversation.status in HUMAN_STATES,
            sources=["support_queue"],
            response_mode="deterministic",
            conversation_status=conversation.status,
            stored_for_support=True,
            customer_message_id=customer_message.id,
        )

    sources: list[str] = []
    response_mode: ResponseMode = "deterministic"
    assistant_message: Message | None = None
    normalized = normalize_message(payload.message)

    if intent == "greeting":
        answer = "Halo, Kak! Ada yang bisa Sapa bantu soal produk, pembayaran, atau pesanan GlowMart?"
    elif intent == "thanks":
        answer = "Sama-sama, Kak. Senang bisa membantu."
    elif intent == "goodbye":
        answer = "Sampai jumpa, Kak. Semoga harinya menyenangkan!"
    elif intent == "order_tracking":
        number = _order_number(payload.message)
        order = db.scalar(
            select(Order).where(func.upper(Order.order_number) == number.upper())
        ) if number else None
        if order:
            answer = (
                f"Pesanan {order.order_number}: {order.status}. Kurir {order.courier}, "
                f"nomor resi {order.tracking_number}, estimasi tiba {order.estimated_arrival}."
            )
            sources = ["order_database"]
            confidence = 0.99
        else:
            answer = (
                f"Pesanan {number} tidak ditemukan. Periksa kembali nomor pesanan atau minta bantuan admin."
                if number
                else "Mohon kirim nomor pesanan dengan format GM-xxxx agar dapat saya cek."
            )
            confidence = 0.72
    elif should_escalate:
        if intent == "medical_or_sensitive" or any(
            word in payload.message.lower() for word in MEDICAL_WORDS
        ):
            answer = (
                "Maaf, Kak, saya tidak dapat memberikan diagnosis medis. Percakapan sudah "
                "diteruskan ke admin; untuk keluhan kesehatan, konsultasikan dengan tenaga medis."
            )
        elif checkout_agreement:
            answer = (
                "Permintaan pembelian Anda sudah masuk ke antrean tim GlowMart. Admin akan "
                "mengonfirmasi produk dan stok, lalu menjelaskan langkah checkout yang tersedia."
            )
        elif intent in {"complaint", "refund"}:
            answer = (
                "Maaf atas kendalanya, Kak. Permintaan Anda sudah masuk ke antrean tim GlowMart. "
                "Admin akan memeriksa bukti dan data pesanan sebelum menentukan tindak lanjut."
            )
        else:
            answer = (
                "Permintaan Anda sudah masuk ke antrean tim GlowMart. Admin akan melanjutkan "
                "percakapan ini setelah mengambil alih chat."
            )
        conversation.status = "waiting_admin"
        conversation.requires_human = True
        sources = ["handoff_policy"]
        confidence = max(confidence, 0.97)
    elif any(phrase in normalized for phrase in ("sudah bayar", "udah bayar", "telah membayar")):
        answer = (
            "Status pembayaran tidak dapat diverifikasi melalui chat ini. Sapa tidak dapat "
            "menyatakan pembayaran berhasil atau memproses pesanan. Admin GlowMart perlu "
            "memeriksa transaksi secara langsung."
        )
        sources = ["payment_policy"]
    else:
        customer_context = "\n".join(
            item.content for item in recent_messages if item.sender == "customer"
        )
        reference_context = "\n".join(item.content for item in recent_messages)
        knowledge = retrieve_knowledge(
            db, payload.message, intent, customer_context, reference_context
        )
        products, faqs = knowledge.products, knowledge.faqs
        logger.info(
            "Retrieved products count=%s names=%s intent=%s",
            len(products),
            [product.name for product in products],
            intent,
        )
        if _is_purchase_request(payload.message) and len(products) == 1:
            product = products[0]
            price = f"{product.price:,.0f}".replace(",", ".")
            answer = (
                f"{product.name} tersedia dengan harga Rp{price} dan stok {product.stock} unit. "
                "Sapa tidak dapat melakukan checkout atau memverifikasi pembayaran. Admin membantu "
                "proses checkout secara manual. Jika ingin dilanjutkan, balas 'ya' untuk masuk ke antrean admin."
            )
            sources = ["product_catalog", "checkout_policy"]
        else:
            answer, response_mode = await generate_answer(
                payload.message,
                intent,
                products,
                faqs,
                [(item.sender, item.content) for item in recent_messages],
                knowledge.filter_note,
            )
            if products:
                sources.append("product_catalog")
            if faqs:
                sources.append("faq")

    answer = normalize_response_text(answer)
    assistant_message = Message(
        conversation_id=conversation.id,
        sender="assistant",
        content=answer,
        intent=intent,
    )
    db.add(assistant_message)
    db.flush()
    db.commit()
    return ChatResponse(
        conversation_id=conversation.id,
        answer=answer,
        intent=intent,
        confidence=confidence,
        requires_human=conversation.status in HUMAN_STATES,
        sources=sources,
        response_mode=response_mode,
        conversation_status=conversation.status,
        stored_for_support=False,
        customer_message_id=customer_message.id,
        assistant_message_id=assistant_message.id,
    )
