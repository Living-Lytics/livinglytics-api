import React from 'react';

export default function SectionHeading({ eyebrow, heading, subcopy, centered = true }) {
  return (
    <div className={`max-w-3xl ${centered ? 'mx-auto text-center' : ''} mb-16`}>
      {eyebrow && (
        <div className="inline-block px-4 py-1.5 rounded-full bg-gradient-to-r from-[#3C3CE0]/10 to-[#00C4B3]/10 text-[#3C3CE0] text-sm font-semibold mb-4">
          {eyebrow}
        </div>
      )}
      <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-[#1E1E2F] mb-6">
        {heading}
      </h2>
      {subcopy && (
        <p className="text-lg text-[#1E1E2F]/60 leading-relaxed">
          {subcopy}
        </p>
      )}
    </div>
  );
}