
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthStatus } from '@/lib/api';
import SectionHeading from '../components/marketing/SectionHeading';
import CTAButton from '../components/marketing/CTAButton';
import { createPageUrl } from '@/utils';
import { motion } from 'framer-motion';
import {
  Instagram,
  TrendingUp,
  ShoppingBag,
  CreditCard,
  Mail,
  Users,
  CheckCircle,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export default function Integrations() {
  const navigate = useNavigate();
  const [selectedIntegration, setSelectedIntegration] = React.useState(null);

  const handleConnect = async () => {
    const status = await getAuthStatus();
    const authenticated = !!(status && (status.google || status.instagram || status.authenticated));
    
    if (authenticated) {
      navigate('/connect');
    } else {
      navigate('/signin');
    }
  };

  const integrations = [
    {
      name: 'Google Analytics 4',
      icon: TrendingUp,
      color: 'orange',
      description: 'Connect your GA4 property to track website traffic, user behavior, and conversion metrics.',
      scopes: ['Website sessions', 'Page views', 'User demographics', 'Event tracking', 'Conversion goals'],
      updateFrequency: 'Every hour',
    },
    {
      name: 'Instagram / Meta',
      icon: Instagram,
      color: 'purple',
      description: 'Sync your Instagram business account and Facebook page data for social media insights.',
      scopes: ['Post reach & impressions', 'Engagement metrics', 'Follower growth', 'Story performance', 'Ad campaign data'],
      updateFrequency: 'Every 2 hours',
    },
    {
      name: 'Shopify',
      icon: ShoppingBag,
      color: 'teal',
      description: 'Pull sales data, product performance, and customer metrics from your Shopify store.',
      scopes: ['Orders & revenue', 'Product sales', 'Customer data', 'Cart analytics', 'Traffic sources'],
      updateFrequency: 'Every hour',
    },
    {
      name: 'Stripe',
      icon: CreditCard,
      color: 'indigo',
      description: 'Track payment data, subscription metrics, and revenue analytics from Stripe.',
      scopes: ['Transaction volume', 'Revenue trends', 'Subscription MRR', 'Customer lifetime value', 'Payment success rates'],
      updateFrequency: 'Every hour',
    },
    {
      name: 'HubSpot',
      icon: Users,
      color: 'orange',
      description: 'Connect your CRM to analyze lead generation, deal pipeline, and customer relationships.',
      scopes: ['Contact activity', 'Deal stages', 'Email campaigns', 'Lead sources', 'Sales pipeline'],
      updateFrequency: 'Every 2 hours',
    },
    {
      name: 'Mailchimp',
      icon: Mail,
      color: 'purple',
      description: 'Sync email campaign performance, subscriber growth, and engagement metrics.',
      scopes: ['Campaign performance', 'Open & click rates', 'Subscriber growth', 'List segmentation', 'Automation analytics'],
      updateFrequency: 'Every 4 hours',
    },
  ];

  const colorClasses = {
    orange: 'from-orange-500 to-orange-600',
    purple: 'from-purple-500 to-purple-600',
    teal: 'from-teal-500 to-teal-600',
    indigo: 'from-indigo-500 to-indigo-600',
  };

  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Integrations"
          heading="Connect Your Favorite Tools"
          subcopy="Secure OAuth connections to all your data sources. Setup in minutes, no technical knowledge required."
        />

        {/* Integration grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {integrations.map((integration, index) => (
            <motion.button
              key={integration.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.08 }}
              onClick={() => setSelectedIntegration(integration)}
              className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition-all duration-300 text-left group"
            >
              <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colorClasses[integration.color]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <integration.icon className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-bold text-[#1E1E2F] mb-2">{integration.name}</h3>
              <p className="text-[#1E1E2F]/60 text-sm mb-4">{integration.description}</p>
              <div className="text-sm font-semibold text-[#3C3CE0] group-hover:text-[#00C4B3] transition-colors">
                View details →
              </div>
            </motion.button>
          ))}
        </div>

        {/* More integrations coming */}
        <div className="bg-gradient-to-br from-[#3C3CE0]/5 to-[#00C4B3]/5 rounded-3xl p-12 text-center mb-16">
          <h3 className="text-2xl font-bold text-[#1E1E2F] mb-4">
            Need Another Integration?
          </h3>
          <p className="text-[#1E1E2F]/60 mb-6 max-w-2xl mx-auto">
            We're constantly adding new integrations. Let us know what tools you use and we'll prioritize them.
          </p>
          <CTAButton to={createPageUrl('Contact')} variant="secondary">
            Request an Integration
          </CTAButton>
        </div>

        {/* CTA */}
        <div className="text-center">
          <CTAButton onClick={handleConnect}>
            Connect Your First Source
          </CTAButton>
        </div>
      </div>

      {/* Integration detail modal */}
      <Dialog open={!!selectedIntegration} onOpenChange={() => setSelectedIntegration(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedIntegration && (
                <>
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses[selectedIntegration.color]} flex items-center justify-center`}>
                    <selectedIntegration.icon className="w-6 h-6 text-white" />
                  </div>
                  {selectedIntegration.name}
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          {selectedIntegration && (
            <div className="space-y-4">
              <p className="text-[#1E1E2F]/60">{selectedIntegration.description}</p>
              
              <div>
                <h4 className="font-semibold text-[#1E1E2F] mb-2">Data Synced:</h4>
                <ul className="space-y-2">
                  {selectedIntegration.scopes.map((scope) => (
                    <li key={scope} className="flex items-center gap-2 text-sm text-[#1E1E2F]/60">
                      <CheckCircle className="w-4 h-4 text-[#10B981]" />
                      {scope}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-center justify-between pt-4 border-t">
                <span className="text-sm text-[#1E1E2F]/60">Update Frequency:</span>
                <span className="text-sm font-semibold text-[#1E1E2F]">{selectedIntegration.updateFrequency}</span>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
