import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';
type Ctx = { theme: Theme; setTheme: (t: Theme) => void; toggle: () => void; };
const ThemeCtx = createContext<Ctx | null>(null);

function getStored(): Theme {
  const t = localStorage.getItem('ll_theme');
  return (t === 'dark' || t === 'light') ? t : 'light';
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getStored());

  useEffect(() => {
    localStorage.setItem('ll_theme', theme);
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('dark'); else root.classList.remove('dark');
  }, [theme]);

  const setTheme = (t: Theme) => setThemeState(t);
  const toggle = () => setThemeState(prev => prev === 'dark' ? 'light' : 'dark');

  return <ThemeCtx.Provider value={{ theme, setTheme, toggle }}>{children}</ThemeCtx.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeCtx);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
