import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import CTAButton from '../marketing/CTAButton';
import { createPageUrl } from '@/utils';
import { openSignInModal } from '@/hooks/useSignInModal';
import { getAuthStatus } from '@/lib/api';
import { CheckCircle } from 'lucide-react';

export default function FinalCTA() {
  const navigate = useNavigate();
  
  const handleGetStarted = async () => {
    const status = await getAuthStatus();
    const authenticated = !!(status && (status.google || status.instagram || status.authenticated));
    
    if (authenticated) {
      navigate('/connect');
    } else {
      openSignInModal();
    }
  };

  return (
    <section className="py-20 md:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] rounded-3xl p-12 md:p-16 text-center text-white shadow-2xl"
        >
          <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-6">
            Ready to Turn Data Into Growth?
          </h2>
          <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
            Join hundreds of businesses using Living Lytics to make smarter decisions, faster.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <CTAButton
              onClick={handleGetStarted}
              variant="secondary"
              className="bg-white text-[#3C3CE0] hover:bg-white/90"
            >
              Get Started Free
            </CTAButton>
            <CTAButton
              to={createPageUrl('Contact')}
              variant="secondary"
              className="border-white text-white hover:bg-white/10"
            >
              Talk to Sales
            </CTAButton>
          </div>

          <div className="flex items-center justify-center gap-6 text-sm text-white/80">
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> Free 14-day trial
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> No credit card required
            </span>
            <span className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" /> Cancel anytime
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}