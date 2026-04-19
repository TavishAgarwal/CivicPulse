/**
 * CivicPulse — Landing Page
 * Assembles all landing sections in order.
 */
import LandingNav from '../components/landing/LandingNav';
import HeroSection from '../components/landing/HeroSection';
import LiveStatsBar from '../components/landing/LiveStatsBar';
import HowItWorksSection from '../components/landing/HowItWorksSection';
import CSSExplainerSection from '../components/landing/CSSExplainerSection';
import SignalSourcesSection from '../components/landing/SignalSourcesSection';
import TestimonialsSection from '../components/landing/TestimonialsSection';
import ForNGOsSection from '../components/landing/ForNGOsSection';
import CTASection from '../components/landing/CTASection';
import LandingFooter from '../components/landing/LandingFooter';
import './LandingPage.css';

export default function LandingPage() {
  return (
    <div className="lp-root">
      <LandingNav />
      <HeroSection />
      <LiveStatsBar />
      <HowItWorksSection />
      <CSSExplainerSection />
      <SignalSourcesSection />
      <TestimonialsSection />
      <ForNGOsSection />
      <CTASection />
      <LandingFooter />
    </div>
  );
}
