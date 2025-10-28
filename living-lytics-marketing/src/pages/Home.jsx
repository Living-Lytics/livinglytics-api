import React from 'react';
import HeroSection from '../components/home/HeroSection';
import ProblemSection from '../components/home/ProblemSection';
import SolutionSection from '../components/home/SolutionSection';
import FeaturesGrid from '../components/home/FeaturesGrid';
import SocialProof from '../components/home/SocialProof';
import FinalCTA from '../components/home/FinalCTA';

export default function Home() {
  return (
    <div>
      <HeroSection />
      <ProblemSection />
      <SolutionSection />
      <FeaturesGrid />
      <SocialProof />
      <FinalCTA />
    </div>
  );
}