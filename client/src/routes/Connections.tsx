import { useEffect, useState } from 'react';
import { Page } from '../components/Page';
import { useToast } from '../components/Toast';
import { useStore } from '../lib/useStore';
import { runInstagramBackfill } from '../lib/api';

export const Connections = () => {
  const { connections, refreshConnections } = useStore();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    refreshConnections();
  }, [refreshConnections]);

  const handleGoogleConnect = () => {
    const email = localStorage.getItem('userEmail') || prompt('Enter your email:');
    if (email) {
      localStorage.setItem('userEmail', email);
      window.location.href = `${import.meta.env.VITE_OAUTH_GA_INIT}?email=${encodeURIComponent(email)}`;
    }
  };

  const handleInstagramConnect = () => {
    const email = localStorage.getItem('userEmail') || prompt('Enter your email:');
    if (email) {
      localStorage.setItem('userEmail', email);
      window.location.href = `${import.meta.env.VITE_OAUTH_IG_INIT}?email=${encodeURIComponent(email)}`;
    }
  };

  const handleBackfill = async () => {
    setLoading(true);
    try {
      await runInstagramBackfill();
      toast('Instagram backfill started successfully!', 'success');
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Backfill failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const isAdmin = localStorage.getItem('userRole') === 'admin';

  return (
    <Page title="Data Connections">
      <p className="text-gray-600 mb-8">Connect your analytics platforms to unify insights</p>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Google Analytics 4 */}
        <div className="bg-white rounded-lg shadow-md p-6 border-t-4 border-orange-500">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-orange-100 p-3 rounded-lg">
                <svg className="w-8 h-8 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Google Analytics 4</h3>
                <span
                  className={`inline-block px-2 py-1 text-xs font-medium rounded mt-1 ${
                    connections.google === 'connected'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {connections.google === 'connected' ? 'Connected' : 'Not Connected'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-sm mb-4">
            Track website sessions, conversions, and user behavior
          </p>
          <button
            onClick={handleGoogleConnect}
            className="w-full bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {connections.google === 'connected' ? 'Reconnect' : 'Connect'} Google Analytics
          </button>
        </div>

        {/* Instagram Business */}
        <div className="bg-white rounded-lg shadow-md p-6 border-t-4 border-pink-500">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-pink-100 p-3 rounded-lg">
                <svg className="w-8 h-8 text-pink-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">Instagram Business</h3>
                <span
                  className={`inline-block px-2 py-1 text-xs font-medium rounded mt-1 ${
                    connections.instagram === 'connected'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {connections.instagram === 'connected' ? 'Connected' : 'Not Connected'}
                </span>
              </div>
            </div>
          </div>
          <p className="text-gray-600 text-sm mb-4">
            Track reach, engagement, and content performance
          </p>
          <button
            onClick={handleInstagramConnect}
            className="w-full bg-pink-600 hover:bg-pink-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {connections.instagram === 'connected' ? 'Reconnect' : 'Connect'} Instagram Business
          </button>
        </div>
      </div>

      {/* Sync Info */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <p>Last synced: {connections.lastSyncedAt || '—'}</p>
      </div>

      {/* Admin Controls */}
      {isAdmin && (
        <div className="mt-6">
          <button
            onClick={handleBackfill}
            disabled={loading}
            className="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Run IG Backfill (30d)'}
          </button>
        </div>
      )}
    </Page>
  );
};
