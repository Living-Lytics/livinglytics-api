import React from 'react';
import SectionHeading from '../components/marketing/SectionHeading';
import { Shield, Lock, Eye, Database, Server, CheckCircle } from 'lucide-react';

export default function Security() {
  const features = [
    {
      icon: Lock,
      title: 'Bank-Level Encryption',
      description: 'All data is encrypted in transit (TLS 1.3) and at rest (AES-256). Your information is protected with the same standards used by financial institutions.',
    },
    {
      icon: Shield,
      title: 'SOC 2 Compliant',
      description: 'We undergo annual SOC 2 Type II audits to ensure we meet the highest standards for security, availability, and confidentiality.',
    },
    {
      icon: Eye,
      title: 'OAuth Authentication',
      description: 'We never store your passwords. All integrations use secure OAuth flows, and you can revoke access at any time.',
    },
    {
      icon: Database,
      title: 'Data Isolation',
      description: 'Your data is completely isolated from other customers. We use database-level separation and strict access controls.',
    },
    {
      icon: Server,
      title: 'Regular Backups',
      description: 'Automated daily backups with 30-day retention. Your data is replicated across multiple availability zones.',
    },
    {
      icon: CheckCircle,
      title: 'GDPR & CCPA Ready',
      description: 'Full compliance with GDPR, CCPA, and other privacy regulations. Export or delete your data anytime.',
    },
  ];

  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Security & Privacy"
          heading="Your Data is Safe with Us"
          subcopy="Enterprise-grade security and privacy protection for all plans"
        />

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature) => (
            <div key={feature.title} className="bg-white rounded-2xl p-8 shadow-sm">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mb-6">
                <feature.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-xl font-bold text-[#1E1E2F] mb-3">{feature.title}</h3>
              <p className="text-[#1E1E2F]/60 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Data Deletion */}
        <div className="bg-white rounded-3xl p-12 shadow-lg mb-16">
          <h2 className="text-2xl font-bold text-[#1E1E2F] mb-6 text-center">
            You Own Your Data
          </h2>
          <div className="max-w-3xl mx-auto space-y-4 text-[#1E1E2F]/70">
            <p>
              <strong>Export anytime:</strong> Download all your data in standard formats (CSV, JSON) whenever you want.
            </p>
            <p>
              <strong>Delete anytime:</strong> Request complete data deletion and we'll remove everything within 30 days.
            </p>
            <p>
              <strong>Transparency:</strong> We clearly document what data we collect, how we use it, and who has access. No surprises.
            </p>
          </div>
        </div>

        {/* Status link */}
        <div className="text-center">
          <p className="text-[#1E1E2F]/60 mb-4">
            Check our current system status and uptime history
          </p>
          <a
            href="#"
            className="inline-flex items-center gap-2 text-[#3C3CE0] font-semibold hover:text-[#00C4B3] transition-colors"
          >
            <div className="w-2 h-2 rounded-full bg-[#10B981]" />
            Status Page →
          </a>
        </div>
      </div>
    </div>
  );
}