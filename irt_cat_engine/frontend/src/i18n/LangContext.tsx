import { createContext, useContext, useState, useCallback } from "react";
import type { Lang } from "./translations";

interface LangContextValue {
  lang: Lang;
  toggle: () => void;
}

const LangContext = createContext<LangContextValue>({
  lang: "ko",
  toggle: () => {},
});

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try {
      const saved = localStorage.getItem("irt-lang");
      if (saved === "en" || saved === "ko") return saved;
    } catch { /* ignore */ }
    return "ko";
  });

  const toggle = useCallback(() => {
    setLang((prev) => {
      const next = prev === "ko" ? "en" : "ko";
      try { localStorage.setItem("irt-lang", next); } catch { /* ignore */ }
      return next;
    });
  }, []);

  return (
    <LangContext.Provider value={{ lang, toggle }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
