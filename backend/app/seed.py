from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Conversation, FAQ, Order, Product


PRODUCTS = [
    ("Aqua Calm Gel Moisturizer", "Moisturizer", "Gel ringan non-comedogenic dengan hyaluronic acid untuk menjaga kelembapan tanpa rasa lengket.", "Berminyak, kombinasi, sensitif", 89000, 24, "Gunakan pagi dan malam setelah serum."),
    ("Bright Dew Vitamin C Serum", "Serum", "Serum vitamin C untuk membantu kulit tampak cerah dan merata.", "Normal, kombinasi, berminyak", 119000, 18, "Gunakan 2-3 tetes pada pagi hari, lanjutkan sunscreen."),
    ("Barrier Rescue Ceramide Cream", "Moisturizer", "Krim ceramide untuk membantu merawat skin barrier yang kering.", "Kering, sensitif", 129000, 12, "Gunakan pagi dan malam sebagai pelembap terakhir."),
    ("Daily Shield Sunscreen SPF 50", "Sunscreen", "Sunscreen ringan SPF 50 PA++++ tanpa white cast.", "Semua jenis kulit", 99000, 31, "Aplikasikan dua ruas jari 15 menit sebelum aktivitas."),
    ("Gentle Cloud Cleanser", "Cleanser", "Pembersih wajah pH rendah yang lembut dan bebas scrub.", "Semua jenis kulit, sensitif", 69000, 40, "Pijat pada wajah basah 30-60 detik lalu bilas."),
    ("BHA Clear Pore Toner", "Toner", "Toner eksfoliasi BHA untuk membantu membersihkan pori.", "Berminyak, berjerawat", 109000, 15, "Gunakan malam hari 2-3 kali seminggu."),
    ("Cica Soothe Essence", "Essence", "Essence centella untuk menenangkan kulit yang terasa kemerahan.", "Sensitif, kombinasi", 95000, 21, "Tepuk perlahan setelah toner, pagi atau malam."),
    ("Niacinamide Balance Serum", "Serum", "Serum niacinamide 5% untuk membantu mengontrol minyak.", "Berminyak, kombinasi", 85000, 27, "Gunakan 2-3 tetes setelah toner."),
    ("Lipid Soft Cleansing Balm", "Cleanser", "Cleansing balm untuk mengangkat sunscreen dan makeup.", "Semua jenis kulit", 105000, 16, "Pijat pada wajah kering, emulsikan, lalu bilas."),
    ("Overnight Hydration Mask", "Mask", "Masker malam dengan panthenol untuk hidrasi tambahan.", "Normal, kering, sensitif", 115000, 9, "Gunakan tipis 2-3 kali seminggu sebagai langkah terakhir."),
]

FAQS = [
    ("payment", "Metode pembayaran apa yang tersedia?", "GlowMart menerima transfer bank BCA, QRIS, serta e-wallet GoPay, OVO, dan DANA."),
    ("payment", "Apakah bisa membayar dengan QRIS?", "Bisa. Pembayaran QRIS biasanya terverifikasi otomatis dalam 1-3 menit."),
    ("payment", "Apakah bisa membayar dengan COD?", "Saat ini GlowMart belum menyediakan pembayaran COD."),
    ("shipping", "Kurir apa yang digunakan?", "Pengiriman tersedia melalui J&T Express, JNE, SiCepat, dan AnterAja sesuai area."),
    ("shipping", "Berapa lama waktu pengiriman?", "Estimasi umum 1-3 hari kerja untuk Jabodetabek dan 3-7 hari kerja untuk luar Jabodetabek."),
    ("refund", "Bagaimana mengajukan refund?", "Hubungi admin maksimal 2x24 jam setelah paket diterima dengan video unboxing dan foto produk."),
    ("refund", "Bagaimana jika produk rusak?", "Jangan gunakan produk dan simpan kemasannya. Admin akan memeriksa bukti untuk penggantian atau refund."),
    ("usage", "Bagaimana urutan pemakaian skincare?", "Urutan dasar: cleanser, toner, serum, moisturizer, lalu sunscreen pada pagi hari."),
    ("policy", "Apakah produk yang sudah dibuka dapat dikembalikan?", "Produk yang sudah dibuka hanya dapat ditinjau untuk retur jika rusak, bocor, atau tidak sesuai pesanan."),
    ("policy", "Jam layanan admin GlowMart?", "Admin GlowMart tersedia setiap hari pukul 09.00-21.00 WIB."),
    ("promotion", "Apakah ada promo atau voucher?", "Saat ini belum ada promo atau voucher khusus yang tercatat. Admin dapat membantu mengecek penawaran terbaru."),
]

