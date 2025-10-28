import React, { useState, useEffect } from 'react';
import { getAuthStatus, startGoogleConnect, startInstagramConnect, disconnectGoogle, disconnectInstagram } from '@/lib/api';
import { ConnectedBadge, DisconnectedBadge } from '@/components/Badges';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { Loader2, BarChart3, Instagram, Unplug } from 'lucide-react';

export default function Connect() {
  const [authStatus, setAuthStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [disconnecting, setDisconnecting] = useState({ google: false, instagram: false });
  const { toast } = useToast();

  useEffect(() => {
    loadAuthStatus();

    // Poll status every 20 seconds to keep badges fresh after OAuth
    const interval = setInterval(() => {
      loadAuthStatus(true); // Silent refresh (don't show loading state)
    }, 20000);

    return () => clearInterval(interval);
  }, []);

  const loadAuthStatus = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
      }
      setError(null);
      const status = await getAuthStatus();
      setAuthStatus(status);
    } catch (err) {
      if (!silent) {
        setError('Failed to load connection status. Please try again.');
      }
      console.error('Error loading auth status:', err);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const handleGoogleConnect = () => {
    try {
      startGoogleConnect();
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Connection failed',
        description: 'Failed to start Google Analytics connection.',
      });
      console.error('Error starting Google connect:', err);
    }
  };

  const handleInstagramConnect = () => {
    try {
      startInstagramConnect();
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Connection failed',
        description: 'Failed to start Instagram connection.',
      });
      console.error('Error starting Instagram connect:', err);
    }
  };

  const handleGoogleDisconnect = async () => {
    try {
      setDisconnecting({ ...disconnecting, google: true });
      await disconnectGoogle();
      await loadAuthStatus(true);
      toast({
        title: 'Disconnected',
        description: 'Google Analytics has been disconnected.',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Something went wrong while disconnecting Google Analytics.',
      });
      console.error('Error disconnecting Google:', err);
    } finally {
      setDisconnecting({ ...disconnecting, google: false });
    }
  };

  const handleInstagramDisconnect = async () => {
    try {
      setDisconnecting({ ...disconnecting, instagram: true });
      await disconnectInstagram();
      await loadAuthStatus(true);
      toast({
        title: 'Disconnected',
        description: 'Instagram Business has been disconnected.',
      });
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Something went wrong while disconnecting Instagram.',
      });
      console.error('Error disconnecting Instagram:', err);
    } finally {
      setDisconnecting({ ...disconnecting, instagram: false });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8F9FB] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#3C3CE0]" />
          <p className="text-gray-600">Loading connections...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FB] py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-[#1E1E2F] mb-4">
            Connect Your Accounts
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Link your data sources to start tracking metrics and generating insights.
            Your data is securely stored and never shared.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="mb-8 border-red-200 bg-red-50">
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Connection Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Google Analytics Card */}
          <Card className="border-2 hover:border-[#3C3CE0] transition-colors">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-orange-600" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">Google Analytics</CardTitle>
                    <CardDescription>GA4 properties & metrics</CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-3 border-t">
                <span className="text-sm font-medium text-gray-700">Status</span>
                {authStatus?.google ? (
                  <ConnectedBadge accountInfo={authStatus.google} />
                ) : (
                  <DisconnectedBadge />
                )}
              </div>
              
              <div className="pt-2 space-y-2">
                <Button
                  onClick={handleGoogleConnect}
                  className="w-full gradient-button text-white border-0 rounded-xl"
                >
                  {authStatus?.google ? 'Reconnect' : 'Connect'} Google Analytics
                </Button>
                
                {authStatus?.google && (
                  <Button
                    onClick={handleGoogleDisconnect}
                    disabled={disconnecting.google}
                    variant="outline"
                    className="w-full rounded-xl"
                  >
                    {disconnecting.google ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Disconnecting...
                      </>
                    ) : (
                      <>
                        <Unplug className="w-4 h-4 mr-2" />
                        Disconnect
                      </>
                    )}
                  </Button>
                )}
              </div>

              <div className="pt-2 space-y-2 text-sm text-gray-600">
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Access to GA4 properties</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Pageviews, sessions, and user metrics</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Automatic 30-day data backfill</span>
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Instagram Business Card */}
          <Card className="border-2 hover:border-[#3C3CE0] transition-colors">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-lg bg-pink-100 flex items-center justify-center">
                    <Instagram className="w-6 h-6 text-pink-600" />
                  </div>
                  <div>
                    <CardTitle className="text-xl">Instagram Business</CardTitle>
                    <CardDescription>Reach & engagement data</CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between py-3 border-t">
                <span className="text-sm font-medium text-gray-700">Status</span>
                {authStatus?.instagram ? (
                  <ConnectedBadge accountInfo={authStatus.instagram} />
                ) : (
                  <DisconnectedBadge />
                )}
              </div>
              
              <div className="pt-2 space-y-2">
                <Button
                  onClick={handleInstagramConnect}
                  className="w-full gradient-button text-white border-0 rounded-xl"
                >
                  {authStatus?.instagram ? 'Reconnect' : 'Connect'} Instagram Business
                </Button>
                
                {authStatus?.instagram && (
                  <Button
                    onClick={handleInstagramDisconnect}
                    disabled={disconnecting.instagram}
                    variant="outline"
                    className="w-full rounded-xl"
                  >
                    {disconnecting.instagram ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Disconnecting...
                      </>
                    ) : (
                      <>
                        <Unplug className="w-4 h-4 mr-2" />
                        Disconnect
                      </>
                    )}
                  </Button>
                )}
              </div>

              <div className="pt-2 space-y-2 text-sm text-gray-600">
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Reach and impressions</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Engagement metrics</span>
                </p>
                <p className="flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Automatic 30-day data backfill</span>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Info Section */}
        <div className="mt-12 p-6 bg-blue-50 border border-blue-200 rounded-xl">
          <h3 className="font-semibold text-blue-900 mb-2">How it works</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>1. Click "Connect" to authorize Living Lytics with your account</li>
            <li>2. You'll be redirected to the service's login page</li>
            <li>3. Grant permissions and you'll be redirected back</li>
            <li>4. We'll automatically start syncing your historical data (30 days)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
