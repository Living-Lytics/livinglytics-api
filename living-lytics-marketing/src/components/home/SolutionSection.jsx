import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getAuthStatus } from '@/lib/api';
import SectionHeading from '../marketing/SectionHeading';
import CTAButton from '../marketing/CTAButton';
import { Link2, Brain, Zap } from 'lucide-react';

export default function SolutionSection() {
  const navigate = useNavigate();
  const steps = [
    {
      icon: Link2,
      number: '01',
      title: 'Connect',
      description: 'Link your data sources in minutes with secure OAuth. Google Analytics, Instagram, Shopify, Stripe, and more.',
    },
    {
      icon: Brain,
      number: '02',
      title: 'Analyze',
      description: 'Our AI cross-references your data, finds lag correlations, and identifies patterns you would never spot manually.',
    },
    {
      icon: Zap,
      number: '03',
      title: 'Act',
      description: 'Get plain-English recommendations with evidence. Know exactly what to do next to drive growth.',
    },
  ];

  const handleConnect = async () => {
    const status = await getAuthStatus();
    const authenticated = !!(status && (status.google || status.instagram || status.authenticated));
    
    if (authenticated) {
      navigate('/connect');
    } else {
      navigate('/signin');
    }
  };

  return (
    <section className="py-20 md:py-32 bg-gradient-to-b from-[#F8F9FB] to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="How it Works"
          heading="Three Steps to Clarity"
          subcopy="Connect your tools once. Get insights forever."
        />

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.15 }}
              className="relative"
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-16 left-full w-full h-0.5 bg-gradient-to-r from-[#3C3CE0] to-[#00C4B3] opacity-20 z-0" />
              )}

              <div className="relative bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition-all duration-300 h-full">
                <div className="text-5xl font-bold text-[#3C3CE0]/10 mb-4">{step.number}</div>
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mb-6">
                  <step.icon className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-bold text-[#1E1E2F] mb-3">{step.title}</h3>
                <p className="text-[#1E1E2F]/60 leading-relaxed">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-center">
          <CTAButton onClick={handleConnect}>
            Connect your first source
          </CTAButton>
        </div>
      </div>
    </section>
  );
}