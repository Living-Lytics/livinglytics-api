import React from 'react';
import { useTheme } from '../state/theme';

export default function Settings() {
  const { theme, toggle } = useTheme();

  return (
    <div className="px-4 py-6 mx-auto max-w-3xl">
      <h1 className="text-2xl font-semibold mb-6">Settings</h1>
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Theme</div>
            <div className="text-sm text-slate-500">Switch between light and dark mode</div>
          </div>
          <button onClick={toggle} className="rounded-lg px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700">
            {theme === 'dark' ? 'Use Light' : 'Use Dark'}
          </button>
        </div>
        <div className="border-t border-slate-200 dark:border-slate-800 pt-4 text-sm">
          <a href="/billing" className="text-indigo-600 hover:text-indigo-700">Manage plan & payment</a>
        </div>
      </div>
    </div>
  );
}
