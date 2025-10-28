import React from 'react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center p-8">
      <div className="max-w-lg text-center">
        <h1 className="text-2xl font-semibold mb-2">Dashboard (Coming Soon)</h1>
        <p className="text-gray-600 mb-6">We're building your unified analytics view.</p>
        <Link 
          to="/connect" 
          className="inline-block rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-700 transition-colors"
        >
          Go to Connections
        </Link>
      </div>
    </div>
  );
}
