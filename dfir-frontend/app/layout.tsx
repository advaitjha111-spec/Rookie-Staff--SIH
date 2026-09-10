import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter, Noto_Sans_Devanagari, Newsreader, Space_Grotesk } from "next/font/google";
import { Providers } from "@/components/ui/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "700"], variable: "--font-mono" });
const devanagari = Noto_Sans_Devanagari({ subsets: ["devanagari"], variable: "--font-devanagari" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-newsreader", style: ['normal', 'italic'] });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk" });

export const metadata: Metadata = { title: "PRATIKRIYA | DFIR Workbench", description: "Air-gapped digital forensics and incident response analysis." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body suppressHydrationWarning className={`${inter.variable} ${mono.variable} ${devanagari.variable} ${newsreader.variable} ${spaceGrotesk.variable}`}><Providers>{children}</Providers></body></html>;
}
