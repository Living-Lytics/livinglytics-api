import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function ConnectCallback() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();

  React.useEffect(() => {
    const tokenParam = searchParams.get('token');
    
    if (tokenParam) {
      localStorage.setItem('ll_token', tokenParam);
    }

    const onboarded = localStorage.getItem('ll_onboarding_done') === '1';
    const target = onboarded ? '/connect' : '/onboarding';
    
    nav(target, { replace: true });
  }, [nav, searchParams]);

  return (
    <div className="min-h-screen bg-[#F8F9FB] flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-8 h-8 animate-spin text-[#3C3CE0]" />
        <p className="text-gray-600">Processing connection...</p>
      </div>
    </div>
  );
}
