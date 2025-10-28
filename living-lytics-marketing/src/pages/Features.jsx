
import React from 'react';
import SectionHeading from '../components/marketing/SectionHeading';
import FeatureCard from '../components/marketing/FeatureCard';
import CTAButton from '../components/marketing/CTAButton';
import {
  LayoutDashboard,
  Sparkles,
  GitCompare,
  Mail,
  TrendingUp,
  Shield,
  Zap,
  Bell,
  Filter,
} from 'lucide-react';

export default function Features() {
  const mainFeatures = [
    {
      icon: LayoutDashboard,
      title: 'Unified Dashboard',
      description: 'All your data sources in one beautiful interface. No more switching between tabs and tools. See website analytics, social media metrics, e-commerce data, and CRM insights side by side.',
    },
    {
      icon: Sparkles,
      title: 'AI-Powered Insights',
      description: 'Our AI analyzes your data 24/7 and surfaces actionable recommendations in plain English. Get notified when something important happens or when there is an opportunity to act.',
    },
    {
      icon: GitCompare,
      title: 'Cross-Data Correlation',
      description: 'Discover hidden relationships between your data sources. See how marketing spend affects sales, how social engagement drives website traffic, and more.',
    },
    {
      icon: Zap,
      title: 'Lag Correlation Detection',
      description: 'Understand the delay between actions and results. Find out if your Instagram posts drive sales 2 days later, or if email campaigns peak after 48 hours.',
    },
    {
      icon: Mail,
      title: 'Weekly Digest',
      description: 'Get a beautiful summary of your week performance every Monday morning. Key metrics, top insights, and recommended actions delivered to your inbox.',
    },
    {
      icon: Filter,
      title: 'Custom Views & Filters',
      description: 'Create personalized dashboard views for different team members. Filter by date range, data source, or metric type to focus on what matters most.',
    },
    {
      icon: Bell,
      title: 'Smart Alerts',
      description: 'Set up intelligent alerts for metric thresholds, anomalies, or opportunities. Get notified via email or Slack when something needs your attention.',
    },
    {
      icon: TrendingUp,
      title: 'Industry Benchmarks',
      description: 'Compare your performance against industry standards and competitors. See where you excel and where there is room for improvement (coming soon).',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Bank-level encryption, SOC 2 compliance, and granular access controls. Your data is safe and secure with us.',
    },
  ];

  const handleStartTrial = () => {
    // Assuming 'base44' is a globally available object or imported elsewhere
    // that handles authentication redirects.
    if (typeof base44 !== 'undefined' && base44.auth && base44.auth.redirectToLogin) {
      base44.auth.redirectToLogin();
    } else {
      console.warn("base44.auth.redirectToLogin is not available. Please ensure base44 SDK is initialized.");
      // Fallback or navigate to a default signup page if base44 is not configured
      // For example: window.location.href = '/signup';
    }
  };

  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <SectionHeading
          eyebrow="Features"
          heading="Everything You Need to Make Data-Driven Decisions"
          subcopy="Powerful analytics and AI insights without the complexity of enterprise tools"
        />

        {/* Feature grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {mainFeatures.map((feature, index) => (
            <FeatureCard key={feature.title} {...feature} index={index} />
          ))}
        </div>

        {/* Comparison table */}
        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-lg mb-16">
          <h3 className="text-2xl font-bold text-[#1E1E2F] mb-8 text-center">
            Living Lytics vs. Manual Reporting
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200">
                  <th className="text-left py-4 px-4 text-[#1E1E2F]/60 font-medium">Task</th>
                  <th className="text-center py-4 px-4 text-[#1E1E2F]/60 font-medium">Manual</th>
                  <th className="text-center py-4 px-4 text-[#3C3CE0] font-semibold">Living Lytics</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { task: 'Weekly reporting', manual: '10+ hours', lytics: '10 minutes' },
                  { task: 'Finding correlations', manual: 'Days/weeks', lytics: 'Instant' },
                  { task: 'Cross-platform analysis', manual: 'Nearly impossible', lytics: 'Automatic' },
                  { task: 'Getting recommendations', manual: 'Manual guesswork', lytics: 'AI-powered' },
                  { task: 'Team collaboration', manual: 'Email spreadsheets', lytics: 'Shared dashboards' },
                ].map((row, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-4 px-4 font-medium text-[#1E1E2F]">{row.task}</td>
                    <td className="py-4 px-4 text-center text-[#1E1E2F]/60">{row.manual}</td>
                    <td className="py-4 px-4 text-center font-semibold text-[#00C4B3]">{row.lytics}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <CTAButton onClick={handleStartTrial}>
            Start Your Free Trial
          </CTAButton>
        </div>
      </div>
    </div>
  );
}
