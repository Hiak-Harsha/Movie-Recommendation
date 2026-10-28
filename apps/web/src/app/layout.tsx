import type { Metadata } from "next";
import Providers from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CineMatch — Find your next favourite film.",
  description: "Pick a few movies you love. We'll do the rest.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0b0b0c] text-[#f2efe6] antialiased flex flex-col font-sans selection:bg-[#f5a524]/30 selection:text-[#f2efe6]">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
