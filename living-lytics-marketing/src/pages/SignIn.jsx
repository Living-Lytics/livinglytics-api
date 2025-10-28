import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthStatus } from '@/lib/api';
import SignInForm from '@/components/auth/SignInForm';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

export default function SignIn() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const status = await getAuthStatus();
      // Check if user is authenticated (has any connected accounts or a session)
      const hasAuth = status && (status.google || status.instagram || status.authenticated);
      
      if (hasAuth) {
        setIsAuthenticated(true);
        // Redirect to connect page if already authenticated
        navigate('/connect');
      }
    } catch (err) {
      console.error('Error checking auth status:', err);
    } finally {
      setChecking(false);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-[#F8F9FB] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#3C3CE0]" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FB] py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Side - Branding & Benefits */}
          <div className="hidden lg:block">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full"></div>
              </div>
              <h1 className="text-3xl font-bold text-[#1E1E2F]">Living Lytics</h1>
            </div>

            <h2 className="text-4xl font-bold text-[#1E1E2F] mb-6">
              Turn Your Business Data Into Actionable Growth
            </h2>

            <p className="text-lg text-gray-600 mb-8">
              Connect marketing, sales and web data to get clear, AI-driven recommendations.
            </p>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-green-600 text-sm">✓</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[#1E1E2F] mb-1">Connect in minutes</h3>
                  <p className="text-gray-600">No credit card required. Setup takes less than 5 minutes.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-green-600 text-sm">✓</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[#1E1E2F] mb-1">Automatic data sync</h3>
                  <p className="text-gray-600">We automatically backfill 30 days of historical data.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="text-green-600 text-sm">✓</span>
                </div>
                <div>
                  <h3 className="font-semibold text-[#1E1E2F] mb-1">AI-powered insights</h3>
                  <p className="text-gray-600">Get actionable recommendations to grow your business.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side - Sign In Form */}
          <div>
            <div className="bg-white rounded-2xl shadow-lg p-8 lg:p-10">
              {isAuthenticated && (
                <Alert className="mb-6 border-blue-200 bg-blue-50">
                  <AlertDescription className="text-blue-800">
                    You're already signed in! Redirecting to your dashboard...
                  </AlertDescription>
                </Alert>
              )}

              <div className="mb-6 lg:hidden">
                <h2 className="text-2xl font-bold text-[#1E1E2F] mb-2">Welcome to Living Lytics</h2>
                <p className="text-gray-600">Sign in or create your account to get started.</p>
              </div>

              <SignInForm onSuccess={() => navigate('/connect')} />
            </div>

            <p className="text-center text-sm text-gray-500 mt-6">
              By signing up, you agree to our{' '}
              <a href="#" className="text-[#3C3CE0] hover:underline">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-[#3C3CE0] hover:underline">Privacy Policy</a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
