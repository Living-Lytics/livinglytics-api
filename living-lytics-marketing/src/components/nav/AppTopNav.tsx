import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTheme } from '../../state/theme';

export default function AppTopNav({ email }: { email?: string | null }) {
  const nav = useNavigate();
  const { theme } = useTheme();

  async function logout() {
    try { await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' }); } catch {}
    window.location.assign('/');
  }

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/dashboard" className="font-semibold text-slate-900 dark:text-white">Living Lytics</Link>
          <nav className="hidden md:flex items-center gap-4 text-sm">
            <Link to="/dashboard" className="hover:text-indigo-600 dark:hover:text-teal-400">Dashboard</Link>
            <Link to="/connect" className="hover:text-indigo-600 dark:hover:text-teal-400">Connections</Link>
            <Link to="/insights" className="hover:text-indigo-600 dark:hover:text-teal-400">Insights</Link>
            <Link to="/settings" className="hover:text-indigo-600 dark:hover:text-teal-400">Settings</Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => nav('/settings')} className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800" title="Settings">
            ⚙️
          </button>
          <button onClick={logout} className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800" title="Logout">
            ⎋
          </button>
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-600 to-teal-400" title={email || 'Profile'} />
        </div>
      </div>
    </header>
  );
}
