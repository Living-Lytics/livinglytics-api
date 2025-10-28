

import React from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "@/utils";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { base44 } from "@/api/base44Client";

export default function Layout({ children, currentPageName }) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Home', path: 'Home' },
    { name: 'How it Works', path: 'HowItWorks' },
    { name: 'Features', path: 'Features' },
    { name: 'Integrations', path: 'Integrations' },
    { name: 'Pricing', path: 'Pricing' },
    { name: 'Case Studies', path: 'CaseStudies' },
    { name: 'Resources', path: 'Resources' },
  ];

  const handleSignIn = () => {
    base44.auth.redirectToLogin();
  };

  const handleGetStarted = () => {
    base44.auth.redirectToLogin();
  };

  return (
    <div className="min-h-screen bg-[#F8F9FB]">
      <style>{`
        :root {
          --primary: #3C3CE0;
          --accent: #00C4B3;
          --text: #1E1E2F;
          --background: #F8F9FB;
          --success: #10B981;
          --warning: #F59E0B;
          --error: #EF4444;
        }
        
        * {
          font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        h1, h2, h3, h4, h5, h6 {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          font-weight: 700;
        }
        
        .gradient-button {
          background: linear-gradient(135deg, #3C3CE0 0%, #00C4B3 100%);
          transition: all 150ms ease;
        }
        
        .gradient-button:hover {
          transform: scale(1.03);
          background: linear-gradient(135deg, #2D2DD0 0%, #00B5A5 100%);
        }
        
        .focus-ring:focus-visible {
          outline: 2px solid rgba(0, 196, 179, 0.6);
          outline-offset: 2px;
        }
      `}</style>

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/95 backdrop-blur-lg shadow-md' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Logo */}
            <Link to={createPageUrl('Home')} className="flex items-center gap-3 focus-ring rounded-lg">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center">
                <div className="w-2 h-2 bg-white rounded-full"></div>
              </div>
              <span className="text-xl font-bold text-[#1E1E2F]">Living Lytics</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-8">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={createPageUrl(link.path)}
                  className={`text-sm font-medium transition-colors focus-ring rounded px-2 py-1 ${
                    location.pathname === createPageUrl(link.path)
                      ? 'text-[#3C3CE0]'
                      : 'text-[#1E1E2F]/70 hover:text-[#1E1E2F]'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
            </div>

            {/* Desktop CTAs */}
            <div className="hidden lg:flex items-center gap-4">
              <Button variant="ghost" className="text-[#1E1E2F] focus-ring" onClick={handleSignIn}>
                Sign in
              </Button>
              <Button className="gradient-button text-white border-0 focus-ring rounded-xl" onClick={handleGetStarted}>
                Get Started
              </Button>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 focus-ring rounded-lg"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6 text-[#1E1E2F]" />
              ) : (
                <Menu className="w-6 h-6 text-[#1E1E2F]" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-white border-t border-gray-200">
            <div className="px-4 py-4 space-y-2">
              {navLinks.map((link) => (
                <Link
                  key={link.path}
                  to={createPageUrl(link.path)}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname === createPageUrl(link.path)
                      ? 'bg-[#3C3CE0]/10 text-[#3C3CE0]'
                      : 'text-[#1E1E2F]/70 hover:bg-gray-50'
                  }`}
                >
                  {link.name}
                </Link>
              ))}
              <div className="pt-4 space-y-2">
                <Button variant="outline" className="w-full" onClick={handleSignIn}>Sign in</Button>
                <Button className="w-full gradient-button text-white border-0" onClick={handleGetStarted}>Get Started</Button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="pt-20">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-[#1E1E2F] text-white mt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
            {/* Brand */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                </div>
                <span className="text-xl font-bold">Living Lytics</span>
              </div>
              <p className="text-white/60 text-sm mb-6">
                Turn your business data into actionable growth. Connect, analyze, and act on insights that drive results.
              </p>
              <div className="flex gap-4">
                <a href="#" className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                  <span className="sr-only">Twitter</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" /></svg>
                </a>
                <a href="#" className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors">
                  <span className="sr-only">LinkedIn</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" /></svg>
                </a>
              </div>
            </div>

            {/* Product */}
            <div>
              <h3 className="font-bold mb-4">Product</h3>
              <ul className="space-y-3 text-sm text-white/60">
                <li><Link to={createPageUrl('Features')} className="hover:text-white transition-colors">Features</Link></li>
                <li><Link to={createPageUrl('Integrations')} className="hover:text-white transition-colors">Integrations</Link></li>
                <li><Link to={createPageUrl('Pricing')} className="hover:text-white transition-colors">Pricing</Link></li>
                <li><a href="#" className="hover:text-white transition-colors">Templates</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Changelog</a></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h3 className="font-bold mb-4">Company</h3>
              <ul className="space-y-3 text-sm text-white/60">
                <li><Link to={createPageUrl('About')} className="hover:text-white transition-colors">About</Link></li>
                <li><Link to={createPageUrl('Contact')} className="hover:text-white transition-colors">Contact</Link></li>
                <li><Link to={createPageUrl('CaseStudies')} className="hover:text-white transition-colors">Case Studies</Link></li>
              </ul>
            </div>

            {/* Trust & Resources */}
            <div>
              <h3 className="font-bold mb-4">Trust & Resources</h3>
              <ul className="space-y-3 text-sm text-white/60">
                <li><Link to={createPageUrl('Security')} className="hover:text-white transition-colors">Security</Link></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
                <li><Link to={createPageUrl('Resources')} className="hover:text-white transition-colors">Blog</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-12 pt-8 text-center text-sm text-white/40">
            © {new Date().getFullYear()} Living Lytics. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

