import React from 'react';
import { motion } from 'framer-motion';
import { Instagram, TrendingUp, ShoppingBag, CreditCard } from 'lucide-react';
import Badge from '../marketing/Badge';
import InsightCard from '../marketing/InsightCard';

export default function DashboardMockup() {
  const [showInsight, setShowInsight] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setShowInsight(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  const badges = [
    { icon: Instagram, label: 'Instagram', color: 'purple' },
    { icon: TrendingUp, label: 'Google Analytics', color: 'orange' },
    { icon: ShoppingBag, label: 'Shopify', color: 'teal' },
    { icon: CreditCard, label: 'Stripe', color: 'indigo' },
  ];

  return (
    <div className="relative">
      {/* Badge flow animation */}
      <div className="flex flex-wrap gap-3 mb-6">
        {badges.map((badge, index) => (
          <motion.div
            key={badge.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.15, duration: 0.4 }}
          >
            <Badge icon={badge.icon} label={badge.label} color={badge.color} />
          </motion.div>
        ))}
      </div>

      {/* Dashboard mockup */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
        className="bg-white rounded-3xl shadow-2xl p-6 border border-gray-100"
      >
        {/* KPI tiles */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.8, duration: 0.3 }}
            className="bg-gradient-to-br from-[#3C3CE0]/10 to-[#3C3CE0]/5 rounded-xl p-4 origin-left"
          >
            <div className="text-sm text-[#1E1E2F]/60 mb-1">Website Sessions</div>
            <div className="text-2xl font-bold text-[#1E1E2F]">12,847</div>
            <div className="text-xs text-[#10B981] mt-1">↑ 18.2%</div>
          </motion.div>
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ delay: 0.9, duration: 0.3 }}
            className="bg-gradient-to-br from-[#00C4B3]/10 to-[#00C4B3]/5 rounded-xl p-4 origin-left"
          >
            <div className="text-sm text-[#1E1E2F]/60 mb-1">Conversion Rate</div>
            <div className="text-2xl font-bold text-[#1E1E2F]">3.8%</div>
            <div className="text-xs text-[#10B981] mt-1">↑ 0.4%</div>
          </motion.div>
        </div>

        {/* Chart placeholder */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 1.0, duration: 0.4 }}
          className="bg-gray-50 rounded-xl h-32 mb-6 flex items-end gap-2 p-4 origin-left"
        >
          {[40, 65, 45, 80, 60, 75, 55, 90, 70, 85, 95, 78].map((height, i) => (
            <div
              key={i}
              className="flex-1 bg-gradient-to-t from-[#3C3CE0] to-[#00C4B3] rounded-t"
              style={{ height: `${height}%` }}
            />
          ))}
        </motion.div>

        {/* AI Insight card */}
        {showInsight && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <InsightCard
              title="AI Insight"
              body="Instagram reach spike was followed by +18% website sessions the next day. Post again Tue 4–6 PM."
              action="View Details"
              evidenceChips={['2-day lag', 'High confidence']}
            />
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}