import React from 'react';

export type AuthStatus = {
  authenticated?: boolean;
  email?: string | null;
  providers?: Record<string, { connected: boolean; email?: string | null }>;
};

type Ctx = {
  status: AuthStatus;
  setStatus: (s: AuthStatus) => void;
  ready: boolean;
  setReady: (v: boolean) => void;
};

const AuthCtx = React.createContext<Ctx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = React.useState<AuthStatus>({ authenticated: false, providers: {} });
  const [ready, setReady] = React.useState(false);
  return <AuthCtx.Provider value={{ status, setStatus, ready, setReady }}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  const ctx = React.useContext(AuthCtx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
