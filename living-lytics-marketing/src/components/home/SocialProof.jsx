import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getAuthStatus } from '@/lib/api';
import SectionHeading from '../marketing/SectionHeading';
import TestimonialCard from '../marketing/TestimonialCard';
import CTAButton from '../marketing/CTAButton';

export default function SocialProof() {
  const navigate = useNavigate();
  const testimonials = [
    {
      quote: "Living Lytics helped us discover that our Instagram stories drive 3x more website traffic than feed posts. That single insight changed our content strategy.",
      author: "Sarah Chen",
      role: "Marketing Director",
      company: "GrowthCo",
    },
    {
      quote: "We went from spending 10 hours a week on reports to getting better insights in 10 minutes. The AI recommendations are spot-on.",
      author: "Michael Torres",
      role: "Founder",
      company: "EcomPro",
    },
    {
      quote: "The lag correlation feature is incredible. We found that our email campaigns peak in sales 48 hours later, not immediately. Game changer.",
      author: "Jessica Park",
      role: "Head of Growth",
      company: "RetailPlus",
    },
  ];

  const logos = ['Company A', 'Company B', 'Company C', 'Company D', 'Company E'];

  const handleStartAccount = async () => {
    const status = await getAuthStatus();
    const authenticated = !!(status && (status.google || status.instagram || status.authenticated));
    
    if (authenticated) {
      navigate('/connect');
    } else {
      navigate('/signin');
    }
  };

  return (
    <section className="py-20 md:py-32 bg-gradient-to-b from-white to-[#F8F9FB]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Trusted by Growth Teams"
          heading="Join Hundreds of Data-Driven Businesses"
        />

        {/* Logo strip */}
        <div className="flex flex-wrap justify-center items-center gap-12 mb-16 opacity-40">
          {logos.map((logo) => (
            <div key={logo} className="text-2xl font-bold text-[#1E1E2F]">
              {logo}
            </div>
          ))}
        </div>

        {/* Testimonials */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {testimonials.map((testimonial, index) => (
            <TestimonialCard key={index} {...testimonial} index={index} />
          ))}
        </div>

        <div className="text-center">
          <CTAButton onClick={handleStartAccount}>
            Start your free account
          </CTAButton>
        </div>
      </div>
    </section>
  );
}