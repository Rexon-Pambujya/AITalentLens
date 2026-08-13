'use client';

import { useState, type FormEvent } from 'react';
import { useAuth } from '@/lib/auth';
import { ApiError } from '@/lib/api';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login, register } = useAuth();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(orgName, email, password, name);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <LensMark />
          <div>
            <h1 className="font-display text-2xl font-semibold">TalentLens AI</h1>
            <p className="mt-1 text-sm text-ink-faint">AI-powered candidate intelligence for faster, fairer hiring.</p>
          </div>
        </div>

        <div className="card p-6">
          <div className="mb-5 flex rounded border border-line bg-paper p-0.5 text-sm">
            <button
              className={`flex-1 rounded py-1.5 font-medium transition-colors ${mode === 'login' ? 'bg-paperRaised shadow-sm' : 'text-ink-faint'}`}
              onClick={() => setMode('login')}
              type="button"
            >
              Sign in
            </button>
            <button
              className={`flex-1 rounded py-1.5 font-medium transition-colors ${mode === 'register' ? 'bg-paperRaised shadow-sm' : 'text-ink-faint'}`}
              onClick={() => setMode('register')}
              type="button"
            >
              Create account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3.5">
            {mode === 'register' && (
              <>
                <Field label="Company name">
                  <input className="input" value={orgName} onChange={(e) => setOrgName(e.target.value)} required />
                </Field>
                <Field label="Your name">
                  <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
                </Field>
              </>
            )}
            <Field label="Email">
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>
            <Field label="Password">
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </Field>

            {error && <p className="rounded bg-clay-faint px-3 py-2 text-sm text-clay">{error}</p>}

            <button type="submit" className="btn-primary w-full justify-center" disabled={submitting}>
              {submitting ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-ink-soft">{label}</span>
      {children}
    </label>
  );
}

function LensMark() {
  return (
    <svg width="36" height="36" viewBox="0 0 22 22" fill="none">
      {Array.from({ length: 8 }, (_, i) => {
        const angle = (i / 8) * 360 - 90;
        const rad = (angle * Math.PI) / 180;
        const x1 = 11 + Math.cos(rad) * 4;
        const y1 = 11 + Math.sin(rad) * 4;
        const x2 = 11 + Math.cos(rad) * 9.5;
        const y2 = 11 + Math.sin(rad) * 9.5;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#3B2FA3" strokeWidth="2.2" strokeLinecap="round" />;
      })}
    </svg>
  );
}
