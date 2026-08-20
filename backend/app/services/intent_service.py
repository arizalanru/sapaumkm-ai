import re
import unicodedata
from difflib import SequenceMatcher


HUMAN_WORDS = ("admin", "manusia", "customer service", "operator", "petugas", "orang asli")
MEDICAL_WORDS = (
    "diagnosis", "dokter", "resep", "penyakit kulit", "infeksi", "obat", "dosis",
    "eksim", "eczema", "psoriasis", "dermatitis", "alergi", "luka", "jerawat parah",
    "menyembuhkan", "hamil", "menyusui", "iritasi parah", "terbakar",
)
ANGRY_WORDS = ("marah", "kecewa", "penipu", "kapok", "buruk sekali", "parah banget")
PRODUCT_CONTEXT_INTENTS = {
    "product_discovery", "product_info", "product_recommendation",
    "product_comparison", "stock_check", "product_usage",
}

REPLACEMENTS = {
    r"\byg\b": "yang",
    r"\bga+k?\b|\bngg?a+k?\b": "tidak",
    r"\bbrp\b": "berapa",
    r"\bstock\b": "stok",
    r"\bready\b": "tersedia",
    r"\bpakenya\b|\bpakenya\b|\bpake\b": "pakai",
    r"\bewallet\b|\be-wallet\b": "e wallet",
    r"\bpesenan\b|\borderan\b": "pesanan",
    r"\bmoisturiser\b|\bmoist\b": "moisturizer",
    r"\bsun\s*screen\b": "sunscreen",
    r"\boily\b": "berminyak",
    r"\bacne\b": "jerawat",
    r"\bmakasi+h?\b|\bthx\b|\bthanks\b": "makasih",
}


def normalize_message(message: str) -> str:
    text = unicodedata.normalize("NFKC", message).lower().strip()
    for pattern, replacement in REPLACEMENTS.items():
        text = re.sub(pattern, replacement, text)
    return re.sub(r"\s+", " ", text)


def _has(text: str, variants: tuple[str, ...]) -> bool:
    if any(
        (variant in text if " " in variant else re.search(rf"\b{re.escape(variant)}(?:nya|an)?\b", text))
        for variant in variants
    ):
        return True
    tokens = re.findall(r"[a-z]+", text)
    single_words = [variant for variant in variants if " " not in variant and len(variant) >= 5]
    return any(SequenceMatcher(None, token, variant).ratio() >= 0.9 for token in tokens for variant in single_words)


def detect_intent(
    message: str, recent_intents: list[str] | None = None
) -> tuple[str, float, bool]:
    text = normalize_message(message)
    recent_intents = recent_intents or []
    has_product_context = any(intent in PRODUCT_CONTEXT_INTENTS for intent in recent_intents[-4:])

    if _has(text, MEDICAL_WORDS):
        return "medical_or_sensitive", 0.98, True
    if _has(text, HUMAN_WORDS) or re.search(r"\bcs\b", text):
        return "human_request", 0.99, True
    if _has(text, ("refund", "refun", "refunf", "retur", "uang kembali", "balikin uang")):
        return "refund", 0.98, True
    if _has(text, ("barang tidak sesuai", "pesanan tidak sesuai", "tidak sesuai", "rusak", "bocor", "pecah", "salah barang", "barang kurang", "kurang", "komplain")) or _has(text, ANGRY_WORDS):
        return "complaint", 0.97, True

    if _has(text, ("terima kasih", "makasih", "trimakasih")):
        return "thanks", 0.98, False
    if _has(text, ("dadah", "sampai jumpa", "selamat tinggal", "bye")):
        return "goodbye", 0.97, False
    if _has(text, ("halo", "hai", "hi", "pagi", "siang", "sore", "malam")) and len(text.split()) <= 4:
        return "greeting", 0.96, False

    if re.search(r"\bgm[-\s]?\d+\b", text) or _has(text, ("pesanan", "resi", "lacak", "tracking", "cek order", "paket saya", "paket aku")):
        return "order_tracking", 0.97, False
    if _has(text, ("promo", "promosi", "diskon", "voucher", "potongan harga")):
        return "promotion_info", 0.95, False
    if _has(text, ("qris", "bayar", "pembayaran", "payment", "transfer", "e wallet", "cod", "bca", "bayar pakai apa")):
        return "payment_info", 0.96, False
    if _has(text, ("pengiriman", "kurir", "ongkir", "berapa hari", "sampai kapan", "dikirim")):
        return "shipping_info", 0.94, False

    if _has(text, ("paling murah", "termurah", "bandingkan", "perbandingan", "beda", "lebih bagus")):
        return "product_comparison", 0.95, False
    if _has(text, ("cara pakai", "cara penggunaan", "dipakai", "pemakaian", "urutan skincare")):
        return "product_usage", 0.95, False
    if _has(text, ("jual apa", "apa aja", "produk apa", "katalog", "mau beli", "mau belanja", "mau order")):
        return "product_discovery", 0.91, False
    if _has(text, ("stok", "tersedia")):
        return "stock_check", 0.94, False

    recommendation_signals = (
        "rekomendasi", "cocok", "kulit saya", "kulit aku", "di bawah", "maksimal",
        "budget", "anggaran", "berminyak", "kering", "sensitif", "kombinasi", "jerawat",
    )
    if _has(text, recommendation_signals):
        return "product_recommendation", 0.93 if has_product_context else 0.88, False
    if _has(text, ("harga", "berapa harganya", "kandungan", "manfaat", "moisturizer", "pelembap", "serum", "sunscreen", "cleanser", "toner")):
        return "product_info", 0.9, False

    if has_product_context and len(text.split()) <= 6:
        return "product_info", 0.7, False
    return "unknown", 0.45, False
