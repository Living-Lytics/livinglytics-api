import React from 'react';
import SectionHeading from '../marketing/SectionHeading';
import FeatureCard from '../marketing/FeatureCard';
import CTAButton from '../marketing/CTAButton';
import { createPageUrl } from '@/utils';
import { LayoutDashboard, Sparkles, GitCompare, Mail, TrendingUp, Shield } from 'lucide-react';

export default function FeaturesGrid() {
  const features = [
    {
      icon: LayoutDashboard,
      title: 'Unified Dashboard',
      description: 'See all your metrics in one place. No more tab-switching between tools.',
    },
    {
      icon: Sparkles,
      title: 'AI Insights',
      description: 'Get actionable recommendations written in plain English, backed by data.',
    },
    {
      icon: GitCompare,
      title: 'Cross-Data Analysis',
      description: 'Discover hidden relationships between marketing spend, social reach, and sales.',
    },
    {
      icon: Mail,
      title: 'Weekly Digest',
      description: 'Automated reports delivered to your inbox every Monday morning.',
    },
    {
      icon: TrendingUp,
      title: 'Benchmarks',
      description: 'Compare your performance against industry standards (coming soon).',
    },
    {
      icon: Shield,
      title: 'Secure & Private',
      description: 'Bank-level encryption. Your data never leaves our secure infrastructure.',
    },
  ];

  return (
    <section className="py-20 md:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Features"
          heading="Everything You Need to Grow"
          subcopy="Powerful analytics without the complexity"
        />

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} {...feature} index={index} />
          ))}
        </div>

        <div className="text-center">
          <CTAButton to={createPageUrl('Features')}>
            Explore all features
          </CTAButton>
        </div>
      </div>
    </section>
  );
}