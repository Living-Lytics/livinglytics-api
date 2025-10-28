import React from 'react';
import { motion } from 'framer-motion';
import { Star } from 'lucide-react';

export default function TestimonialCard({ quote, author, role, company, index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.25, delay: index * 0.08 }}
      className="bg-white rounded-2xl p-8 shadow-sm"
    >
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="w-5 h-5 fill-[#F59E0B] text-[#F59E0B]" />
        ))}
      </div>
      <p className="text-[#1E1E2F]/80 mb-6 leading-relaxed italic">"{quote}"</p>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center text-white font-bold">
          {author[0]}
        </div>
        <div>
          <div className="font-semibold text-[#1E1E2F]">{author}</div>
          <div className="text-sm text-[#1E1E2F]/60">{role} at {company}</div>
        </div>
      </div>
    </motion.div>
  );
}