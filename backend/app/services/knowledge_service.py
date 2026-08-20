import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import FAQ, Product
from .intent_service import normalize_message


STOPWORDS = {"yang", "dan", "untuk", "dengan", "apa", "apakah", "bisa", "saya", "kak", "di", "ke", "dari", "ini", "itu", "ada", "mau"}
SKIN_TYPE_ALIASES = {
    "berminyak": ("berminyak",),
    "kering": ("kering",),
    "sensitif": ("sensitif",),
    "kombinasi": ("kombinasi",),
    "normal": ("normal",),
    "berjerawat": ("berjerawat", "jerawat", "acne"),
}


@dataclass
class KnowledgeResult:
    products: list[Product]
    faqs: list[FAQ]
    filter_note: str = ""


def _keywords(message: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", normalize_message(message)) if len(w) > 2 and w not in STOPWORDS}


def _score(text: str, words: set[str]) -> int:
    haystack = text.lower()
    return sum(1 for word in words if word in haystack)


def retrieve_knowledge(
    db: Session,
    message: str,
    intent: str,
    conversation_context: str = "",
    reference_context: str = "",
) -> KnowledgeResult:
    normalized_message = normalize_message(message)
    normalized_context = normalize_message(conversation_context)
    normalized_references = normalize_message(reference_context)
    retrieval_text = f"{normalized_message} {normalized_context} {normalized_references}".strip()
    words = _keywords(retrieval_text)
    all_products = list(db.scalars(select(Product).order_by(Product.category, Product.name)).all())
    available_products = [product for product in all_products if product.stock > 0]
    products = available_products[:]
    faqs = list(db.scalars(select(FAQ)).all())

    budget_match = re.search(r"(?:rp\s*)?(\d{2,3}(?:[.\s]\d{3})+|\d{5,7})", normalized_message)
    short_budget_match = re.search(r"\b(\d{2,4})\s*(?:ribu(?:an)?|rb)\b", normalized_message)
    maximum_price = int(short_budget_match.group(1)) * 1000 if short_budget_match else None
    if budget_match and any(word in normalized_message for word in ("bawah", "maksimal", "budget", "anggaran")):
        maximum_price = int(re.sub(r"\D", "", budget_match.group(1)))
    requested_skin_types = {
        canonical
        for canonical, aliases in SKIN_TYPE_ALIASES.items()
        if any(alias in f"{normalized_message} {normalized_context}" for alias in aliases)
    }
    skin_suitable_products = products
    if requested_skin_types:
        skin_suitable_products = [
            product
            for product in products
            if any(skin_type in product.skin_type.lower() for skin_type in requested_skin_types)
        ]
        products = skin_suitable_products

    filter_note = ""
    if maximum_price is not None:
        products = [product for product in products if product.price <= maximum_price]
        if intent == "product_recommendation" and requested_skin_types and not products:
            above_budget = [
                product for product in skin_suitable_products if product.price > maximum_price
            ]
            if above_budget:
                nearest = min(above_budget, key=lambda product: product.price)
                skin_label = ", ".join(sorted(requested_skin_types))
                formatted_budget = f"{maximum_price:,.0f}".replace(",", ".")
                formatted_price = f"{nearest.price:,.0f}".replace(",", ".")
                filter_note = (
                    f"Tidak ada produk yang cocok untuk kulit {skin_label} dengan budget maksimal "
                    f"Rp{formatted_budget}. Pilihan sesuai terdekat di atas budget adalah "
                    f"{nearest.name} seharga Rp{formatted_price}. Tanyakan apakah pelanggan ingin "
                    "menaikkan budget atau melihat produk umum di bawah budget tersebut."
                )
                products = [nearest]

    reference_matches = sorted(
        [product for product in all_products if product.name.lower() in normalized_references],
        key=lambda product: normalized_references.rfind(product.name.lower()),
        reverse=True,
    )
    searchable_products = all_products if intent in {"product_info", "stock_check", "product_usage"} else products
    product_scores = [(_score(" ".join((p.name, p.category, p.description, p.skin_type, p.usage)), words), p) for p in searchable_products]
    current_words = _keywords(message)
    explicit_product_scores = [
        (_score(" ".join((p.name, p.category, p.description)), current_words), p)
        for p in searchable_products
    ]
    explicit_matches = [
        product
        for score, product in sorted(explicit_product_scores, key=lambda item: (-item[0], item[1].id))
        if score >= 2
    ]
    faq_scores = [(_score(" ".join((f.category, f.question, f.answer)), words), f) for f in faqs]

    limit = 6 if intent in {"product_discovery", "product_comparison"} else 3
    matched_products = [p for score, p in sorted(product_scores, key=lambda item: (-item[0], item[1].id)) if score > 0][:limit]
    matched_faqs = [f for score, f in sorted(faq_scores, key=lambda item: (-item[0], item[1].id)) if score > 0][:3]

    if intent in {"payment_info", "shipping_info", "promotion_info", "refund"}:
        matched_products = []

    if intent == "product_discovery":
        matched_products = explicit_matches[:1] if explicit_matches else products[:6]
    elif intent in {"product_comparison", "product_usage", "stock_check", "product_info"} and explicit_matches:
        matched_products = explicit_matches[:limit]
    elif intent in {"product_comparison", "product_usage", "stock_check", "product_info"} and reference_matches:
        matched_products = reference_matches[:limit]
    elif intent == "product_recommendation" and not matched_products:
        matched_products = products[:3]
    if intent in {"product_discovery", "product_recommendation", "product_comparison", "product_usage", "stock_check", "product_info"}:
        # Recommendations are grounded exclusively in the selected product
        # rows; unrelated FAQ text is deliberately excluded from the prompt.
        matched_faqs = []
    if intent == "payment_info":
        matched_faqs = [faq for faq in faqs if faq.category == "payment"][:4]
    elif intent in {"shipping_info", "refund", "promotion_info"} and not matched_faqs:
        category = {"payment_info": "payment", "shipping_info": "shipping", "refund": "refund", "promotion_info": "promotion"}[intent]
        matched_faqs = [f for f in faqs if f.category == category][:3]
    return KnowledgeResult(matched_products, matched_faqs, filter_note)


def build_context(products: list[Product], faqs: list[FAQ]) -> str:
    lines: list[str] = []
    for p in products:
        formatted_price = f"{p.price:,.0f}".replace(",", ".")
        lines.append(
            f"PRODUCT | nama={p.name} | harga=Rp{formatted_price} | stok={p.stock} "
            f"| kategori={p.category} | deskripsi={p.description} "
            f"| tipe_kulit={p.skin_type} | pemakaian={p.usage}"
        )
    for faq in faqs:
        lines.append(f"FAQ | kategori={faq.category} | pertanyaan={faq.question} | jawaban={faq.answer}")
    return "\n".join(lines[:6])
