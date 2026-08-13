'use client';

import { useQueries, useQuery } from '@tanstack/react-query';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '@/lib/api';
import { LoadingState, EmptyState } from '@/components/common/States';
import type { RankingEntry } from '@/types';

const LENS = '#3B2FA3';
const LENS_SOFT = '#5A4FC4';
const LENS_LIGHT = '#6F5FC0';
const LENS_FAINT = '#8F7FD1';

const SCORE_BANDS = [
  { label: 'Not suitable\n(<60)', min: 0, max: 60 },
  { label: 'Moderate\n(60-74)', min: 60, max: 75 },
  { label: 'Good\n(75-89)', min: 75, max: 90 },
  { label: 'Strong\n(90-100)', min: 90, max: 101 },
];

const PIPELINE_STAGES = ['NEW', 'SCREENING', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'HIRED', 'REJECTED'];

export default function AnalyticsPage() {
  const jobsQuery = useQuery({ queryKey: ['jobs', 'all'], queryFn: () => api.jobs.list({}) });
  const jobs = jobsQuery.data?.items ?? [];

  const rankingResults = useQueries({
    queries: jobs.map((job) => ({
      queryKey: ['ranking', job.id, 'analytics'],
      queryFn: () => api.jobs.ranking(job.id),
      enabled: jobs.length > 0,
    })),
  });

  if (jobsQuery.isLoading) return <LoadingState />;
  if (jobs.length === 0) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState title="Nothing to analyze yet" description="Create a job and start matching candidates to see analytics here." />
      </div>
    );
  }

  const loadingRankings = rankingResults.some((r) => r.isLoading);
  const perJob = jobs.map((job, i) => ({ job, ranking: (rankingResults[i].data as RankingEntry[]) || [] }));
  const allEntries = perJob.flatMap((p) => p.ranking);

  if (loadingRankings) return <LoadingState label="Aggregating candidate data across jobs…" />;

  if (allEntries.length === 0) {
    return (
      <div className="space-y-6">
        <Header />
        <EmptyState
          title="No matches scored yet"
          description="Upload resumes and run matching against a job to see screening analytics here."
        />
      </div>
    );
  }

  const avgScore = Math.round((allEntries.reduce((s, e) => s + e.overall_score, 0) / allEntries.length) * 10) / 10;
  const strongMatches = allEntries.filter((e) => e.overall_score >= 90).length;
  const candidatesPerJob = perJob.map((p) => ({ name: p.job.title, value: p.ranking.length })).sort((a, b) => b.value - a.value);
  const scoreDistribution = SCORE_BANDS.map((band) => ({
    name: band.label,
    value: allEntries.filter((e) => e.overall_score >= band.min && e.overall_score < band.max).length,
  }));
  const skillGapCounts = new Map<string, number>();
  allEntries.forEach((e) => e.missing_skills.forEach((s) => skillGapCounts.set(s, (skillGapCounts.get(s) || 0) + 1)));
  const skillGaps = Array.from(skillGapCounts.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);
  const pipelineFunnel = PIPELINE_STAGES.map((stage) => ({
    name: stage,
    value: allEntries.filter((e) => (e.pipeline_status || 'NEW') === stage).length,
  }));

  return (
    <div className="space-y-6">
      <Header />

      <div className="grid grid-cols-4 gap-4">
        <StatTile label="Candidates screened" value={allEntries.length} />
        <StatTile label="Average match score" value={avgScore} />
        <StatTile label="Strong matches" value={strongMatches} />
        <StatTile label="Jobs with candidates" value={perJob.filter((p) => p.ranking.length > 0).length} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        <ChartCard title="Candidates per job">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={candidatesPerJob} layout="vertical" margin={{ left: 8, right: 16 }}>
              <CartesianGrid horizontal={false} stroke="#E3E5EB" />
              <XAxis type="number" allowDecimals={false} tick={{ fill: '#6C6E82', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fill: '#3A3C4C', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F5F6F8' }} />
              <Bar dataKey="value" fill={LENS} radius={[0, 4, 4, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Score distribution" subtitle="All scored candidates, across jobs">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={scoreDistribution} margin={{ top: 8 }}>
              <CartesianGrid vertical={false} stroke="#E3E5EB" />
              <XAxis dataKey="name" tick={{ fill: '#6C6E82', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: '#6C6E82', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F5F6F8' }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
                {scoreDistribution.map((_, i) => (
                  <Cell key={i} fill={[LENS_FAINT, LENS_LIGHT, LENS_SOFT, LENS][i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Most common missing skills" subtitle="Top gaps across all matched candidates">
          {skillGaps.length === 0 ? (
            <p className="py-16 text-center text-sm text-ink-faint">No missing skills recorded yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={skillGaps} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid horizontal={false} stroke="#E3E5EB" />
                <XAxis type="number" allowDecimals={false} tick={{ fill: '#6C6E82', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={140}
                  tick={{ fill: '#3A3C4C', fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F5F6F8' }} />
                <Bar dataKey="value" fill="#B65C43" radius={[0, 4, 4, 0]} maxBarSize={20} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Pipeline funnel" subtitle="Candidates by current stage, across jobs">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={pipelineFunnel} margin={{ top: 8 }}>
              <CartesianGrid vertical={false} stroke="#E3E5EB" />
              <XAxis dataKey="name" tick={{ fill: '#6C6E82', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: '#6C6E82', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: '#F5F6F8' }} />
              <Bar dataKey="value" fill={LENS} radius={[4, 4, 0, 0]} maxBarSize={32} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function Header() {
  return (
    <div>
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <p className="mt-1 text-sm text-ink-faint">Pipeline health and screening performance across your jobs.</p>
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="card p-4">
      <p className="text-xs text-ink-faint">{label}</p>
      <p className="mt-1.5 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <h2 className="font-medium">{title}</h2>
      {subtitle && <p className="mb-1 text-xs text-ink-faint">{subtitle}</p>}
      <div className="mt-2">{children}</div>
    </div>
  );
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded border border-line bg-paperRaised px-2.5 py-1.5 text-xs shadow-card">
      <p className="font-medium text-ink">{label}</p>
      <p className="text-ink-soft">{payload[0].value}</p>
    </div>
  );
}
