import { ReactNode } from 'react';

interface PageProps {
  title: string;
  actions?: ReactNode;
  children: ReactNode;
}

export const Page = ({ title, actions, children }: PageProps) => {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        {actions && <div>{actions}</div>}
      </div>
      {children}
    </div>
  );
};
