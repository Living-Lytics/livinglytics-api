import React from 'react';
import { useNavigate } from 'react-router-dom';
import { openSignInModal } from '@/hooks/useSignInModal';
import { getAuthStatus } from '@/lib/api';
import CTAButton from '../marketing/CTAButton';
import DashboardMockup from './DashboardMockup';
import { Play, CheckCircle } from 'lucide-react';

export default function HeroSection() {
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
    <section className="relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#3C3CE0]/5 via-transparent to-[#00C4B3]/5" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left column */}
          <div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[#1E1E2F] leading-tight mb-6">
              Turn Your Business Data Into{' '}
              <span className="bg-gradient-to-r from-[#3C3CE0] to-[#00C4B3] bg-clip-text text-transparent">
                Actionable Growth
              </span>
            </h1>
            <p className="text-xl text-[#1E1E2F]/60 mb-8 leading-relaxed">
              Connect marketing, sales and web data to get clear, AI-driven recommendations.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <CTAButton onClick={handleGetStarted}>
                Get Started Free
              </CTAButton>
              <CTAButton variant="secondary" icon={false}>
                <Play className="w-5 h-5 mr-2" />
                Watch Demo
              </CTAButton>
            </div>

            <div className="flex items-center gap-2 text-sm text-[#1E1E2F]/60">
              <CheckCircle className="w-4 h-4 text-[#10B981]" />
              <span>No credit card. Setup in minutes.</span>
            </div>
          </div>

          {/* Right column - Dashboard mockup */}
          <div className="relative">
            <DashboardMockup />
          </div>
        </div>
      </div>
    </section>
  );
}