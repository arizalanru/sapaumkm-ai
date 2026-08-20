import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SapaUMKM AI",
  description: "Asisten layanan pelanggan cerdas untuk UMKM Indonesia.",
  other: { "codex-preview": "development" },
  openGraph: {
    title: "SapaUMKM AI",
    description: "Asisten layanan pelanggan cerdas untuk UMKM Indonesia.",
    images: ["/og.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "SapaUMKM AI",
    description: "Asisten layanan pelanggan cerdas untuk UMKM Indonesia.",
    images: ["/og.png"],
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="id"><body>{children}</body></html>;
}
