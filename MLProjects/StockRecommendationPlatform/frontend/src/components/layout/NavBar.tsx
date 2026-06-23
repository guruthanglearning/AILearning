"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useApiKey } from "@/contexts/ApiKeyContext";

const NAV_LINKS = [
  { href: "/", label: "Analysis" },
  { href: "/market-grid", label: "Market Grid" },
  { href: "/momentum", label: "Momentum" },
  { href: "/sector-heat", label: "Sector Heat" },
  { href: "/earnings", label: "Earnings" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/history", label: "History" },
  { href: "/watchlists", label: "Watchlists" },
  { href: "/alerts", label: "Alerts" },
  { href: "/logs", label: "Logs" },
  { href: "/settings", label: "Settings" },
  { href: "/keys", label: "API Keys" },
];

export function NavBar() {
  const pathname = usePathname();
  const { hasKey } = useApiKey();

  return (
    <nav className="sticky top-0 z-30 bg-gray-900 border-b border-gray-800 px-4 h-12 flex items-center gap-6">
      <span className="text-white font-semibold tracking-tight mr-4">StockResearch</span>
      {NAV_LINKS.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`text-sm transition-colors ${
            pathname === link.href
              ? "text-white font-medium"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          {link.label}
        </Link>
      ))}
      <div className="ml-auto flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${hasKey ? "bg-green-500" : "bg-red-500"}`}
          title={hasKey ? "API key configured" : "No API key — go to API Keys"}
        />
        <span className="text-xs text-gray-500">{hasKey ? "Key set" : "No key"}</span>
      </div>
    </nav>
  );
}