ORDERS = [
    ("GM-1001", "Andi Wijaya", "Daily Shield Sunscreen SPF 50", "Selesai", "JNE", "JNE77412001", "18 Agustus 2026"),
    ("GM-1002", "Rina Amelia", "Aqua Calm Gel Moisturizer", "Dalam perjalanan ke Cikarang", "J&T Express", "JT92817364", "22 Agustus 2026"),
    ("GM-1003", "Nadia Putri", "Gentle Cloud Cleanser", "Sedang dikemas", "SiCepat", "SC88192034", "23 Agustus 2026"),
    ("GM-1004", "Budi Santoso", "Barrier Rescue Ceramide Cream", "Menunggu penjemputan kurir", "AnterAja", "AA23918473", "24 Agustus 2026"),
    ("GM-1005", "Sari Wulandari", "Bright Dew Vitamin C Serum", "Dalam perjalanan ke Bandung", "J&T Express", "JT67192845", "22 Agustus 2026"),
]


def seed_database(db: Session) -> None:
    for conversation in db.scalars(select(Conversation)).all():
        customer_messages = [message for message in conversation.messages if message.sender == "customer"]
        assistant_messages = [message for message in conversation.messages if message.sender == "assistant"]
        has_admin_reply = any(message.sender == "admin" for message in conversation.messages)
        last_customer_intent = customer_messages[-1].intent if customer_messages else ""
        last_assistant_text = assistant_messages[-1].content.lower() if assistant_messages else ""
        legacy_escalation = (
            last_customer_intent in {"refund", "complaint", "human_request", "medical_or_sensitive"}
            and any(phrase in last_assistant_text for phrase in ("masuk ke antrean", "diteruskan ke admin", "terhubung ke admin"))
            and not has_admin_reply
        )
        if conversation.status == "active":
            conversation.status = "waiting_admin" if conversation.requires_human or legacy_escalation else "ai_active"
            conversation.requires_human = conversation.status == "waiting_admin"
        elif conversation.status == "ai_active" and not conversation.requires_human and legacy_escalation:
            # Repair records created by older builds that persisted escalation text
            # without the matching queue state. Current state transitions never
            # produce this mismatch.
            conversation.status = "waiting_admin"
            conversation.requires_human = True
    if db.scalar(select(func.count(Product.id))) == 0:
        db.add_all([Product(name=n, category=c, description=d, skin_type=s, price=p, stock=st, usage=u) for n, c, d, s, p, st, u in PRODUCTS])
    if db.scalar(select(func.count(FAQ.id))) == 0:
        db.add_all([FAQ(category=c, question=q, answer=a) for c, q, a in FAQS])
    else:
        existing_faqs = {faq.question: faq for faq in db.scalars(select(FAQ)).all()}
        db.add_all(
            FAQ(category=category, question=question, answer=answer)
            for category, question, answer in FAQS
            if question not in existing_faqs
        )
        for category, question, answer in FAQS:
            if question in existing_faqs:
                existing_faqs[question].category = category
                existing_faqs[question].answer = answer
    if db.scalar(select(func.count(Order.id))) == 0:
        db.add_all([Order(order_number=o, customer_name=c, product_name=p, status=s, courier=co, tracking_number=t, estimated_arrival=e) for o, c, p, s, co, t, e in ORDERS])
    else:
        gm_1002 = db.scalar(select(Order).where(Order.order_number == "GM-1002"))
        if gm_1002 and gm_1002.estimated_arrival == "22 August 2026":
            gm_1002.estimated_arrival = "22 Agustus 2026"
    db.commit()
