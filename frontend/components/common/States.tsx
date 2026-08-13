import { AlertCircle, Inbox, Loader2 } from 'lucide-react';
import type { ReactNode } from 'react';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-ink-faint">
      <Loader2 size={16} className="animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-clay-faint bg-clay-faint/40 py-12 text-center">
      <AlertCircle size={20} className="text-clay" />
      <p className="max-w-sm text-sm text-ink-soft">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary">
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-line py-16 text-center">
      <Inbox size={22} className="text-ink-faint" />
      <p className="font-medium text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-faint">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-line/70 ${className}`} />;
}
