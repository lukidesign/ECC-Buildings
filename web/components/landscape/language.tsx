"use client";
import { useCallback, useEffect, useState } from "react";
import { LANGUAGE_STORAGE_KEY, readSavedLocale, resolveLocale, translate, type Locale } from "./translations";

export function useLanguage() {
  // Match SSR on the initial render; read browser preferences only after hydration.
  const [locale, setLocale] = useState<Locale>("en");
  useEffect(() => {
    let saved: string | null = null;
    try { saved = readSavedLocale(localStorage); } catch { /* Access to localStorage itself may be disabled. */ }
    setLocale(resolveLocale(saved, navigator.language));
  }, []);
  useEffect(() => { document.documentElement.lang = locale === "zh" ? "zh-CN" : "en"; }, [locale]);
  const selectLocale = useCallback((next: Locale) => {
    setLocale(next);
    try { localStorage.setItem(LANGUAGE_STORAGE_KEY, next); } catch { /* Switching still works in memory. */ }
  }, []);
  const t = useCallback((text: string) => translate(locale, text), [locale]);
  return { locale, selectLocale, t };
}

export function LanguageSwitch({ locale, onChange }: { locale: Locale; onChange: (locale: Locale) => void }) {
  return <div className="language-switch" role="group" aria-label="Language / 语言">
    <button type="button" lang="zh-CN" aria-label="切换为中文" aria-pressed={locale === "zh"} onClick={() => onChange("zh")}>中文</button>
    <span aria-hidden="true">/</span>
    <button type="button" lang="en" aria-label="Switch to English" aria-pressed={locale === "en"} onClick={() => onChange("en")}>EN</button>
  </div>;
}
