from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal
from app.main import app
from app.models import Conversation, Message, Order
from app.seed import seed_database


def chat(client: TestClient, message: str, conversation_id: int | None = None):
    return client.post(
        "/api/chat",
        json={
            "message": message,
            "conversation_id": conversation_id,
            "customer_name": "Pelanggan Uji Takeover",
        },
    )


def escalated_conversation(client: TestClient) -> int:
    response = chat(client, "Barang yang saya terima rusak dan saya mau refund")
    assert response.status_code == 200
    return response.json()["conversation_id"]


def test_refund_creates_waiting_admin_and_complete_detail():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        response = client.get(f"/api/conversations/{conversation_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "waiting_admin"
        assert data["requires_human"] is True
        assert [message["sender"] for message in data["messages"]] == ["customer", "assistant"]


def test_admin_cannot_send_before_takeover():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"sender": "admin", "content": "Halo dari admin"},
        )
        assert response.status_code == 409


def test_takeover_allows_and_stores_admin_message():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        takeover = client.patch(f"/api/conversations/{conversation_id}/takeover")
        assert takeover.status_code == 200
        assert takeover.json()["status"] == "admin_active"

        sent = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"sender": "admin", "content": "Halo, saya Rani dari tim GlowMart."},
        )
        assert sent.status_code == 201
        assert sent.json()["sender"] == "admin"

        messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
        assert any(message["id"] == sent.json()["id"] and message["content"] == "Halo, saya Rani dari tim GlowMart." for message in messages)


def test_admin_message_validation_rejects_empty_and_non_admin_sender():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        client.patch(f"/api/conversations/{conversation_id}/takeover")
        empty = client.post(f"/api/conversations/{conversation_id}/messages", json={"sender": "admin", "content": "   "})
        wrong_sender = client.post(f"/api/conversations/{conversation_id}/messages", json={"sender": "assistant", "content": "Tidak sah"})
        assert empty.status_code == 422
        assert wrong_sender.status_code == 422


def test_customer_message_during_admin_active_is_stored_without_groq(monkeypatch):
    calls = {"count": 0}

    async def forbidden_groq(*_args, **_kwargs):
        calls["count"] += 1
        raise AssertionError("Groq must not be called during admin takeover")

    monkeypatch.setattr("app.routers.chat.generate_answer", forbidden_groq)
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        client.patch(f"/api/conversations/{conversation_id}/takeover")
        response = chat(client, "Nomor pesanan saya GM-1002", conversation_id)
        assert response.status_code == 200
        data = response.json()
        assert data["stored_for_support"] is True
        assert data["answer"] == ""
        assert data["assistant_message_id"] is None
        assert calls["count"] == 0
        messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
        assert messages[-1]["content"] == "Nomor pesanan saya GM-1002"


def test_resolve_and_return_to_ai_state_transitions():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        client.patch(f"/api/conversations/{conversation_id}/takeover")
        resolved = client.patch(f"/api/conversations/{conversation_id}/resolve")
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"
        assert resolved.json()["requires_human"] is False

        returned = client.patch(f"/api/conversations/{conversation_id}/return-to-ai")
        assert returned.status_code == 200
        assert returned.json()["status"] == "ai_active"
        assert returned.json()["requires_human"] is False


def test_messages_endpoint_returns_admin_messages_once_in_order():
    with TestClient(app) as client:
        conversation_id = escalated_conversation(client)
        client.patch(f"/api/conversations/{conversation_id}/takeover")
        created = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"sender": "admin", "content": "Mohon kirim nomor pesanan terlebih dahulu."},
        ).json()
        messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
        ids = [message["id"] for message in messages]
        assert ids == sorted(ids)
        assert len(ids) == len(set(ids))
        assert [message for message in messages if message["id"] == created["id"]] == [created]


def test_purchase_and_paid_messages_do_not_create_or_verify_orders():
    with TestClient(app) as client, SessionLocal() as db:
        before = db.scalar(select(func.count(Order.id)))
        purchase = chat(client, "Saya mau beli Aqua Calm Gel Moisturizer")
        assert purchase.status_code == 200
        purchase_data = purchase.json()
        assert "Aqua Calm Gel Moisturizer" in purchase_data["answer"]
        assert "Rp89.000" in purchase_data["answer"]
        assert "stok 24" in purchase_data["answer"].lower()
        assert "admin" in purchase_data["answer"].lower()

        paid = chat(client, "Saya sudah bayar", purchase_data["conversation_id"])
        assert paid.status_code == 200
        assert "tidak dapat diverifikasi" in paid.json()["answer"].lower()
        assert "pembayaran telah diterima" not in paid.json()["answer"].lower()
        db.expire_all()
        after = db.scalar(select(func.count(Order.id)))
        assert after == before


def test_purchase_handoff_agreement_enters_waiting_admin():
    with TestClient(app) as client:
        purchase = chat(client, "Saya mau beli Aqua Calm Gel Moisturizer").json()
        agreement = chat(client, "ya", purchase["conversation_id"])
        assert agreement.status_code == 200
        assert agreement.json()["conversation_status"] == "waiting_admin"


def test_existing_order_tracking_remains_database_controlled():
    with TestClient(app) as client:
        response = chat(client, "Tolong cek order GM-1002")
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "order_tracking"
        assert "JT92817364" in data["answer"]
        assert data["sources"] == ["order_database"]


def test_complete_refund_queue_takeover_message_and_resolution_flow():
    with TestClient(app) as client:
        refund = chat(client, "Barangnya rusak dan saya ingin refund")
        assert refund.status_code == 200
        refund_data = refund.json()
        conversation_id = refund_data["conversation_id"]
        assert refund_data["conversation_status"] == "waiting_admin"
        assert refund_data["requires_human"] is True
        assert "antrean tim GlowMart" in refund_data["answer"]

        queued = client.get("/api/conversations").json()
        queued_conversation = next(item for item in queued if item["id"] == conversation_id)
        assert queued_conversation["status"] == "waiting_admin"
        assert queued_conversation["requires_human"] is True

        takeover = client.patch(f"/api/conversations/{conversation_id}/takeover")
        assert takeover.json()["status"] == "admin_active"
        admin_reply = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"sender": "admin", "content": "Halo, saya Rani dari tim GlowMart. Mohon kirim nomor pesanan."},
        )
        assert admin_reply.status_code == 201
        customer_messages = client.get(f"/api/conversations/{conversation_id}/messages").json()
        assert customer_messages[-1]["id"] == admin_reply.json()["id"]
        assert customer_messages[-1]["sender"] == "admin"

        resolved = client.patch(f"/api/conversations/{conversation_id}/resolve")
        assert resolved.json()["status"] == "resolved"
        assert resolved.json()["requires_human"] is False


def test_seed_repairs_legacy_refund_handoff_state():
    with SessionLocal() as db:
        conversation = Conversation(customer_name="Legacy Customer", status="ai_active", requires_human=False)
        db.add(conversation)
        db.flush()
        db.add_all([
            Message(conversation_id=conversation.id, sender="customer", content="Saya ingin refund", intent="refund"),
            Message(conversation_id=conversation.id, sender="assistant", content="Permintaan Anda sudah masuk ke antrean tim GlowMart.", intent="refund"),
        ])
        db.commit()
        conversation_id = conversation.id

        seed_database(db)
        repaired = db.get(Conversation, conversation_id)
        assert repaired is not None
        assert repaired.status == "waiting_admin"
        assert repaired.requires_human is True
