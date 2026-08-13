'use client';

import { useState, type FormEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { Plus, X } from 'lucide-react';
import { api } from '@/lib/api';
import { LoadingState, ErrorState, EmptyState } from '@/components/common/States';

export default function JobsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const jobsQuery = useQuery({ queryKey: ['jobs', 'all'], queryFn: () => api.jobs.list({}) });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Jobs</h1>
          <p className="mt-1 text-sm text-ink-faint">Create roles and let AI draft the requirements you review.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} />
          New job
        </button>
      </div>

      {jobsQuery.isLoading && <LoadingState />}
      {jobsQuery.isError && <ErrorState message="Couldn't load jobs." onRetry={() => jobsQuery.refetch()} />}
      {jobsQuery.data && jobsQuery.data.items.length === 0 && (
        <EmptyState
          title="No jobs yet"
          description="Create a job and paste in the description - TalentLens will draft the requirements for you to review."
          action={
            <button className="btn-primary" onClick={() => setShowCreate(true)}>
              Create your first job
            </button>
          }
        />
      )}
      {jobsQuery.data && jobsQuery.data.items.length > 0 && (
        <div className="card divide-y divide-line">
          {jobsQuery.data.items.map((job) => (
            <Link key={job.id} href={`/jobs/${job.id}`} className="flex items-center justify-between px-5 py-4 hover:bg-paper">
              <div>
                <p className="font-medium">{job.title}</p>
                <p className="text-sm text-ink-faint">
                  {job.department || 'No department'} · {job.location || 'Location TBD'} · {job.requirements.length} requirements
                </p>
              </div>
              <span className="badge bg-line/60 text-ink-soft">{job.status}</span>
            </Link>
          ))}
        </div>
      )}

      {showCreate && <CreateJobModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}

function CreateJobModal({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.jobs.create({ title, department, location, description, requirements: [] });
      await queryClient.invalidateQueries({ queryKey: ['jobs'] });
      onClose();
    } catch {
      setError('Could not create the job. Please check the fields and try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-ink/30 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-lg p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold">New job</h2>
          <button onClick={onClose} aria-label="Close" className="text-ink-faint hover:text-ink">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <input className="input" placeholder="Job title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <div className="grid grid-cols-2 gap-3">
            <input className="input" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} />
            <input className="input" placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>
          <textarea
            className="input min-h-[140px] resize-y"
            placeholder="Paste the job description here…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
          <p className="text-xs text-ink-faint">
            After saving, open the job and click &quot;Analyze description&quot; to have AI draft the required skills for you to review.
          </p>
          {error && <p className="rounded bg-clay-faint px-3 py-2 text-sm text-clay">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Creating…' : 'Create job'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
