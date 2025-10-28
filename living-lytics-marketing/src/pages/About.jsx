import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getAuthStatus } from '@/lib/api';
import SectionHeading from '../components/marketing/SectionHeading';
import CTAButton from '../components/marketing/CTAButton';
import { Lightbulb, Shield, Target } from 'lucide-react';

export default function About() {
  const navigate = useNavigate();

  const handleStartTrial = async () => {
    const status = await getAuthStatus();
    const authenticated = !!(status && (status.google || status.instagram || status.authenticated));
    
    if (authenticated) {
      navigate('/connect');
    } else {
      navigate('/signin');
    }
  };
  return (
    <div className="bg-[#F8F9FB]">
      {/* Hero Section */}
      <section className="relative py-24 md:py-32 bg-gradient-to-b from-[#F8F9FB] to-[#EAFBFA]/5 overflow-hidden">
        <div className="max-w-[900px] mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[#1E1E2F] leading-tight mb-6">
              Our Vision for Living Data
            </h1>
            <p className="text-xl text-[#1E1E2F]/60 leading-relaxed mb-8">
              At Living Lytics, we believe data should do more than inform—it should inspire action.
            </p>
            <CTAButton onClick={handleStartTrial}>
              Get Started Free Trial
            </CTAButton>
          </motion.div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.25 }}
            >
              <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-6">
                Empowering Every Business to Understand Their Data.
              </h2>
              <p className="text-lg text-[#1E1E2F]/60 leading-relaxed">
                Small businesses and agencies deserve the same clarity that large enterprises enjoy. Living Lytics bridges that gap with AI-powered analytics that are accessible, actionable, and alive.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.25, delay: 0.1 }}
              className="relative"
            >
              <div className="aspect-square bg-gradient-to-br from-[#3C3CE0]/20 to-[#00C4B3]/20 rounded-3xl" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Story Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.25 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-6">
              Where It Started
            </h2>
            <p className="text-lg text-[#1E1E2F]/60 leading-relaxed mb-8">
              Living Lytics was founded to simplify analytics for non-technical teams. We saw businesses spending hours collecting reports but never uncovering the story behind the numbers. Our goal is to make insights instant, intuitive, and impactful.
            </p>
            <div className="w-full h-px bg-[#E5E7EB]" />
          </motion.div>
        </div>
      </section>

      {/* Values Grid */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-4">
              Our Core Values
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Lightbulb,
                title: 'Clarity',
                description: 'We make complex data simple. Every insight is clear, every recommendation is actionable.',
              },
              {
                icon: Shield,
                title: 'Trust',
                description: 'Your data is secure and yours alone. We earn your confidence through transparency and protection.',
              },
              {
                icon: Target,
                title: 'Action',
                description: 'Insights that lead to results. We focus on what moves the needle for your business.',
              },
            ].map((value, index) => (
              <motion.div
                key={value.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08, duration: 0.25 }}
                className="bg-[#F8F9FB] rounded-2xl p-8 text-center hover:shadow-lg transition-shadow"
              >
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mx-auto mb-6">
                  <value.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-[#1E1E2F] mb-3">{value.title}</h3>
                <p className="text-[#1E1E2F]/60 leading-relaxed">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Vision Forward Section */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-6">
              The Future of Living Data
            </h2>
            <p className="text-lg text-[#1E1E2F]/60 max-w-3xl mx-auto">
              We're continually expanding integrations and AI capabilities to help businesses see connections they never knew existed. Our vision is a world where every decision is guided by living data.
            </p>
          </div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-0 right-0 top-12 h-1 bg-gradient-to-r from-[#3C3CE0] to-[#00C4B3] rounded-full hidden md:block" />

            <div className="grid md:grid-cols-3 gap-8 relative">
              {[
                {
                  year: '2025',
                  title: 'Expanded Integrations',
                  description: 'Connect with 50+ marketing and business tools.',
                },
                {
                  year: '2026',
                  title: 'Advanced AI Insights',
                  description: 'Predictive analytics and forecasting capabilities.',
                },
                {
                  year: '2027',
                  title: 'Sustainability Initiatives',
                  description: 'Carbon-neutral infrastructure and impact tracking.',
                },
              ].map((milestone, index) => (
                <motion.div
                  key={milestone.year}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1, duration: 0.25 }}
                  className="relative"
                >
                  <div className="flex flex-col items-center text-center">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mb-4 relative z-10 shadow-lg">
                      <span className="text-2xl font-bold text-white">{milestone.year}</span>
                    </div>
                    <h3 className="text-xl font-bold text-[#1E1E2F] mb-2">{milestone.title}</h3>
                    <p className="text-[#1E1E2F]/60">{milestone.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Banner */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-[#3C3CE0] to-[#00C4B3] rounded-3xl p-12 md:p-16 text-center text-white shadow-2xl"
          >
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
              Let's Bring Your Data to Life
            </h2>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              Partner with us to turn information into action.
            </p>
            <CTAButton 
              onClick={handleStartTrial}
              className="bg-white text-[#3C3CE0] hover:bg-white/90 border-0"
            >
              Start Your Trial
            </CTAButton>
          </motion.div>
        </div>
      </section>
    </div>
  );
}