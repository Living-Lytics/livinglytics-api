import React from 'react';
import SectionHeading from '../components/marketing/SectionHeading';
import { motion } from 'framer-motion';
import { TrendingUp, Users, ShoppingBag } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';

export default function CaseStudies() {
  const cases = [
    {
      company: 'GrowthCo',
      industry: 'SaaS',
      icon: TrendingUp,
      color: 'indigo',
      metric: '+22% sessions in 14 days',
      summary: 'Discovered Instagram stories drove 3x more traffic than feed posts',
      results: ['18% increase in website sessions', '12% boost in demo requests', '22% improvement in overall traffic'],
    },
    {
      company: 'RetailPlus',
      industry: 'E-commerce',
      icon: ShoppingBag,
      color: 'teal',
      metric: '+31% conversion rate',
      summary: 'Found email campaigns peak 48 hours after send, optimized timing',
      results: ['31% increase in conversion rate', '45% boost in email ROI', '2.3x improvement in revenue per send'],
    },
    {
      company: 'AgencyX',
      industry: 'Marketing Agency',
      icon: Users,
      color: 'purple',
      metric: '10 hours saved weekly',
      summary: 'Automated client reporting and discovered cross-channel opportunities',
      results: ['10 hours saved per week', '15% increase in client retention', '25% growth in upsell opportunities'],
    },
  ];

  const colorClasses = {
    indigo: 'from-indigo-500 to-indigo-600',
    teal: 'from-teal-500 to-teal-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Case Studies"
          heading="Real Results from Real Businesses"
          subcopy="See how companies like yours use Living Lytics to drive growth"
        />

        <div className="grid md:grid-cols-3 gap-8">
          {cases.map((caseStudy, index) => (
            <motion.div
              key={caseStudy.company}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-3xl p-8 shadow-lg hover:shadow-xl transition-shadow group cursor-pointer"
            >
              <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colorClasses[caseStudy.color]} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                <caseStudy.icon className="w-8 h-8 text-white" />
              </div>

              <div className="mb-4">
                <h3 className="text-2xl font-bold text-[#1E1E2F] mb-1">{caseStudy.company}</h3>
                <p className="text-sm text-[#1E1E2F]/60">{caseStudy.industry}</p>
              </div>

              <div className="bg-gradient-to-r from-[#3C3CE0]/10 to-[#00C4B3]/10 rounded-xl p-4 mb-6">
                <div className="text-2xl font-bold text-[#3C3CE0]">{caseStudy.metric}</div>
              </div>

              <p className="text-[#1E1E2F]/70 mb-6 leading-relaxed">{caseStudy.summary}</p>

              <div className="space-y-2 mb-6">
                {caseStudy.results.map((result) => (
                  <div key={result} className="flex items-start gap-2 text-sm text-[#1E1E2F]/60">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] mt-1.5 flex-shrink-0" />
                    {result}
                  </div>
                ))}
              </div>

              <button className="text-sm font-semibold text-[#3C3CE0] group-hover:text-[#00C4B3] transition-colors">
                Read full case study →
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}