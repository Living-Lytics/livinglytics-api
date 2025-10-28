import React from 'react';
import SectionHeading from '../components/marketing/SectionHeading';
import { motion } from 'framer-motion';
import { FileText, Book, Download } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function Resources() {
  const blogPosts = [
    {
      title: '10 Marketing Metrics That Actually Matter',
      category: 'Analytics',
      date: 'Jan 15, 2025',
      readTime: '5 min read',
    },
    {
      title: 'How to Find Hidden Correlations in Your Data',
      category: 'Insights',
      date: 'Jan 12, 2025',
      readTime: '7 min read',
    },
    {
      title: 'The Ultimate Guide to Cross-Platform Analytics',
      category: 'Guide',
      date: 'Jan 8, 2025',
      readTime: '12 min read',
    },
  ];

  return (
    <div className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Resources"
          heading="Learn How to Grow with Data"
          subcopy="Guides, templates, and insights to help you make better decisions"
        />

        {/* Newsletter signup */}
        <div className="bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] rounded-3xl p-12 text-center text-white mb-16">
          <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
          <p className="text-white/90 mb-6 max-w-2xl mx-auto">
            Get weekly insights on data analytics, marketing trends, and growth strategies delivered to your inbox.
          </p>
          <div className="flex gap-3 max-w-md mx-auto">
            <Input
              type="email"
              placeholder="Enter your email"
              className="bg-white/20 border-white/30 text-white placeholder:text-white/60 focus-visible:ring-white/50"
            />
            <Button className="bg-white text-[#3C3CE0] hover:bg-white/90 px-8">
              Subscribe
            </Button>
          </div>
        </div>

        {/* Blog posts */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-[#1E1E2F] mb-8">Latest from the Blog</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {blogPosts.map((post, index) => (
              <motion.article
                key={post.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2 text-sm text-[#3C3CE0] mb-3">
                  <FileText className="w-4 h-4" />
                  {post.category}
                </div>
                <h3 className="text-xl font-bold text-[#1E1E2F] mb-3 group-hover:text-[#3C3CE0] transition-colors">
                  {post.title}
                </h3>
                <div className="flex items-center gap-4 text-sm text-[#1E1E2F]/60">
                  <span>{post.date}</span>
                  <span>•</span>
                  <span>{post.readTime}</span>
                </div>
              </motion.article>
            ))}
          </div>
        </div>

        {/* Templates */}
        <div>
          <h2 className="text-2xl font-bold text-[#1E1E2F] mb-8">Free Templates & Guides</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              { icon: Download, title: 'Weekly Marketing KPI Template', type: 'Spreadsheet' },
              { icon: Book, title: 'Complete Guide to Data-Driven Marketing', type: 'PDF' },
              { icon: Download, title: 'Social Media Analytics Checklist', type: 'PDF' },
              { icon: Book, title: 'E-commerce Metrics That Matter', type: 'Guide' },
            ].map((resource) => (
              <motion.div
                key={resource.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all cursor-pointer group flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                  <resource.icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-[#1E1E2F] mb-1 group-hover:text-[#3C3CE0] transition-colors">
                    {resource.title}
                  </h3>
                  <p className="text-sm text-[#1E1E2F]/60">{resource.type}</p>
                </div>
                <Download className="w-5 h-5 text-[#3C3CE0] opacity-0 group-hover:opacity-100 transition-opacity" />
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}