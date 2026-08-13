'use client';

import { useAuth } from '@/lib/auth';

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="mt-1 text-sm text-ink-faint">Your account and organization preferences.</p>
      </div>

      <div className="card max-w-lg p-5">
        <h2 className="mb-3 font-medium">Account</h2>
        <dl className="space-y-2 text-sm">
          <Row label="Name" value={user?.name} />
          <Row label="Email" value={user?.email} />
          <Row label="Role" value={user?.role} />
        </dl>
      </div>

      <div className="card max-w-lg p-5">
        <h2 className="mb-1 font-medium">Blind screening</h2>
        <p className="mb-3 text-sm text-ink-faint">
          Hide candidate names, photos, and other personal attributes from recruiters during initial screening. The
          matching engine continues using only job-relevant professional information.
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="h-4 w-4 rounded border-line" disabled />
          <span className="text-ink-faint">Coming soon</span>
        </label>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between border-b border-line pb-2">
      <dt className="text-ink-faint">{label}</dt>
      <dd>{value || '—'}</dd>
    </div>
  );
}
