import type { Metadata } from "next";
import { Fustat, Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

const fustat = Fustat({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["400", "500", "700", "800"],
});

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GraphLens — Document Intelligence",
  description:
    "Upload your documents and get cited, graph-augmented answers from an AI that actually reasons across them.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${fustat.variable} ${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-white text-foreground">
        {children}
        <Toaster position="top-center" />
      </body>
    </html>
  );
}
