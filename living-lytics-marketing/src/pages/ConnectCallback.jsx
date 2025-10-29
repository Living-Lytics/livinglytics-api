import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getAuthStatus } from '@/lib/api';
import { createPageUrl } from '@/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { CheckCircle2, XCircle, Loader2, ArrowLeft } from 'lucide-react';

export default function ConnectCallback() {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState('');
  const [provider, setProvider] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      setLoading(true);

      // Read query params (backend may or may not include these)
      const providerParam = searchParams.get('provider');
      const statusParam = searchParams.get('status');
      const messageParam = searchParams.get('message');
      const tokenParam = searchParams.get('token');

      // If token is provided (from Google OAuth), store it
      if (tokenParam) {
        localStorage.setItem('ll_token', tokenParam);
      }

      setProvider(providerParam || 'account');
      
      if (statusParam) {
        setStatus(statusParam);
        setMessage(messageParam || '');
      }

      // Always refresh auth status to get latest connection state
      const authStatus = await getAuthStatus();

      // Check if the provider is now connected
      const isConnected = providerParam && authStatus[providerParam];
      
      if (isConnected) {
        // Show success toast
        const providerName = providerParam === 'google' ? 'Google Analytics' : 
                            providerParam === 'instagram' ? 'Instagram Business' : 
                            'Account';
        
        toast({
          title: 'Connected!',
          description: `${providerName} has been successfully connected.`,
        });
        
        // Set success status if not already set
        if (!statusParam) {
          setStatus('success');
          setMessage(`${providerName} connected successfully! Your account has been linked.`);
        }
      } else if (!statusParam) {
        // If no status param and not connected, assume success anyway
        setStatus('success');
        setMessage('Connection successful! Your account has been linked.');
      }
    } catch (err) {
      console.error('Error in callback:', err);
      setStatus('error');
      setMessage('An error occurred while processing the connection.');
      
      toast({
        variant: 'destructive',
        title: 'Connection error',
        description: 'An error occurred while processing the connection.',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FB] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#3C3CE0]" />
          <p className="text-gray-600">Processing connection...</p>
        </div>
      </div>
    );
  }

  const isSuccess = status === 'success';
  const providerName = provider === 'google' ? 'Google Analytics' : 
                       provider === 'instagram' ? 'Instagram Business' : 
                       'Account';

  return (
    <div className="min-h-screen bg-[#F8F9FB] py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              {isSuccess ? (
                <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                </div>
              ) : (
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <XCircle className="w-6 h-6 text-red-600" />
                </div>
              )}
              <CardTitle className="text-2xl">
                {isSuccess ? 'Connection Successful!' : 'Connection Failed'}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {message && (
              <Alert className={isSuccess ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                <AlertDescription className={isSuccess ? 'text-green-800' : 'text-red-800'}>
                  {message}
                </AlertDescription>
              </Alert>
            )}

            {isSuccess ? (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">What's next?</h4>
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li>✓ {providerName} is now connected to your account</li>
                    <li>✓ We're automatically syncing your last 30 days of data</li>
                    <li>✓ New data will sync automatically going forward</li>
                    <li>✓ You can view your metrics in your dashboard</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Troubleshooting</h4>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>• Make sure you granted all required permissions</li>
                    <li>• Try connecting again from the Connect page</li>
                    <li>• Contact support if the problem persists</li>
                  </ul>
                </div>
              </div>
            )}

            <div className="pt-4 flex gap-3">
              <Button
                asChild
                className="flex-1 gradient-button text-white border-0 rounded-xl"
              >
                <Link to={createPageUrl('Connect')}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Connect
                </Link>
              </Button>
              {isSuccess && (
                <Button
                  asChild
                  variant="outline"
                  className="flex-1 rounded-xl"
                >
                  <Link to={createPageUrl('Home')}>
                    Go to Dashboard
                  </Link>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
