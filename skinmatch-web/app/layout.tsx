import type { Metadata } from "next";
import { AppNav } from "@/components/AppNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkinMatch AI",
  description: "Analise formulas de skincare com base no seu perfil de pele.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
