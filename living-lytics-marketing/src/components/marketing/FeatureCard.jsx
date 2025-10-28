import React from 'react';
import { motion } from 'framer-motion';

export default function FeatureCard({ icon: Icon, title, description, index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.25, delay: index * 0.08 }}
      className="bg-white rounded-2xl p-8 shadow-sm hover:shadow-lg transition-shadow duration-300"
    >
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#3C3CE0] to-[#00C4B3] flex items-center justify-center mb-6">
        <Icon className="w-7 h-7 text-white" />
      </div>
      <h3 className="text-xl font-bold text-[#1E1E2F] mb-3">{title}</h3>
      <p className="text-[#1E1E2F]/60 leading-relaxed">{description}</p>
    </motion.div>
  );
}