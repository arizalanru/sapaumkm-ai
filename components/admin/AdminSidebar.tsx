"use client";

import { BookOpen, Inbox, LayoutDashboard, Menu, ShoppingBag, User, X } from "lucide-react";

export type AdminSection = "overview" | "inbox" | "products" | "knowledge";
const items = [
  { id: "overview" as const, label: "Ringkasan", icon: LayoutDashboard },
  { id: "inbox" as const, label: "Kotak Masuk", icon: Inbox },
  { id: "products" as const, label: "Produk", icon: ShoppingBag },
  { id: "knowledge" as const, label: "Basis Pengetahuan", icon: BookOpen },
];

export function AdminSidebar({ section, onChange, open, onToggle }: { section: AdminSection; onChange: (section: AdminSection) => void; open: boolean; onToggle: () => void }) {
  return <><button className="admin-menu-button" onClick={onToggle} aria-label={open ? "Tutup navigasi" : "Buka navigasi"}>{open ? <X size={20} aria-hidden="true"/> : <Menu size={20} aria-hidden="true"/>}</button><aside className={`admin-sidebar ${open ? "sidebar-open" : ""}`}><div className="admin-brand"><span className="brand-mark" aria-hidden="true">G</span><div><strong>Dukungan GlowMart</strong><span>Ruang kerja operator</span></div></div><nav aria-label="Navigasi admin">{items.map(({ id, label, icon: Icon }) => <button key={id} className={section === id ? "active" : ""} onClick={() => onChange(id)}><Icon size={18} aria-hidden="true"/>{label}</button>)}</nav><a className="customer-view-link" href="/"><User size={17} aria-hidden="true"/>Tampilan Pelanggan</a></aside>{open && <button className="sidebar-backdrop" aria-label="Tutup navigasi" onClick={onToggle}/> }</>;
}
