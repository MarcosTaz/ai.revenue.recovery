import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GovMargin — Government Contract Economic Assurance",
  description: "Evidence-first earned, billed and paid reconciliation for U.S. federal contractors.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
