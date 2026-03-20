import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Local Claude Assistant",
  description: "Local-first ChatGPT-like MVP with Anthropic Claude",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
