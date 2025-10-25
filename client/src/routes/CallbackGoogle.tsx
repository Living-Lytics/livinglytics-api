import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/Toast';

export const CallbackGoogle = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (error) {
      setStatus('error');
      toast('Failed to connect Google Analytics', 'error');
      setTimeout(() => navigate('/connections'), 2000);
      return;
    }

    if (code) {
      // OAuth successful - backend will handle the token exchange
      setStatus('success');
      toast('Google Analytics connected successfully!', 'success');
      setTimeout(() => navigate('/connections'), 1000);
    } else {
      setStatus('error');
      toast('Invalid OAuth response', 'error');
      setTimeout(() => navigate('/connections'), 2000);
    }
  }, [navigate, toast]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
        {status === 'loading' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Finalizing connection...</h2>
            <p className="text-gray-600">Please wait while we complete the setup.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <svg className="w-16 h-16 text-green-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connected successfully!</h2>
            <p className="text-gray-600">Redirecting...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <svg className="w-16 h-16 text-red-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection failed</h2>
            <p className="text-gray-600">Redirecting to connections...</p>
          </>
        )}
      </div>
    </div>
  );
};
