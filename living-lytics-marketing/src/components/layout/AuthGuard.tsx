import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchAuthStatus, hasAnyConnection, isOnboardingDone } from '../../lib/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = React.useState(false);
  const nav = useNavigate();
  const loc = useLocation();

  React.useEffect(() => {
    (async () => {
      const status = await fetchAuthStatus();
      const isAuthed = !!status?.authenticated;

      if (!isAuthed) { 
        setReady(true); 
        return; 
      }

      const onboarded = isOnboardingDone();
      const hasConn = hasAnyConnection(status);

      if (!onboarded && !loc.pathname.startsWith('/onboarding')) {
        nav('/onboarding', { replace: true });
      } else if (onboarded && !hasConn && !loc.pathname.startsWith('/connect')) {
        nav('/connect', { replace: true });
      } else if (onboarded && hasConn && loc.pathname === '/signin') {
        nav('/dashboard', { replace: true });
      }

      setReady(true);
    })();
  }, [nav, loc.pathname]);

  if (!ready) return null;
  return <>{children}</>;
}
