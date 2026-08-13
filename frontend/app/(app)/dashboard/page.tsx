'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Briefcase, Users, TrendingUp, Star } from 'lucide-react';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { LoadingState, ErrorState } from '@/components/common/States';

export default function DashboardPage() {
  const { user } = useAuth();

  const jobsQuery = useQuery({ queryKey: ['jobs', 'active'], queryFn: () => api.jobs.list({ status: 'ACTIVE' }) });
  const allJobsQuery = useQuery({ queryKey: ['jobs', 'all'], queryFn: () => api.jobs.list({}) });
  const candidatesQuery = useQuery({ queryKey: ['candidates', 'recent'], queryFn: () => api.candidates.list({ page: 1 }) });

  if (jobsQuery.isLoading || candidatesQuery.isLoading) return <LoadingState label="Loading your dashboard…" />;
  if (jobsQuery.isError) return <ErrorState message="Couldn't load your dashboard. Please try again." onRetry={() => jobsQuery.refetch()} />;

  const activeJobs = jobsQuery.data?.total ?? 0;
  const totalCandidates = candidatesQuery.data?.total ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Welcome back, {user?.name?.split(' ')[0]}</h1>
        <p className="mt-1 text-sm text-ink-faint">Here&apos;s what&apos;s happening across your pipeline.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={Briefcase} label="Active jobs" value={activeJobs} />
        <StatCard icon={Users} label="Total candidates" value={totalCandidates} />
        <StatCard icon={TrendingUp} label="Candidates screened" value={totalCandidates} />
        <StatCard icon={Star} label="Strong matches" value="—" hint="Run matching to populate" />
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium">Your jobs</h2>
          <Link href="/jobs" className="text-sm text-lens hover:underline">
            View all
          </Link>
        </div>
        {allJobsQuery.data && allJobsQuery.data.items.length > 0 ? (
          <ul className="divide-y divide-line">
            {allJobsQuery.data.items.slice(0, 5).map((job) => (
              <li key={job.id}>
                <Link href={`/jobs/${job.id}`} className="flex items-center justify-between py-3 hover:text-lens">
                  <div>
                    <p className="text-sm font-medium">{job.title}</p>
                    <p className="text-xs text-ink-faint">
                      {job.department || 'No department'} · {job.location || 'Location TBD'}
                    </p>
                  </div>
                  <span className="badge bg-line/60 text-ink-soft">{job.status}</span>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <div className="py-6 text-center text-sm text-ink-faint">
            No jobs yet.{' '}
            <Link href="/jobs" className="text-lens hover:underline">
              Create your first job
            </Link>
            .
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof Briefcase;
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="card p-4">
      <div className="mb-2 flex items-center gap-2 text-ink-faint">
        <Icon size={15} />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className="font-mono text-2xl font-semibold">{value}</p>
      {hint && <p className="mt-0.5 text-[11px] text-ink-faint">{hint}</p>}
    </div>
  );
}
