"use client";

import { CreditCard, Package, Search, ShoppingBag } from "lucide-react";

const suggestions = [
  { label: "Jelajahi katalog", message: "Jual produk apa saja yang tersedia?", icon: ShoppingBag },
  { label: "Cari rekomendasi", message: "Bantu rekomendasikan skincare untuk saya", icon: Search },
  { label: "Lacak pesanan", message: "Saya ingin melacak pesanan", icon: Package },
  { label: "Metode pembayaran", message: "Metode pembayaran apa saja yang tersedia?", icon: CreditCard },
];

export function SuggestionActions({ onSelect, disabled }: { onSelect: (message: string) => void; disabled: boolean }) {
  return <section className="suggestion-block" aria-label="Saran pertanyaan"><div><strong>Apa yang bisa kami bantu?</strong><p>Pilih topik atau tulis pertanyaan Anda di bawah.</p></div><div className="suggestion-grid">{suggestions.map(({ label, message, icon: Icon }) => <button key={label} onClick={() => onSelect(message)} disabled={disabled}><Icon size={17} aria-hidden="true"/><span>{label}</span></button>)}</div></section>;
}
