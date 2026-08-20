import pytest

from app.services.intent_service import detect_intent


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("halo min", "greeting"),
        ("Selamat pagi", "greeting"),
        ("aku mau beli", "product_discovery"),
        ("mau belanja skincare", "product_discovery"),
        ("jual apa aja", "product_discovery"),
        ("skincare apa aja yang ready", "product_discovery"),
        ("ada yg buat kulit berminyak ga", "product_recommendation"),
        ("budget aku 100 ribuan", "product_recommendation"),
        ("untuk oily dan acne ada saran?", "product_recommendation"),
        ("yg paling murah apa", "product_comparison"),
        ("tolong bandingkan produknya", "product_comparison"),
        ("brp harganya", "product_info"),
        ("info moiturizer dong", "product_info"),
        ("ada pelembap?", "product_info"),
        ("stoknya ready?", "stock_check"),
        ("stock sunscreen masih ada?", "stock_check"),
        ("cara pakenya gimana", "product_usage"),
        ("bagaimana cara penggunaan serum?", "product_usage"),
        ("bisa cod ga", "payment_info"),
        ("bisa qris?", "payment_info"),
        ("metode pembayarannya apa?", "payment_info"),
        ("berapa ongkir ke Bandung?", "shipping_info"),
        ("kurirnya apa saja?", "shipping_info"),
        ("ada diskon?", "promotion_info"),
        ("voucher terbaru", "promotion_info"),
        ("pesenan aku dimana", "order_tracking"),
        ("cek order GM-1002", "order_tracking"),
        ("nomor resi GM 1002", "order_tracking"),
        ("barangnya rusak", "complaint"),
        ("saya kecewa sekali", "complaint"),
        ("aku mau refund", "refund"),
        ("mau ngomong sama admin", "human_request"),
        ("sambungkan ke cs", "human_request"),
        ("makasih min", "thanks"),
        ("terima kasih banyak", "thanks"),
        ("dadah", "goodbye"),
        ("apakah ini menyembuhkan eksim?", "medical_or_sensitive"),
        ("aman untuk psoriasis?", "medical_or_sensitive"),
        ("siapa presiden Indonesia?", "unknown"),
    ],
)
def test_realistic_intent_matrix(message, expected):
    intent, _, _ = detect_intent(message)
    assert intent == expected


