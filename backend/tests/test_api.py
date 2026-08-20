import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GROQ_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


def post_chat(client: TestClient, message: str):
    return client.post("/api/chat", json={"message": message, "customer_name": "Rina Amelia"})


def test_required_scenarios():
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        products = client.get("/api/products").json()
        assert len(products) >= 10
        aqua = next(item for item in products if item["name"] == "Aqua Calm Gel Moisturizer")
        assert aqua["price"] == 89000
        assert aqua["stock"] == 24

        recommendation = post_chat(client, "Rekomendasi moisturizer untuk kulit berminyak di bawah Rp100.000")
        assert recommendation.status_code == 200
        assert recommendation.json()["intent"] == "product_recommendation"
        assert "product_catalog" in recommendation.json()["sources"]
        assert recommendation.json()["response_mode"] == "deterministic"

        order = client.get("/api/orders/GM-1002")
        assert order.status_code == 200
        assert order.json()["tracking_number"] == "JT92817364"
        tracked = post_chat(client, "Cek pesanan GM-1002")
        assert "JT92817364" in tracked.json()["answer"]
        assert tracked.json()["sources"] == ["order_database"]
        assert tracked.json()["response_mode"] == "deterministic"

        qris = post_chat(client, "Bisa bayar pakai QRIS?")
        assert qris.json()["intent"] == "payment_info"
        assert "QRIS" in qris.json()["answer"]

        damaged = post_chat(client, "Barang saya rusak dan ingin refund")
        assert damaged.json()["requires_human"] is True
        assert damaged.json()["intent"] == "refund"

        medical = post_chat(client, "Apakah produk ini bisa menyembuhkan eksim?")
        assert medical.json()["requires_human"] is True
        assert "diagnosis" in medical.json()["answer"].lower()

        conversations = client.get("/api/conversations")
        assert conversations.status_code == 200
        assert all(len(item["messages"]) >= 2 for item in conversations.json())

        stats = client.get("/api/dashboard/stats")
        assert stats.status_code == 200
        assert stats.json()["total_conversations"] >= 4


def test_product_recommendation_calls_groq_with_usage_context(monkeypatch):
    captured: dict = {"calls": 0}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Generated answer",
                            "reasoning": "Internal reasoning",
                        },
                        "finish_reason": "stop",
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, **kwargs):
            captured["calls"] += 1
            captured["url"] = url
            captured["request"] = kwargs
            return FakeResponse()

    monkeypatch.setattr(settings, "groq_api_key", "test-key-not-real")
    monkeypatch.setattr(settings, "groq_model", "openai/gpt-oss-120b")
    monkeypatch.setattr("app.services.ai_service.httpx.AsyncClient", FakeAsyncClient)

    with TestClient(app) as client:
        response = post_chat(
            client,
            "Rekomendasi moisturizer untuk kulit berminyak di bawah Rp100.000 dan cara pakainya",
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Generated answer"
    assert response.json()["response_mode"] == "groq"
    assert response.json()["answer"] != (
        "Rekomendasi dari katalog GlowMart: Aqua Calm Gel Moisturizer "
        "(Rp89.000, stok 24). Pilih sesuai kebutuhan dan tipe kulit Kakak, ya."
    )
    assert captured["calls"] == 1
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["request"]["json"]["model"] == settings.groq_model
    assert captured["request"]["json"]["reasoning_effort"] == "low"
    assert captured["request"]["json"]["include_reasoning"] is False
    assert captured["request"]["json"]["max_completion_tokens"] == 1000
    assert captured["request"]["json"]["stream"] is False
    assert captured["request"]["json"]["temperature"] == 0.2
    assert "max_tokens" not in captured["request"]["json"]
    assert "reasoning_format" not in captured["request"]["json"]

    prompt = captured["request"]["json"]["messages"][1]["content"]
    system_prompt = captured["request"]["json"]["messages"][0]["content"]
    assert "tanpa tabel Markdown" in system_prompt
    assert "daftar bernomor" in system_prompt
    assert "180 kata atau kurang" in system_prompt
    assert "maksimal Rp150.000" in system_prompt
    assert "nama=Aqua Calm Gel Moisturizer" in prompt
    assert "harga=Rp89.000" in prompt
    assert "stok=24" in prompt
    assert "kategori=Moisturizer" in prompt
    assert "tipe_kulit=Berminyak, kombinasi, sensitif" in prompt
    assert "pemakaian=Gunakan pagi dan malam setelah serum." in prompt


def test_groq_markdown_and_unicode_are_normalized(monkeypatch):
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "**bold** `kode` – non‑breaking space"
                        },
                        "finish_reason": "stop",
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(settings, "groq_api_key", "test-key-not-real")
    monkeypatch.setattr("app.services.ai_service.httpx.AsyncClient", FakeAsyncClient)

    with TestClient(app) as client:
        response = post_chat(client, "Bisa bayar pakai QRIS?")

    assert response.status_code == 200
    assert response.json()["answer"] == "bold kode - non-breaking space"
    assert response.json()["response_mode"] == "groq"
    assert "**" not in response.json()["answer"]
    assert "`" not in response.json()["answer"]
    assert not any(
        character in response.json()["answer"]
        for character in "\u00a0\u202f\u2007\u2010\u2011\u2012\u2013\u2014\u2212"
    )
