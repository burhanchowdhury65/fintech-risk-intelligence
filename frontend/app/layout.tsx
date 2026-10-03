import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Risk Intelligence",
  description: "Transaction risk analysis with an AI assistant that explains the result.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
