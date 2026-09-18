import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "../components/Navbar";
import { VoiceAssistant } from "../components/VoiceAssistant";

export const metadata: Metadata = {
  title: "VoiceNav AI - Multilingual Voice Navigation (English & Marathi)",
  description: "AI-driven virtual voice assistant for web navigation in English and Marathi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main>{children}</main>
        <VoiceAssistant />
      </body>
    </html>
  );
}
