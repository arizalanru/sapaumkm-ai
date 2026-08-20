"use client";

import { AlertCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getConversations, getDashboardStats, getProducts, resolveConversation, returnConversationToAI, sendAdminMessage, takeOverConversation } from "../../lib/api";
import type { Conversation, DashboardStats, Product } from "../../lib/types";
import { AdminInbox } from "../../components/admin/AdminInbox";
import { AdminKnowledge } from "../../components/admin/AdminKnowledge";
import { AdminOverview } from "../../components/admin/AdminOverview";
import { AdminProducts } from "../../components/admin/AdminProducts";
import { AdminSidebar, type AdminSection } from "../../components/admin/AdminSidebar";

export default function AdminPage() {
  const [section, setSection] = useState<AdminSection>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stats, setStats] = useState<DashboardStats>();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedId, setSelectedId] = useState<number>();
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [overviewError, setOverviewError] = useState("");
  const [conversationError, setConversationError] = useState("");
  const [productError, setProductError] = useState("");

  const refreshConversations = useCallback(async (selectPriority = false) => {
    const data = await getConversations();
    setConversations(data);
    if (selectPriority) {
      const priority = data.find((item) => item.status === "waiting_admin") || data.find((item) => item.status === "admin_active") || data[0];
      setSelectedId(priority?.id);
    }
    setConversationError("");
  }, []);

  useEffect(() => {
    let active = true;
    Promise.allSettled([getDashboardStats(), getConversations(), getProducts()]).then(([statsResult, conversationResult, productResult]) => {
      if (!active) return;
      if (statsResult.status === "fulfilled") setStats(statsResult.value); else setOverviewError("Layanan statistik tidak dapat dihubungi.");
      if (conversationResult.status === "fulfilled") {
        setConversations(conversationResult.value);
        const priority = conversationResult.value.find((item) => item.status === "waiting_admin") || conversationResult.value.find((item) => item.status === "admin_active") || conversationResult.value[0];
        setSelectedId(priority?.id);
      } else setConversationError("Layanan percakapan tidak dapat dihubungi.");
      if (productResult.status === "fulfilled") setProducts(productResult.value); else setProductError("Layanan produk tidak dapat dihubungi.");
      setLoading(false);
    });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    let polling = false;
    const poll = async () => {
      if (document.hidden || polling) return;
      polling = true;
      try { if (active) await refreshConversations(); } catch { if (active) setConversationError("Percakapan tidak dapat diperbarui."); } finally { polling = false; }
    };
    const timer = window.setInterval(poll, 2000);
    const resume = () => { if (!document.hidden) void poll(); };
    document.addEventListener("visibilitychange", resume);
    return () => { active = false; window.clearInterval(timer); document.removeEventListener("visibilitychange", resume); };
  }, [refreshConversations]);

  async function runTransition(action: () => Promise<Conversation>) {
    setActionLoading(true);
    setConversationError("");
    try {
      const updated = await action();
      setConversations((current) => current.map((conversation) => conversation.id === updated.id ? updated : conversation));
      const latestStats = await getDashboardStats();
      setStats(latestStats);
    } catch (error) {
      setConversationError("Status percakapan belum dapat diperbarui. Coba kembali.");
    } finally { setActionLoading(false); }
  }

  async function postAdminMessage(conversationId: number, content: string) {
    setActionLoading(true);
    try {
      const created = await sendAdminMessage(conversationId, content);
      setConversations((current) => current.map((conversation) => conversation.id === conversationId && !conversation.messages.some((message) => message.id === created.id) ? { ...conversation, messages: [...conversation.messages, created] } : conversation));
    } finally { setActionLoading(false); }
  }

  function changeSection(next: AdminSection) { setSection(next); setSidebarOpen(false); }

  return <main className="admin-page">
    <AdminSidebar section={section} onChange={changeSection} open={sidebarOpen} onToggle={() => setSidebarOpen((value) => !value)}/>
    <section className="admin-main">
      {conversationError && section === "inbox" && <div className="admin-error" role="alert"><AlertCircle size={17} aria-hidden="true"/>{conversationError}</div>}
      {section === "overview" && <AdminOverview stats={stats} loading={loading} error={overviewError}/>} 
      {section === "inbox" && <AdminInbox conversations={conversations} selectedId={selectedId} onSelect={setSelectedId} onTakeover={(id) => runTransition(() => takeOverConversation(id))} onResolve={(id) => runTransition(() => resolveConversation(id))} onReturnToAI={(id) => runTransition(() => returnConversationToAI(id))} onSendMessage={postAdminMessage} actionLoading={actionLoading}/>} 
      {section === "products" && <AdminProducts products={products} error={productError}/>} 
      {section === "knowledge" && <AdminKnowledge/>}
    </section>
  </main>;
}
