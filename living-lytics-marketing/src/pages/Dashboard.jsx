import React from 'react';
import { getConnectionsSummary } from '../lib/api';

export default function Dashboard() {
  const [summary, setSummary] = React.useState({ total: 0, providers: {} });

  React.useEffect(() => {
    (async () => {
      setSummary(await getConnectionsSummary());
    })();
  }, []);

  return (
    <div className="px-4 py-6 mx-auto max-w-7xl">
      <h1 className="text-2xl font-semibold mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KPI title="Connected Sources" value={summary.total} />
        <KPI title="Sessions (GA4)" value="12,430" />
        <KPI title="Ad Spend (Meta)" value="$3,270" />
        <KPI title="IG Engagement" value="4.8%" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
          <h2 className="font-medium mb-2">Correlation: GA4 Sessions vs Meta Ad Spend</h2>
          <MockLineChart />
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
          <h2 className="font-medium mb-2">AI Insights</h2>
          <ul className="space-y-2 text-sm text-slate-700 dark:text-slate-200">
            <li>• Sessions rose after ad spend increases on 3 of 5 recent days.</li>
            <li>• Consider increasing budget on Tue/Thu when IG engagement peaks.</li>
            <li>• Landing page /pricing drove 32% of conversions this week.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 dark:border-slate-800 p-4">
      <div className="text-sm text-slate-500">{title}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}

function MockLineChart() {
  return (
    <div className="h-56 w-full bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 rounded-xl border border-slate-100 dark:border-slate-800 flex items-center justify-center text-slate-500">
      <span className="text-sm">Line chart placeholder (Sessions vs Spend)</span>
    </div>
  );
}
