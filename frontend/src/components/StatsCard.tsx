import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
  loading?: boolean;
  className?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({
  icon: Icon,
  label,
  value,
  loading = false,
  className = ''
}) => {
  return (
    <div className={`p-6 bg-white dark:bg-slate-900 rounded-xl border border-primary/10 shadow-sm flex items-center gap-4 ${className}`}>
      <div className="size-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
        <Icon className="size-6" />
      </div>
      <div>
        <p className="text-slate-500 text-sm font-medium">{label}</p>
        <p className="text-2xl font-bold">
          {loading ? '...' : typeof value === 'number' ? value.toLocaleString() : value}
        </p>
      </div>
    </div>
  );
};

export default StatsCard;
