import { AlertCircle, CheckCircle, Clock, MessageCircle, Users } from "lucide-react";
import type { DashboardStats } from "../../lib/types";
import { intentLabel } from "../../lib/text";
import { EmptyState } from "../ui/EmptyState";
import { LoadingState } from "../ui/LoadingState";

export function AdminOverview({ stats, loading, error }: { stats?: DashboardStats; loading: boolean; error: string }) {
  if (loading) return <LoadingState label="Memuat ringkasan"/>;
  if (!stats || error) return <EmptyState icon={AlertCircle} title="Ringkasan tidak tersedia" description={error || "Layanan server belum mengirim statistik."}/>;
  const totalIntents = Object.values(stats.intent_distribution).reduce((sum, count) => sum + count, 0) || 1;
  const intents = Object.entries(stats.intent_distribution).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const estimatedHours = ((stats.resolved_by_ai * 2) / 60).toLocaleString("id-ID", { maximumFractionDigits: 1 });
  const metrics = [
    { label: "Total percakapan", value: stats.total_conversations, detail: "Data tersimpan", icon: MessageCircle },
    { label: "Tingkat resolusi AI", value: `${stats.automation_rate}%`, detail: `${stats.resolved_by_ai} percakapan`, icon: CheckCircle },
    { label: "Rata-rata respons", value: `${stats.average_response_seconds.toLocaleString("id-ID")} dtk`, detail: "Nilai prototipe", icon: Clock },
    { label: "Alih layanan ke admin", value: stats.requires_human, detail: "Perlu perhatian", icon: Users },
  ];
  return <div className="admin-content-scroll">
    <header className="section-heading"><div><span>Ringkasan</span><h1>Operasional layanan pelanggan</h1><p>Ringkasan percakapan GlowMart yang tersimpan di layanan server.</p></div></header>
    <section className="metric-grid">{metrics.map(({ label, value, detail, icon: Icon }) => <article key={label}><div><span>{label}</span><Icon size={18} aria-hidden="true"/></div><strong>{value}</strong><small>{detail}</small></article>)}</section>
    <section className="overview-grid">
      <article className="panel intent-panel"><div className="panel-heading"><div><h2>Distribusi topik</h2><p>Berdasarkan pesan pelanggan tersimpan</p></div></div>{intents.length ? <div className="intent-list">{intents.map(([intent, count]) => { const percentage = Math.round((count / totalIntents) * 100); return <div key={intent}><div><span>{intentLabel(intent)}</span><strong>{percentage}%</strong></div><i><b style={{ width: `${percentage}%` }}/></i></div>; })}</div> : <p className="muted-copy">Belum ada percakapan untuk dianalisis.</p>}</article>
      <article className="panel impact-panel"><div className="panel-heading"><div><h2>Estimasi dampak</h2><p>Perkiraan, bukan metrik waktu aktual</p></div></div><div className="impact-value"><strong>{estimatedHours} jam</strong><span>estimasi waktu admin dihemat</span></div><p>Perhitungan demonstrasi menggunakan asumsi 2 menit per percakapan yang diselesaikan AI.</p><div className="impact-note"><AlertCircle size={17} aria-hidden="true"/><span>Tandai metrik estimasi secara jelas saat dipresentasikan.</span></div></article>
    </section>
  </div>;
}
