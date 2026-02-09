import { Zap } from "lucide-react";
import React from "react";

import { ThemeToggle } from "./ThemeToggle";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen relative bg-[var(--bg-canvas)] overflow-hidden">
      {/* Decorative background blobs */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-50 dark:opacity-30">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[var(--accent)] blur-[120px] mix-blend-soft-light" />
        <div className="absolute bottom-[10%] right-[0%] w-[30%] h-[30%] rounded-full bg-[var(--accent)] blur-[100px] mix-blend-soft-light" />
      </div>

      <header className="sticky top-0 z-20 border-b border-[var(--border-subtle)] bg-[var(--surface-1)]/90 backdrop-blur-md">
        <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-4 py-3 md:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)] text-[var(--accent)] shadow-sm">
              <Zap className="h-5 w-5 fill-current" />
            </div>
            <div>
              <p className="text-sm font-bold tracking-tight text-[var(--text-primary)]">LLMinate</p>
              <p className="text-[10px] font-medium uppercase tracking-wider text-[var(--text-muted)]">AI Optimizer</p>
            </div>
          </div>

          <nav className="flex items-center gap-6 text-sm font-medium">
            <a href="#" className="hidden md:block text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]">
              Docs
            </a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="hidden md:block text-[var(--text-muted)] transition-colors hover:text-[var(--text-primary)]"
            >
              GitHub
            </a>
            <div className="hidden md:block h-4 w-px bg-[var(--border-subtle)]" />
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-[1600px] px-4 py-4 md:px-6 md:py-6">
        {children}
      </main>
    </div>
  );
}
