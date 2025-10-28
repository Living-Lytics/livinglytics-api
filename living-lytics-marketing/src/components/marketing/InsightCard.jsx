import React from 'react';
import { Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function InsightCard({ title, body, action, evidenceChips = [] }) {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-[#00C4B3]/20">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center flex-shrink-0">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-[#1E1E2F] mb-2">{title}</h4>
          <p className="text-[#1E1E2F]/70 text-sm leading-relaxed">{body}</p>
        </div>
      </div>
      {evidenceChips.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {evidenceChips.map((chip, i) => (
            <Badge key={i} variant="secondary" className="bg-[#00C4B3]/10 text-[#00C4B3] text-xs">
              {chip}
            </Badge>
          ))}
        </div>
      )}
      {action && (
        <button className="text-sm font-semibold text-[#3C3CE0] hover:text-[#00C4B3] transition-colors">
          {action} →
        </button>
      )}
    </div>
  );
}