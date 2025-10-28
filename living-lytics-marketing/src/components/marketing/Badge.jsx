import React from 'react';

export default function Badge({ icon: Icon, label, color = 'indigo' }) {
  const colorClasses = {
    indigo: 'bg-[#3C3CE0]/10 text-[#3C3CE0]',
    teal: 'bg-[#00C4B3]/10 text-[#00C4B3]',
    purple: 'bg-purple-100 text-purple-700',
    orange: 'bg-orange-100 text-orange-700',
  };

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${colorClasses[color]} font-medium text-sm`}>
      {Icon && <Icon className="w-4 h-4" />}
      {label}
    </div>
  );
}