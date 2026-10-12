"use client";

import { useRouter } from "next/navigation";
import { tokenStore } from "@/lib/api";

export default function Topbar({ title }: { title: string }) {
  const router = useRouter();

  function logout() {
    tokenStore.clear();
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-line px-8 py-5">
      <h1 className="font-display text-2xl text-ink">{title}</h1>
      <button
        onClick={logout}
        className="text-sm text-ink/60 hover:text-ink border border-line px-3 py-1.5"
      >
        Sign out
      </button>
    </header>
  );
}
