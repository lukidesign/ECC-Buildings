import type { Metadata } from "next";
import "./globals.css";
import "./explorer.css";

export const metadata: Metadata = {
  title: "Buildings | ECC",
  description: "ECC spatial explorer: discover connected buildings and modular power distribution.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg?v=ecc-brand",
    shortcut: "/favicon.svg?v=ecc-brand",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