def _turn(client, message, conversation_id=None):
    response = client.post(
        "/api/chat",
        json={
            "message": message,
            "conversation_id": conversation_id,
            "customer_name": "Rina Amelia",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_vague_purchase_to_filtered_recommendation(client):
    first = _turn(client, "Aku mau beli skincare")
    assert first["intent"] == "product_discovery"
    assert "Aqua Calm Gel Moisturizer" in first["answer"]
    assert "budget" in first["answer"].lower()

    second = _turn(client, "Berminyak, budget 150 ribu", first["conversation_id"])
    assert second["intent"] == "product_recommendation"
    assert "Rp" in second["answer"]
    assert "belum ada produk" not in second["answer"].lower()


def test_recommendation_cheapest_then_usage(client):
    first = _turn(client, "Rekomendasi untuk kulit berminyak budget 100 ribu")
    second = _turn(client, "Yang paling murah yang mana?", first["conversation_id"])
    assert second["intent"] == "product_comparison"
    assert "paling murah" in second["answer"].lower()

    third = _turn(client, "Cara pakainya?", first["conversation_id"])
    assert third["intent"] == "product_usage"
    assert "gunakan" in third["answer"].lower()


def test_order_number_follow_up_is_deterministic(client):
    first = _turn(client, "Pesenan aku dimana?")
    assert first["intent"] == "order_tracking"
    assert "GM-xxxx" in first["answer"]

    second = _turn(client, "GM-1002", first["conversation_id"])
    assert second["response_mode"] == "deterministic"
    assert "JT92817364" in second["answer"]
    assert "22 Agustus 2026" in second["answer"]


def test_complaint_refund_keeps_handoff(client):
    first = _turn(client, "Barangnya rusak")
    assert first["intent"] == "complaint"
    assert first["requires_human"] is True

    second = _turn(client, "Aku mau refund", first["conversation_id"])
    assert second["intent"] == "refund"
    assert second["requires_human"] is True
    assert second["response_mode"] == "deterministic"

    takeover = client.patch(
        f"/api/conversations/{first['conversation_id']}/handoff",
        json={"requires_human": False},
    )
    assert takeover.status_code == 200
    assert takeover.json()["requires_human"] is False


def test_catalog_selection_then_stock(client):
    first = _turn(client, "Jual apa aja?")
    assert first["intent"] == "product_discovery"
    assert "Aqua Calm Gel Moisturizer" in first["answer"]

    second = _turn(client, "Aqua Calm Gel Moisturizer", first["conversation_id"])
    assert second["intent"] == "product_info"
    assert "Rp89.000" in second["answer"]

    third = _turn(client, "Stoknya ready?", first["conversation_id"])
    assert third["intent"] == "stock_check"
    assert "Aqua Calm Gel Moisturizer" in third["answer"]
    assert "stok 24" in third["answer"]


def test_sensitive_and_unknown_are_safe(client):
    sensitive = _turn(client, "Apakah ini bisa menyembuhkan eksim?")
    assert sensitive["intent"] == "medical_or_sensitive"
    assert sensitive["requires_human"] is True
    assert "diagnosis" in sensitive["answer"].lower()

    unknown = _turn(client, "Siapa presiden Indonesia?")
    assert unknown["intent"] == "unknown"
    assert unknown["response_mode"] == "deterministic"


def test_repeated_payment_question_stays_grounded(client):
    first = _turn(client, "Bisa QRIS?")
    second = _turn(client, "Bisa QRIS?", first["conversation_id"])
    assert first["intent"] == second["intent"] == "payment_info"
    assert "QRIS" in first["answer"] and "QRIS" in second["answer"]
    assert "belum tersedia" not in second["answer"].lower()


def test_promotion_uses_seeded_faq(client):
    response = _turn(client, "Ada promo atau voucher?")
    assert response["intent"] == "promotion_info"
    assert response["sources"] == ["faq"]
    assert "promo" in response["answer"].lower()


@pytest.mark.parametrize(
    "message",
    ["BAYARNYA BISA PAKE APA AA", "BISA BAYAR PAKE BCA?"],
)
def test_uat_generic_payment_uses_seeded_faq(client, message):
    response = _turn(client, message)
    assert response["intent"] == "payment_info"
    assert response["sources"] == ["faq"]
    assert "BCA" in response["answer"]
    assert "QRIS" in response["answer"]
    assert "GoPay" in response["answer"]
    assert "COD" in response["answer"]
    assert "tidak tersedia" not in response["answer"].lower()


def test_uat_refund_typo_escalates_without_automatic_decision(client):
    response = _turn(
        client,
        "barang yang di terima ini tidak sesuai kak aku pengen refunf",
    )
    assert response["intent"] == "refund"
    assert response["requires_human"] is True
    assert response["response_mode"] == "deterministic"
    assert "admin" in response["answer"].lower()
    assert "bukti" in response["answer"].lower()
    assert "data pesanan" in response["answer"].lower()


def test_uat_valid_unknown_order_number(client):
    first = _turn(client, "Pesenan aku dimana?")
    second = _turn(client, "GM-1200", first["conversation_id"])
    assert second["intent"] == "order_tracking"
    assert second["answer"] == (
        "Pesanan GM-1200 tidak ditemukan. Periksa kembali nomor pesanan "
        "atau minta bantuan admin."
    )
    assert "GM-xxxx" not in second["answer"]


def test_uat_dry_skin_budget_context_offers_nearest_match(client):
    first = _turn(client, "kulit aku kering")
    second = _turn(
        client,
        "kasih aku yang harganya di bawah rp 100.000",
        first["conversation_id"],
    )
    assert second["intent"] == "product_recommendation"
    assert "kulit kering" in second["answer"].lower()
    assert "maksimal Rp100.000" in second["answer"]
    assert "Overnight Hydration Mask" in second["answer"]
    assert "Rp115.000" in second["answer"]
    assert "menaikkan budget" in second["answer"].lower()
    assert "produk umum" in second["answer"].lower()


@pytest.fixture
def client():
    # Imported lazily so test_api.py configures the shared in-memory database
    # before application modules are initialized during normal suite collection.
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
