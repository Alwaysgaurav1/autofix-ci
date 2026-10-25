import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoFix CI — Autonomous CI/CD Remediation Agent",
  description: "Powered by NVIDIA Nemotron on Nebius Token Factory",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-[#0b0f19] text-slate-100">
        {children}
      </body>
    </html>
  );
}
