"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/sales", label: "Sales" },
  { href: "/inventory", label: "Inventory" },
  { href: "/products", label: "Products" },
  { href: "/suppliers", label: "Suppliers" },
  { href: "/procurement", label: "Procurement" },
  { href: "/expenses", label: "Expenses" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-ledger text-paper min-h-screen flex flex-col">
      <div className="px-5 py-6 border-b border-white/10">
        <div className="font-display text-xl leading-tight">BizMind</div>
        <div className="font-display text-sm text-gold-light tracking-wide">BD</div>
      </div>
      <nav className="flex-1 py-4">
        {NAV.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-5 py-2.5 text-sm border-l-2 ${
                active
                  ? "border-gold bg-white/5 text-white font-medium"
                  : "border-transparent text-paper/70 hover:text-white hover:bg-white/5"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-white/10 text-xs text-paper/50">
        Noor General Store
      </div>
    </aside>
  );
}
