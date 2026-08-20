export function localTime(date = new Date()) {
  return date.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta" });
}

export function formatDateTime(value: string) {
  const date = parseBackendDate(value);
  const datePart = date.toLocaleDateString("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Jakarta",
  });
  const timePart = date.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Jakarta",
  });
  return `${datePart}, ${timePart} WIB`;
}

export function formatShortTime(value: string) {
  return parseBackendDate(value).toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Jakarta",
  });
}

export function conversationDisplayName(conversation: { id: number; customer_name: string }) {
  const name = conversation.customer_name.trim();
  if (!name || /^(pelanggan(?: glowmart)?|customer|guest)$/i.test(name)) {
    return `Pelanggan #${conversation.id}`;
  }
  return name;
}

function parseBackendDate(value: string) {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasTimezone ? value : `${value}Z`);
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function cleanMessageText(text: string) {
  return text
    .replace(/\*\*([\s\S]*?)\*\*/g, "$1")
    .replace(/`/g, "")
    .replace(/[\u00a0\u202f\u2007]/g, " ")
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2212]/g, "-");
}

export function intentLabel(intent?: string) {
  const labels: Record<string, string> = {
    greeting: "Sapaan",
    product_discovery: "Jelajah produk",
    product_info: "Informasi produk",
    product_recommendation: "Rekomendasi produk",
    product_comparison: "Perbandingan produk",
    stock_check: "Cek stok",
    product_usage: "Cara pakai",
    order_tracking: "Pelacakan pesanan",
    payment_info: "Informasi pembayaran",
    shipping_info: "Pengiriman",
    promotion_info: "Promo",
    complaint: "Keluhan",
    refund: "Pengembalian dana",
    human_request: "Permintaan admin",
    thanks: "Terima kasih",
    goodbye: "Penutup",
    medical_or_sensitive: "Pertanyaan sensitif",
    unknown: "Lainnya",
  };
  return intent ? labels[intent] || intent : "Belum tersedia";
}
