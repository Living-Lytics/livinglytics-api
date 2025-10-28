import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export default function CTAButton({ children, to, variant = 'primary', icon = true, onClick, ...props }) {
  const buttonClasses = variant === 'primary'
    ? 'gradient-button text-white border-0 rounded-xl text-lg px-8 py-6 h-auto focus-ring'
    : 'border-2 border-[#3C3CE0] text-[#3C3CE0] hover:bg-[#3C3CE0]/5 rounded-xl text-lg px-8 py-6 h-auto focus-ring';

  const content = (
    <>
      {children}
      {icon && <ArrowRight className="w-5 h-5 ml-2" />}
    </>
  );

  if (to) {
    return (
      <Link to={to}>
        <Button className={buttonClasses} {...props}>
          {content}
        </Button>
      </Link>
    );
  }

  return (
    <Button className={buttonClasses} onClick={onClick} {...props}>
      {content}
    </Button>
  );
}