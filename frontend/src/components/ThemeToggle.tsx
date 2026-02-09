import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("theme");
      if (saved === "light" || saved === "dark") return saved;
      return document.documentElement.classList.contains("dark") ? "dark" : "light";
    }
    return "light";
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      root.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [theme]);

  return (
    <button
      onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
      className="group relative flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-2)]/50 text-[var(--text-muted)] backdrop-blur-sm transition-all hover:bg-[var(--accent-soft)] hover:text-[var(--accent)] hover:border-[var(--accent-border)] active:scale-95"
      title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      type="button"
    >
      <div className="relative h-4 w-4">
        {theme === "light" ? (
          <Moon size={16} className="transition-all" />
        ) : (
          <Sun size={16} className="transition-all" />
        )}
      </div>
    </button>
  );
}
