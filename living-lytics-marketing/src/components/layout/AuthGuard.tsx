import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { hasAnyConnection } from '../../lib/auth';
import { useAuth } from '../../state/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { status, ready } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  const lastRedirectRef = React.useRef<string>('');

  React.useEffect(() => {
    if (!ready) return;
    const isAuthed = !!status?.authenticated;
    const connected = hasAnyConnection(status);

    const appRoutes = ['/dashboard', '/connect', '/settings', '/insights', '/onboarding'];
    const isAppRoute = appRoutes.some(route => loc.pathname.startsWith(route));

    if (!isAuthed) {
      if (isAppRoute && loc.pathname !== '/signin') {
        if (lastRedirectRef.current === '/signin') return;
        lastRedirectRef.current = '/signin';
        nav('/signin', { replace: true });
      }
      return;
    }

    const onboarded = localStorage.getItem('ll_onboarding_done') === '1';

    if (!onboarded && !loc.pathname.startsWith('/onboarding')) {
      if (lastRedirectRef.current === '/onboarding') return;
      lastRedirectRef.current = '/onboarding';
      nav('/onboarding', { replace: true });
      return;
    }

    if (onboarded && !connected && !loc.pathname.startsWith('/connect')) {
      if (lastRedirectRef.current === '/connect') return;
      lastRedirectRef.current = '/connect';
      nav('/connect', { replace: true });
      return;
    }

    if (onboarded && connected && loc.pathname === '/signin') {
      if (lastRedirectRef.current === '/dashboard') return;
      lastRedirectRef.current = '/dashboard';
      nav('/dashboard', { replace: true });
      return;
    }

    lastRedirectRef.current = '';
  }, [ready, status, loc.pathname, nav]);

  if (!ready) return null;
  return <>{children}</>;
}
