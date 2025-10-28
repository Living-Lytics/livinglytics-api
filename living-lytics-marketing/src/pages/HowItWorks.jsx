
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getAuthStatus } from '@/lib/api';
import { createPageUrl } from '@/utils';
import SectionHeading from '../components/marketing/SectionHeading';
import CTAButton from '../components/marketing/CTAButton';
import { Plug, TrendingUp, Zap, Play, ArrowRight, LayoutDashboard, Sparkles, GitCompare, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function HowItWorks() {
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
      {/* Breadcrumbs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <div className="flex items-center gap-2 text-sm text-[#1E1E2F]/60">
          <Link to={createPageUrl('Home')} className="hover:text-[#3C3CE0]">Home</Link>
          <span>›</span>
          <span className="text-[#1E1E2F]">How It Works</span>
        </div>
      </div>

      {/* Hero Section */}
      <section className="relative py-20 md:py-[120px] bg-white overflow-hidden">
        {/* Subtle background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#3C3CE0]/[0.02] to-[#00C4B3]/[0.02]" />
        
        <div className="relative max-w-[800px] mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <h1 className="text-[32px] md:text-[48px] font-bold text-[#1E1E2F] leading-tight mb-3">
              How Living Lytics Works
            </h1>
            
            <p className="text-[16px] md:text-[20px] text-[#4B5563] leading-[1.6] mb-6">
              Connect your data, analyze performance, and act on AI-powered insights—all in one simple platform.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <CTAButton onClick={handleStartTrial}>
                Get Started Free Trial
              </CTAButton>
              <CTAButton variant="secondary" icon={false}>
                <Play className="w-5 h-5 mr-2" />
                Watch Demo
              </CTAButton>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Three-Step Process */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-4">
              Three Simple Steps to Better Insights
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Plug,
                step: 'Step 1',
                title: 'Connect Sources',
                description: 'Securely connect Google Analytics, Instagram, Shopify, and more. Automatic daily updates.',
                cta: 'View Integrations',
                link: 'Integrations',
              },
              {
                icon: TrendingUp,
                step: 'Step 2',
                title: 'Analyze Insights',
                description: 'Cross-reference metrics and discover relationships between your marketing channels.',
                cta: 'See Example Insights',
                link: 'Features',
              },
              {
                icon: Zap,
                step: 'Step 3',
                title: 'Act on AI',
                description: 'Receive plain-language recommendations that turn data into growth.',
                cta: 'Start Analyzing',
                link: 'Pricing',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="bg-[#F8F9FB] rounded-2xl p-8 text-center hover:shadow-lg transition-shadow"
              >
                <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] items-center justify-center mb-6">
                  <item.icon className="w-8 h-8 text-white" />
                </div>
                <div className="text-sm font-semibold text-[#00C4B3] mb-2">{item.step}</div>
                <h3 className="text-xl font-bold text-[#1E1E2F] mb-3">{item.title}</h3>
                <p className="text-[#1E1E2F]/60 mb-6 leading-relaxed">{item.description}</p>
                <Link 
                  to={createPageUrl(item.link)}
                  className="inline-flex items-center gap-2 text-[#3C3CE0] font-semibold hover:text-[#00C4B3] transition-colors"
                >
                  {item.cta} <ArrowRight className="w-4 h-4" />
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo Preview */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-12">
              See the Dashboard in Action
            </h2>
            
            <div className="relative bg-white rounded-3xl shadow-2xl p-4 mb-8">
              <div className="aspect-video bg-gradient-to-br from-[#3C3CE0]/10 to-[#00C4B3]/10 rounded-2xl flex items-center justify-center">
                <div className="text-center">
                  <div className="w-20 h-20 rounded-full bg-white shadow-lg flex items-center justify-center mx-auto mb-4">
                    <Play className="w-10 h-10 text-[#3C3CE0] ml-1" />
                  </div>
                  <p className="text-[#1E1E2F]/60 font-medium">Video Demo Coming Soon</p>
                </div>
              </div>
            </div>

            <CTAButton variant="secondary">
              Open Live Demo
            </CTAButton>
          </motion.div>
        </div>
      </section>

      {/* Key Benefits Grid */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-4">
              Everything You Need in One Platform
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {[
              { icon: LayoutDashboard, title: 'Unified Dashboard', desc: 'All metrics in one place' },
              { icon: Sparkles, title: 'AI Insights', desc: 'Smart recommendations' },
              { icon: GitCompare, title: 'Cross-Data Correlation', desc: 'Find hidden patterns' },
              { icon: Mail, title: 'Weekly Reports', desc: 'Automated summaries' },
            ].map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.08 }}
                className="bg-[#F8F9FB] rounded-2xl p-6 text-center"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mx-auto mb-4">
                  <benefit.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="font-bold text-[#1E1E2F] mb-2">{benefit.title}</h3>
                <p className="text-sm text-[#1E1E2F]/60">{benefit.desc}</p>
              </motion.div>
            ))}
          </div>

          <div className="text-center">
            <Link 
              to={createPageUrl('Features')}
              className="inline-flex items-center gap-2 text-[#3C3CE0] font-semibold hover:text-[#00C4B3] transition-colors text-lg"
            >
              Learn More in Features <ArrowRight className="w-5 h-5" />
            </Link>
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
              Ready to make your data come to life?
            </h2>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              Start your 14-day trial and see personalized insights for your business.
            </p>
            <CTAButton 
              onClick={handleStartTrial}
              className="bg-white text-[#3C3CE0] hover:bg-white/90 border-0"
            >
              Start Free Trial
            </CTAButton>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
