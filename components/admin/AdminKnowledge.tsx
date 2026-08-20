import { BookOpen } from "lucide-react";
import { EmptyState } from "../ui/EmptyState";

export function AdminKnowledge() {
  return <div className="admin-content-scroll"><header className="section-heading"><div><span>Basis Pengetahuan</span><h1>Pengetahuan layanan</h1><p>FAQ digunakan Sapa sebagai konteks jawaban yang terverifikasi.</p></div></header><EmptyState icon={BookOpen} title="Akses pengetahuan belum tersedia" description="Layanan server saat ini menggunakan FAQ untuk percakapan, tetapi belum menyediakan akses baca-saja untuk admin."/></div>;
}
