import { AlertCircle, Package } from "lucide-react";
import type { Product } from "../../lib/types";
import { formatCurrency } from "../../lib/text";
import { EmptyState } from "../ui/EmptyState";

export function AdminProducts({ products, error }: { products: Product[]; error: string }) {
  return <div className="admin-content-scroll"><header className="section-heading"><div><span>Produk</span><h1>Katalog GlowMart</h1><p>Tampilan baca-saja dari basis data produk.</p></div></header>{error ? <EmptyState icon={AlertCircle} title="Produk tidak tersedia" description={error}/> : <div className="product-table-wrap"><table className="product-table"><thead><tr><th>Produk</th><th>Kategori</th><th>Tipe kulit</th><th>Harga</th><th>Stok</th></tr></thead><tbody>{products.map((product) => <tr key={product.id}><td><Package size={16} aria-hidden="true"/><span><strong>{product.name}</strong><small>{product.description}</small></span></td><td>{product.category}</td><td>{product.skin_type}</td><td>{formatCurrency(product.price)}</td><td>{product.stock}</td></tr>)}</tbody></table></div>}</div>;
}
