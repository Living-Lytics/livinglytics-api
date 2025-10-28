import React from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';

export function ConnectedBadge({ accountInfo }) {
  const displayText = accountInfo?.email || accountInfo?.account_name || 'Active';
  
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 border border-green-200">
      <CheckCircle2 className="w-4 h-4 text-green-600" />
      <span className="text-sm font-medium text-green-700">Connected</span>
      {displayText && <span className="text-sm text-green-600">({displayText})</span>}
    </div>
  );
}

export function DisconnectedBadge() {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-50 border border-gray-200">
      <XCircle className="w-4 h-4 text-gray-400" />
      <span className="text-sm font-medium text-gray-600">Not Connected</span>
    </div>
  );
}
