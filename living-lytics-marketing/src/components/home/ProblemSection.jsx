import React from 'react';
import { motion } from 'framer-motion';
import SectionHeading from '../marketing/SectionHeading';
import CTAButton from '../marketing/CTAButton';
import { createPageUrl } from '@/utils';

export default function ProblemSection() {
  return (
    <section className="py-20 md:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          heading="You Have the Data — But Not the Clarity"
          subcopy="Your tools are scattered. Google Analytics, social media insights, e-commerce dashboards, CRM reports — each telling a different story. You're drowning in metrics but starving for answers."
        />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto"
        >
          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {[
              { icon: '📊', title: 'Disconnected Tools', desc: 'Data lives in silos' },
              { icon: '⏰', title: 'Manual Analysis', desc: 'Hours spent in spreadsheets' },
              { icon: '❓', title: 'Missing Context', desc: "Can't see the full picture" },
            ].map((item, i) => (
              <div key={i} className="bg-red-50 rounded-2xl p-6 text-center border border-red-100">
                <div className="text-4xl mb-3">{item.icon}</div>
                <h3 className="font-bold text-[#1E1E2F] mb-2">{item.title}</h3>
                <p className="text-sm text-[#1E1E2F]/60">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <CTAButton to={createPageUrl('HowItWorks')} variant="secondary">
              See how we unify your data
            </CTAButton>
          </div>
        </motion.div>
      </div>
    </section>
  );
}