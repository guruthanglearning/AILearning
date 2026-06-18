import type { Metadata } from "next";
import "./globals.css";

import { DisclaimerBanner } from "@/components/layout/DisclaimerBanner";
import { NavBar } from "@/components/layout/NavBar";
import { Providers } from "@/components/layout/Providers";

export const metadata: Metadata = {
  title: "StockResearch Platform",
  description: "Multi-agent stock research tool — not investment advice",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <Providers>
          <NavBar />
          <DisclaimerBanner />
          <main className="max-w-screen-2xl mx-auto px-4 py-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
