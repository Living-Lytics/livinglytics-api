import React from 'react';
import { motion } from 'framer-motion';
import { base44 } from '@/api/base44Client';
import { createPageUrl } from '@/utils';
import SectionHeading from '../components/marketing/SectionHeading';
import CTAButton from '../components/marketing/CTAButton';
import { Check, Sparkles, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

export default function Pricing() {
  const [isAnnual, setIsAnnual] = React.useState(false);

  const plans = [
    {
      name: 'Essential',
      price: { monthly: 20, annual: 17 },
      description: 'Perfect for small businesses getting started',
      features: [
        'Up to 2 data sources',
        'Weekly AI Insights',
        'Basic Dashboard Analytics',
        'Email support',
        '30-day data history',
      ],
      notIncluded: ['Cross-data analysis', 'Daily insights', 'Advanced AI'],
      cta: 'Choose Essential',
      popular: false,
    },
    {
      name: 'Pro',
      price: { monthly: 49, annual: 42 },
      description: 'Best for growing teams and agencies',
      features: [
        'Up to 5 data sources',
        'Daily AI Insights & Recommendations',
        'Cross-Data Analysis',
        'Priority email support',
        '12-month data history',
        'Custom dashboard views',
        'Weekly digest emails',
      ],
      notIncluded: ['White-label dashboards', 'API access'],
      cta: 'Choose Pro',
      popular: true,
    },
    {
      name: 'Agency',
      price: { monthly: 99, annual: 84 },
      description: 'For agencies and enterprise teams',
      features: [
        'Unlimited sources & users',
        'Advanced AI Insights + Custom Benchmarks',
        'White-Label Dashboards',
        'API access',
        'Unlimited data history',
        'Dedicated account manager',
        'Phone & priority support',
        'Custom integrations',
      ],
      notIncluded: [],
      cta: 'Choose Agency',
      popular: false,
    },
  ];

  const comparisonFeatures = [
    { name: 'Data Sources', essential: '2', pro: '5', agency: 'Unlimited' },
    { name: 'AI Insights', essential: 'Weekly', pro: 'Daily', agency: 'Real-time' },
    { name: 'Data History', essential: '30 days', pro: '12 months', agency: 'Unlimited' },
    { name: 'Cross-Data Analysis', essential: false, pro: true, agency: true },
    { name: 'Custom Benchmarks', essential: false, pro: false, agency: true },
    { name: 'White-Label', essential: false, pro: false, agency: true },
    { name: 'API Access', essential: false, pro: false, agency: true },
    { name: 'Priority Support', essential: false, pro: true, agency: true },
  ];

  const faqs = [
    {
      question: 'What counts as a data source?',
      answer: 'A data source is any integration you connect, such as Google Analytics, Instagram, Shopify, or Stripe. Each connected account counts as one source.',
    },
    {
      question: 'Can I change plans any time?',
      answer: 'Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we\'ll prorate any charges or credits.',
    },
    {
      question: 'Do you offer agency discounts?',
      answer: 'Yes, we offer custom pricing for agencies managing multiple client accounts. Contact our sales team to discuss your needs.',
    },
    {
      question: 'What happens if I exceed my data source limit?',
      answer: 'You\'ll receive a notification when you\'re close to your limit. You can either upgrade your plan or remove unused sources to stay within your tier.',
    },
    {
      question: 'Is there a free trial?',
      answer: 'Yes! All plans include a 14-day free trial with full access to features. No credit card required to start.',
    },
  ];

  return (
    <div className="bg-[#F8F9FB]">
      {/* Hero Section */}
      <section className="py-20 md:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[#1E1E2F] leading-tight mb-6">
                Simple Plans for Every Business Size
              </h1>
              <p className="text-xl text-[#1E1E2F]/60 mb-8 leading-relaxed">
                Choose a plan that fits your growth stage—upgrade as you scale.
              </p>
              <CTAButton onClick={() => base44.auth.redirectToLogin()}>
                Start Free Trial
              </CTAButton>
            </motion.div>

            {/* Animated bar chart */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="relative"
            >
              <div className="bg-white rounded-3xl shadow-2xl p-8">
                <div className="flex items-end justify-around h-64 gap-4">
                  {[40, 70, 100].map((height, i) => (
                    <motion.div
                      key={i}
                      initial={{ scaleY: 0 }}
                      animate={{ scaleY: 1 }}
                      transition={{ delay: 0.5 + i * 0.2, duration: 0.5 }}
                      className="flex-1 bg-gradient-to-t from-[#3C3CE0] to-[#00C4B3] rounded-t-xl origin-bottom"
                      style={{ height: `${height}%` }}
                    />
                  ))}
                </div>
                <div className="flex justify-around mt-4 text-sm font-semibold text-[#1E1E2F]/60">
                  <span>Essential</span>
                  <span>Pro</span>
                  <span>Agency</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Pricing Toggle */}
      <section className="pb-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center gap-4">
            <span className={`font-medium ${!isAnnual ? 'text-[#1E1E2F]' : 'text-[#1E1E2F]/40'}`}>
              Monthly
            </span>
            <button
              onClick={() => setIsAnnual(!isAnnual)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                isAnnual ? 'bg-[#3C3CE0]' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                  isAnnual ? 'transform translate-x-7' : ''
                }`}
              />
            </button>
            <span className={`font-medium ${isAnnual ? 'text-[#1E1E2F]' : 'text-[#1E1E2F]/40'}`}>
              Annual
            </span>
            {isAnnual && (
              <span className="text-sm font-semibold text-[#10B981] bg-[#10B981]/10 px-3 py-1 rounded-full">
                Save 15%
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={`relative bg-white rounded-3xl p-8 shadow-lg ${
                  plan.popular ? 'ring-2 ring-[#3C3CE0] scale-105 md:scale-105' : ''
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-[#3C3CE0] to-[#00C4B3] text-white px-4 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                      <Sparkles className="w-4 h-4" />
                      Most Popular
                    </div>
                  </div>
                )}

                <h3 className="text-2xl font-bold text-[#1E1E2F] mb-2">{plan.name}</h3>
                <p className="text-[#1E1E2F]/60 text-sm mb-6">{plan.description}</p>

                <div className="mb-6">
                  <span className="text-5xl font-bold text-[#1E1E2F]">
                    ${isAnnual ? plan.price.annual : plan.price.monthly}
                  </span>
                  <span className="text-[#1E1E2F]/60 text-lg">/month</span>
                  {isAnnual && (
                    <div className="text-sm text-[#1E1E2F]/40 mt-1">
                      Billed ${plan.price.annual * 12}/year
                    </div>
                  )}
                </div>

                <Button
                  onClick={() => base44.auth.redirectToLogin()}
                  className={`w-full mb-6 rounded-xl h-12 ${
                    plan.popular
                      ? 'gradient-button text-white border-0'
                      : 'border-2 border-[#3C3CE0] text-[#3C3CE0] bg-transparent hover:bg-[#3C3CE0]/5'
                  }`}
                >
                  {plan.cta}
                </Button>

                <ul className="space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-[#1E1E2F]/70">
                      <Check className="w-5 h-5 text-[#10B981] flex-shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                  {plan.notIncluded.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm text-[#1E1E2F]/30">
                      <X className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison Table */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-12 text-center">
            Compare Plans
          </h2>

          <div className="bg-white rounded-3xl shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200 bg-[#F8F9FB]">
                    <th className="text-left py-4 px-6 font-semibold text-[#1E1E2F]">Feature</th>
                    <th className="text-center py-4 px-6 font-semibold text-[#1E1E2F]">Essential</th>
                    <th className="text-center py-4 px-6 font-semibold text-[#3C3CE0]">Pro</th>
                    <th className="text-center py-4 px-6 font-semibold text-[#1E1E2F]">Agency</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonFeatures.map((feature, i) => (
                    <tr key={feature.name} className="border-b border-gray-100">
                      <td className="py-4 px-6 font-medium text-[#1E1E2F]">{feature.name}</td>
                      <td className="py-4 px-6 text-center">
                        {typeof feature.essential === 'boolean' ? (
                          feature.essential ? (
                            <Check className="w-5 h-5 text-[#10B981] mx-auto" />
                          ) : (
                            <X className="w-5 h-5 text-[#1E1E2F]/20 mx-auto" />
                          )
                        ) : (
                          <span className="text-[#1E1E2F]/70">{feature.essential}</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-center bg-[#3C3CE0]/5">
                        {typeof feature.pro === 'boolean' ? (
                          feature.pro ? (
                            <Check className="w-5 h-5 text-[#10B981] mx-auto" />
                          ) : (
                            <X className="w-5 h-5 text-[#1E1E2F]/20 mx-auto" />
                          )
                        ) : (
                          <span className="text-[#1E1E2F]/70 font-semibold">{feature.pro}</span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-center">
                        {typeof feature.agency === 'boolean' ? (
                          feature.agency ? (
                            <Check className="w-5 h-5 text-[#10B981] mx-auto" />
                          ) : (
                            <X className="w-5 h-5 text-[#1E1E2F]/20 mx-auto" />
                          )
                        ) : (
                          <span className="text-[#1E1E2F]/70">{feature.agency}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-center mt-8">
            <CTAButton onClick={() => base44.auth.redirectToLogin()}>
              Start My 14-Day Trial
            </CTAButton>
          </div>
        </div>
      </section>

      {/* FAQ Accordion */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-[#1E1E2F] mb-12 text-center">
            Frequently Asked Questions
          </h2>

          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="bg-white rounded-2xl px-6 border-none shadow-sm">
                <AccordionTrigger className="text-left font-semibold text-[#1E1E2F] hover:no-underline">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-[#1E1E2F]/60">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>

          <div className="text-center mt-8">
            <CTAButton to={createPageUrl('Contact')} variant="secondary">
              Contact Sales
            </CTAButton>
          </div>
        </div>
      </section>

      {/* Final Banner */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-gradient-to-r from-[#00C4B3] to-[#3C3CE0] rounded-3xl p-12 md:p-16 text-center text-white shadow-2xl"
          >
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
              Get AI-Powered Insights Working for You Today
            </h2>
            <CTAButton 
              onClick={() => base44.auth.redirectToLogin()}
              className="bg-white text-[#3C3CE0] hover:bg-white/90 border-0"
            >
              Start Trial
            </CTAButton>
          </motion.div>
        </div>
      </section>
    </div>
  );
}