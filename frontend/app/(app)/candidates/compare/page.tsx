'use client';

import { useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Download, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { LoadingState, ErrorState } from '@/components/common/States';
import { RecommendationBadge } from '@/components/common/Badges';
import { downloadComparisonCsv } from '@/lib/export';
import type { CandidateDetail, Match } from '@/types';

export default function CompareCandidatesPage() {
  const ids = (useSearchParams().get('ids') || '').split(',').filter(Boolean);
  const [jobId, setJobId] = useState('');
  const [matches, setMatches] = useState<Record<string, Match | null>>({});
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

  const results = useQueries({
    queries: ids.map((id) => ({ queryKey: ['candidate', id], queryFn: () => api.candidates.get(id) })),
  });

  const loading = results.some((r) => r.isLoading);
  const errored = results.some((r) => r.isError);
  const candidates = results.map((r) => r.data).filter((c): c is CandidateDetail => !!c);

  async function handleRunMatches() {
    if (!jobId) return;
    setMatching(true);
    setMatchError(null);
    try {
      const entries = await Promise.all(
        ids.map(async (id) => {
          try {
            return [id, await api.matching.matchCandidate(id, jobId)] as const;
          } catch {
            return [id, null] as const;
          }
        })
      );
      setMatches(Object.fromEntries(entries));
    } catch {
      setMatchError('Could not run matching for one or more candidates.');
    } finally {
      setMatching(false);
    }
  }

  if (ids.length < 2) {
    return (
      <ErrorState message="Select 2-5 candidates from the Candidates page to compare them." />
    );
  }
  if (loading) return <LoadingState label="Loading candidates…" />;
  if (errored || candidates.length === 0) {
    return <ErrorState message="Couldn't load one or more candidates for comparison." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Compare candidates</h1>
          <p className="mt-1 text-sm text-ink-faint">Side-by-side view of {candidates.length} candidates.</p>
        </div>
        <button className="btn-secondary" onClick={() => downloadComparisonCsv(candidates, matches)}>
          <Download size={14} />
          Export CSV
        </button>
      </div>

      <div className="card flex items-center gap-2 p-4">
        <input
          className="input flex-1 text-sm"
          placeholder="Paste a job ID to compare match scores for these candidates…"
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
        />
        <button className="btn-primary text-sm" disabled={!jobId || matching} onClick={handleRunMatches}>
          <Sparkles size={14} />
          {matching ? 'Scoring…' : 'Run matches'}
        </button>
      </div>
      {matchError && <p className="rounded bg-clay-faint px-3 py-2 text-sm text-clay">{matchError}</p>}

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <tbody className="divide-y divide-line">
            <CompareRow label="Candidate">
              {candidates.map((c) => (
                <td key={c.id} className="px-5 py-3 font-medium">
                  <Link href={`/candidates/${c.id}`} className="hover:text-lens">
                    {c.name || 'Unnamed candidate'}
                  </Link>
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Current role">
              {candidates.map((c) => (
                <td key={c.id} className="px-5 py-3 text-ink-soft">
                  {c.current_title || '—'}
                  {c.current_company ? ` at ${c.current_company}` : ''}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Experience">
              {candidates.map((c) => (
                <td key={c.id} className="px-5 py-3 text-ink-soft">
                  {c.total_years_experience ?? totalYears(c)} yrs
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Education">
              {candidates.map((c) => (
                <td key={c.id} className="px-5 py-3 text-ink-soft">
                  {c.educations[0] ? `${c.educations[0].degree || 'Degree'} — ${c.educations[0].institution || ''}` : '—'}
                </td>
              ))}
            </CompareRow>
            <CompareRow label="Skills">
              {candidates.map((c) => (
                <td key={c.id} className="px-5 py-3">
                  <div className="flex flex-wrap gap-1">
                    {c.skills.slice(0, 8).map((s) => (
                      <span key={s.skill_name} className="badge bg-line/60 text-ink-soft">
                        {s.skill_name}
                      </span>
                    ))}
                  </div>
                </td>
              ))}
            </CompareRow>

            {Object.values(matches).some(Boolean) && (
              <>
                <CompareRow label="Overall score" highlight>
                  {candidates.map((c) => (
                    <td key={c.id} className="px-5 py-3 font-mono font-medium">
                      {matches[c.id]?.overall_score ?? '—'}
                    </td>
                  ))}
                </CompareRow>
                <CompareRow label="Recommendation">
                  {candidates.map((c) => (
                    <td key={c.id} className="px-5 py-3">
                      {matches[c.id] ? <RecommendationBadge value={matches[c.id]!.recommendation} /> : '—'}
                    </td>
                  ))}
                </CompareRow>
                <CompareRow label="Skill match">
                  {candidates.map((c) => (
                    <td key={c.id} className="px-5 py-3 text-ink-soft">
                      {matches[c.id] ? Math.round(matches[c.id]!.score_breakdown.skills) : '—'}
                    </td>
                  ))}
                </CompareRow>
                <CompareRow label="Missing skills">
                  {candidates.map((c) => (
                    <td key={c.id} className="px-5 py-3 text-xs text-ink-faint">
                      {matches[c.id]?.missing_skills.join(', ') || '—'}
                    </td>
                  ))}
                </CompareRow>
                <CompareRow label="Strengths">
                  {candidates.map((c) => (
                    <td key={c.id} className="px-5 py-3 text-xs text-ink-soft">
                      {matches[c.id]?.strengths.join('; ') || '—'}
                    </td>
                  ))}
                </CompareRow>
              </>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function totalYears(c: CandidateDetail): number {
  return Math.round(c.experiences.reduce((sum, e) => sum + (e.years || 0), 0) * 10) / 10;
}

function CompareRow({ label, highlight, children }: { label: string; highlight?: boolean; children: React.ReactNode }) {
  return (
    <tr className={highlight ? 'bg-lens-faint/40' : ''}>
      <td className="w-40 px-5 py-3 text-xs font-medium text-ink-faint">{label}</td>
      {children}
    </tr>
  );
}
