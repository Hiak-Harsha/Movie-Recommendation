import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Providers from "@/components/Providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "CineMatch — Hybrid Movie Recommendation Intelligence",
  description: "Production movie recommendation engine combining explicit ALS matrix factorization, shrunk Item-kNN, and TF-IDF content vectors with honest statistical evaluation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} dark`}>
      <body className="min-h-screen bg-[#0b0b0c] text-[#f4f4f5] antialiased flex flex-col font-sans selection:bg-amber-500 selection:text-black">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
