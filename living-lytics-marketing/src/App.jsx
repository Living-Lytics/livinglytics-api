import React from 'react'
import './App.css'
import Pages from "@/pages/index.jsx"
import { Toaster } from "@/components/ui/toaster"
import SignInModal from "@/components/auth/SignInModal"
import { ThemeProvider } from '@/state/theme'
import { AuthProvider, useAuth } from '@/state/auth'
import { fetchAuthStatus } from '@/lib/auth'

function AuthBootstrap({ children }) {
  const { setStatus, setReady } = useAuth();
  React.useEffect(() => {
    (async () => {
      const s = await fetchAuthStatus();
      setStatus(s);
      setReady(true);
    })();
  }, [setStatus, setReady]);
  return <>{children}</>;
}

function GlobalCtaInterceptor() {
  const { status } = useAuth();
  const isAuthed = !!status?.authenticated;

  React.useEffect(() => {
    if (isAuthed) return;
    const handler = async (e) => {
      const target = e.target;
      const clickable = target?.closest('a,button,[data-auth-cta="true"]');
      if (!clickable) return;

      const txt = (clickable.textContent || '').trim().toLowerCase();
      const isCta = ['sign in','get started free','start your free account','start free trial','get started free trial','connect your first source'].includes(txt)
        || clickable.getAttribute('data-auth-cta') === 'true';
      if (!isCta) return;

      e.preventDefault();
      e.stopPropagation();
      
      const SignInModal = document.querySelector('[data-sign-in-modal]');
      if (SignInModal) {
        SignInModal.click();
      }
    };
    document.addEventListener('click', handler, true);
    return () => document.removeEventListener('click', handler, true);
  }, [isAuthed]);

  return null;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AuthBootstrap>
          <GlobalCtaInterceptor />
          <Pages />
          <Toaster />
          <SignInModal />
        </AuthBootstrap>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App 