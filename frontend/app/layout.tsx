import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuMind — Document Intelligence Workspace",
  description:
    "Upload a text-based PDF or DOCX and get a normalized result: document type, summary, and structured fields.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <div className="mx-auto flex min-h-screen max-w-4xl flex-col px-4 py-6 sm:px-6 sm:py-10">
          <header className="mb-8 border-b border-slate-200 pb-5">
            <Link href="/" className="inline-flex flex-col">
              <span className="text-xl font-semibold tracking-tight text-slate-900">
                DocuMind
              </span>
              <span className="text-sm text-slate-500">
                Document Intelligence Workspace
              </span>
            </Link>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="mt-12 border-t border-slate-200 pt-4 text-xs text-slate-400">
            Portfolio demo. Documents are analyzed synchronously on upload; original
            files are not stored.
          </footer>
        </div>
      </body>
    </html>
  );
}
