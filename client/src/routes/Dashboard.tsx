import { useState, useEffect } from 'react';
import { Page } from '../components/Page';
import { useStore } from '../lib/useStore';

export const Dashboard = () => {
  const { connections } = useStore();
  const [range, setRange] = useState<'last_7d' | 'last_30d' | 'last_90d'>('last_7d');

  const hasConnections = connections.google === 'connected' || connections.instagram === 'connected';

  if (!hasConnections) {
    return (
      <Page title="Dashboard">
        <div className="flex flex-col items-center justify-center py-16">
          <div className="text-center max-w-md">
            <svg className="mx-auto h-24 w-24 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Connect your accounts to see insights</h2>
            <p className="text-gray-600 mb-6">
              Start by connecting Google Analytics or Instagram Business to view your data dashboard.
            </p>
            <a
              href="/connections"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Go to Connections
            </a>
          </div>
        </div>
      </Page>
    );
  }

  return (
    <Page
      title="Dashboard"
      actions={
        <select
          value={range}
          onChange={(e) => setRange(e.target.value as typeof range)}
          className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="last_7d">Last 7 days</option>
          <option value="last_30d">Last 30 days</option>
          <option value="last_90d">Last 90 days</option>
        </select>
      }
    >
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        {/* KPI Tiles */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">Sessions</p>
          <p className="text-3xl font-bold text-gray-900">—</p>
          <p className="text-sm text-gray-500 mt-1">No data yet</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">Conversions</p>
          <p className="text-3xl font-bold text-gray-900">—</p>
          <p className="text-sm text-gray-500 mt-1">No data yet</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">IG Reach</p>
          <p className="text-3xl font-bold text-gray-900">—</p>
          <p className="text-sm text-gray-500 mt-1">No data yet</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-600 text-sm mb-1">IG Engagement</p>
          <p className="text-3xl font-bold text-gray-900">—</p>
          <p className="text-sm text-gray-500 mt-1">No data yet</p>
        </div>
      </div>

      {/* Timeline Placeholder */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Combined Timeline</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          Timeline chart will appear here once data is available
        </div>
      </div>

      {/* Insights Placeholder */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Insights</h3>
        <p className="text-gray-500 text-center py-8">
          No insights yet; data is still processing.
        </p>
      </div>
    </Page>
  );
};
