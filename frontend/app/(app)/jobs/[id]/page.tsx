'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Download, RefreshCw, Sparkles, Upload, Users, X } from 'lucide-react';
import { api } from '@/lib/api';
import { LoadingState, ErrorState, EmptyState } from '@/components/common/States';
import { RecommendationBadge } from '@/components/common/Badges';
import { ResumeUploadModal } from '@/components/common/ResumeUploadModal';
import { exportRankingCsv } from '@/lib/export';
import type { JobProfile, JobRequirementInput } from '@/types';

const PIPELINE_STATUSES = ['NEW', 'SCREENING', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'HIRED', 'REJECTED'] as const;

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [sortBy, setSortBy] = useState('overall_score');
  const [showUpload, setShowUpload] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [draft, setDraft] = useState<JobProfile | null>(null);
  const [draftReqs, setDraftReqs] = useState<JobRequirementInput[]>([]);
  const [savingReqs, setSavingReqs] = useState(false);
  const [newSkill, setNewSkill] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkUpdating, setBulkUpdating] = useState(false);
  const [matchingAll, setMatchingAll] = useState(false);
  const [matchAllResult, setMatchAllResult] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const jobQuery = useQuery({ queryKey: ['job', id], queryFn: () => api.jobs.get(id) });
  const rankingQuery = useQuery({
    queryKey: ['ranking', id, sortBy],
    queryFn: () => api.jobs.ranking(id, sortBy),
    enabled: !!jobQuery.data,
  });

  if (jobQuery.isLoading) return <LoadingState />;
  if (jobQuery.isError || !jobQuery.data) return <ErrorState message="Couldn't load this job." onRetry={() => jobQuery.refetch()} />;

  const job = jobQuery.data;

  async function handleAnalyze() {
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const profile = await api.jobs.analyze(id);
      setDraft(profile);
      setDraftReqs([
        ...profile.required_skills.map((r) => ({ ...r, required: true })),
        ...profile.preferred_skills.map((r) => ({ ...r, required: false })),
      ]);
    } catch {
      setAnalyzeError('Could not analyze the description. Try again, or add requirements manually.');
    } finally {
      setAnalyzing(false);
    }
  }

  function updateDraftReq(index: number, patch: Partial<JobRequirementInput>) {
    setDraftReqs((reqs) => reqs.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  function removeDraftReq(index: number) {
    setDraftReqs((reqs) => reqs.filter((_, i) => i !== index));
  }

  function addDraftReq() {
    if (!newSkill.trim()) return;
    setDraftReqs((reqs) => [...reqs, { skill: newSkill.trim(), required: true, minimum_years: null }]);
    setNewSkill('');
  }

  async function handleSaveRequirements() {
    setSavingReqs(true);
    try {
      await api.jobs.update(id, {
        requirements: draftReqs,
        // Only include fields the AI actually extracted, so we never null
        // out a value the recruiter already set manually.
        ...(draft?.seniority ? { seniority: draft.seniority } : {}),
        ...(draft?.min_experience_years != null ? { min_experience_years: draft.min_experience_years } : {}),
        ...(draft?.preferred_experience_years != null ? { preferred_experience_years: draft.preferred_experience_years } : {}),
      });
      await queryClient.invalidateQueries({ queryKey: ['job', id] });
      setDraft(null);
      setDraftReqs([]);
    } finally {
      setSavingReqs(false);
    }
  }

  async function handleMatchAll() {
    setMatchingAll(true);
    setMatchAllResult(null);
    try {
      const result = await api.jobs.recalculate(id);
      setMatchAllResult(
        result.failed > 0
          ? `Matched ${result.candidates_recalculated}, ${result.failed} failed.`
          : `Matched ${result.candidates_recalculated} candidate${result.candidates_recalculated === 1 ? '' : 's'} against this job.`
      );
      await queryClient.invalidateQueries({ queryKey: ['ranking', id] });
    } finally {
      setMatchingAll(false);
    }
  }

  async function handleBulkUpdate(status: string) {
    setBulkUpdating(true);
    try {
      await Promise.all(
        Array.from(selected).map((candidateId) => api.candidates.updatePipeline(candidateId, id, status))
      );
      await queryClient.invalidateQueries({ queryKey: ['ranking', id] });
      setSelected(new Set());
    } finally {
      setBulkUpdating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm text-ink-faint">
          <Link href="/jobs" className="hover:text-lens">
            Jobs
          </Link>{' '}
          / {job.title}
        </p>
        <div className="mt-1 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{job.title}</h1>
            <p className="mt-1 text-sm text-ink-faint">
              {job.department || 'No department'} · {job.location || 'Location TBD'}
              {job.seniority && ` · ${job.seniority}`}
              {job.min_experience_years ? ` · ${job.min_experience_years}+ yrs experience` : ''}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge bg-line/60 text-ink-soft">{job.status}</span>
            <button className="btn-primary" onClick={() => setShowUpload(true)}>
              <Upload size={15} />
              Upload resumes
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <div className="card p-5">
            <h2 className="mb-2 font-medium">Description</h2>
            <p className="whitespace-pre-wrap text-sm text-ink-soft">{job.description}</p>
          </div>

          <div className="card p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-medium">Requirements</h2>
              {!draft && (
                <button className="btn-secondary text-xs" disabled={analyzing} onClick={handleAnalyze}>
                  <Sparkles size={13} />
                  {analyzing ? 'Analyzing…' : 'Analyze description'}
                </button>
              )}
            </div>

            {analyzeError && <p className="mb-3 rounded bg-clay-faint px-3 py-2 text-sm text-clay">{analyzeError}</p>}

            {!draft && job.requirements.length === 0 && (
              <p className="text-sm text-ink-faint">No structured requirements yet - add them or analyze the description.</p>
            )}
            {!draft && job.requirements.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {job.requirements.map((r) => (
                  <span
                    key={r.id}
                    className={`badge ${r.required ? 'bg-lens-faint text-lens' : 'bg-line/60 text-ink-soft'}`}
                  >
                    {r.skill}
                    {r.minimum_years ? ` · ${r.minimum_years}+ yrs` : ''}
                    {!r.required && ' (preferred)'}
                  </span>
                ))}
              </div>
            )}

            {draft && (
              <div className="space-y-3">
                <p className="text-xs text-ink-faint">
                  AI-drafted from the description below. Review and edit before saving — nothing is persisted yet.
                </p>
                {draft.ambiguous_requirements.length > 0 && (
                  <div className="rounded bg-clay-faint px-3 py-2 text-xs text-clay">
                    {draft.ambiguous_requirements.join(' ')}
                  </div>
                )}
                <div className="space-y-1.5">
                  {draftReqs.map((r, i) => (
                    <div key={i} className="flex items-center gap-2 rounded border border-line px-2.5 py-1.5 text-sm">
                      <span className="flex-1">{r.skill}</span>
                      <select
                        className="rounded border border-line bg-paperRaised px-1.5 py-1 text-xs"
                        value={r.required ? 'required' : 'preferred'}
                        onChange={(e) => updateDraftReq(i, { required: e.target.value === 'required' })}
                      >
                        <option value="required">Required</option>
                        <option value="preferred">Preferred</option>
                      </select>
                      <input
                        type="number"
                        min={0}
                        className="input w-16 py-1 text-xs"
                        placeholder="yrs"
                        value={r.minimum_years ?? ''}
                        onChange={(e) =>
                          updateDraftReq(i, { minimum_years: e.target.value === '' ? null : Number(e.target.value) })
                        }
                      />
                      <button onClick={() => removeDraftReq(i)} className="text-ink-faint hover:text-clay" aria-label="Remove">
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                  {draftReqs.length === 0 && (
                    <p className="text-xs text-ink-faint">No requirements drafted — add one below or save an empty list.</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    className="input flex-1 text-sm"
                    placeholder="Add a skill…"
                    value={newSkill}
                    onChange={(e) => setNewSkill(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addDraftReq())}
                  />
                  <button className="btn-secondary text-xs" onClick={addDraftReq}>
                    Add
                  </button>
                </div>
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setDraft(null);
                      setDraftReqs([]);
                    }}
                  >
                    Discard
                  </button>
                  <button className="btn-primary" disabled={savingReqs} onClick={handleSaveRequirements}>
                    {savingReqs ? 'Saving…' : 'Save requirements'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="card h-fit p-5">
          <h2 className="mb-3 font-medium">Scoring weights</h2>
          <dl className="space-y-2 text-sm">
            <WeightRow label="Skills" value={job.weight_skills} />
            <WeightRow label="Semantic" value={job.weight_semantic} />
            <WeightRow label="Experience" value={job.weight_experience} />
            <WeightRow label="Education" value={job.weight_education} />
            <WeightRow label="Projects" value={job.weight_projects} />
          </dl>
        </div>
      </div>

      {rankingQuery.data && rankingQuery.data.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <StatTile label="Candidates" value={rankingQuery.data.length} />
          <StatTile label="Strong matches" value={rankingQuery.data.filter((r) => r.recommendation === 'STRONG_MATCH').length} />
          <StatTile
            label="Average score"
            value={Math.round(rankingQuery.data.reduce((s, r) => s + r.overall_score, 0) / rankingQuery.data.length)}
          />
          <StatTile
            label="Missing critical skills"
            value={rankingQuery.data.filter((r) => r.missing_skills.length > 0).length}
          />
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="font-medium">Candidate ranking</h2>
          <div className="flex items-center gap-3">
            <select
              className="rounded border border-line bg-paperRaised px-2 py-1.5 text-sm"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="overall_score">Overall score</option>
              <option value="skill_match">Skill match</option>
              <option value="experience">Experience</option>
              <option value="semantic">Semantic relevance</option>
              <option value="recently_added">Recently added</option>
            </select>
            <button
              className="btn-secondary"
              disabled={!rankingQuery.data || rankingQuery.data.length === 0}
              onClick={() => exportRankingCsv(job.title, rankingQuery.data || [])}
            >
              <Download size={14} />
              Export CSV
            </button>
            <button className="btn-secondary" onClick={() => rankingQuery.refetch()}>
              <RefreshCw size={14} />
              Refresh
            </button>
            <button className="btn-primary" disabled={matchingAll} onClick={handleMatchAll}>
              <Users size={14} />
              {matchingAll ? 'Matching…' : 'Match all candidates'}
            </button>
          </div>
        </div>

        {matchAllResult && (
          <div className="border-b border-line bg-lens-faint px-5 py-2 text-xs text-lens">{matchAllResult}</div>
        )}

        {selected.size > 0 && (
          <div className="flex items-center gap-3 border-b border-line bg-lens-faint px-5 py-2.5 text-sm">
            <span>{selected.size} selected</span>
            <button
              className="btn-secondary text-xs"
              disabled={bulkUpdating}
              onClick={() => handleBulkUpdate('SHORTLISTED')}
            >
              Shortlist selected
            </button>
            <button className="btn-secondary text-xs" disabled={bulkUpdating} onClick={() => handleBulkUpdate('REJECTED')}>
              Reject selected
            </button>
            <button className="ml-auto text-xs text-ink-faint hover:text-ink" onClick={() => setSelected(new Set())}>
              Clear
            </button>
          </div>
        )}

        {rankingQuery.isLoading && <LoadingState label="Loading candidates…" />}
        {rankingQuery.data && rankingQuery.data.length === 0 && (
          <div className="p-8">
            <EmptyState
              title="No candidates matched yet"
              description="Upload resumes here, or click &ldquo;Match all candidates&rdquo; to score everyone in your org against this job."
            />
          </div>
        )}
        {rankingQuery.data && rankingQuery.data.length > 0 && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-ink-faint">
                <th className="w-10 px-5 py-2.5">
                  <input
                    type="checkbox"
                    checked={selected.size === rankingQuery.data.length}
                    onChange={(e) =>
                      setSelected(e.target.checked ? new Set(rankingQuery.data!.map((r) => r.candidate_id)) : new Set())
                    }
                  />
                </th>
                <th className="px-5 py-2.5 font-medium">Rank</th>
                <th className="px-5 py-2.5 font-medium">Candidate</th>
                <th className="px-5 py-2.5 font-medium">Score</th>
                <th className="px-5 py-2.5 font-medium">Recommendation</th>
                <th className="px-5 py-2.5 font-medium">Missing skills</th>
                <th className="px-5 py-2.5 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rankingQuery.data.map((entry) => (
                <tr key={entry.candidate_id} className="hover:bg-paper">
                  <td className="px-5 py-3">
                    <input
                      type="checkbox"
                      checked={selected.has(entry.candidate_id)}
                      onChange={(e) =>
                        setSelected((prev) => {
                          const next = new Set(prev);
                          if (e.target.checked) next.add(entry.candidate_id);
                          else next.delete(entry.candidate_id);
                          return next;
                        })
                      }
                    />
                  </td>
                  <td className="px-5 py-3 font-mono text-ink-faint">{rankLabel(entry.rank)}</td>
                  <td className="px-5 py-3">
                    <Link href={`/candidates/${entry.candidate_id}?job=${id}`} className="font-medium hover:text-lens">
                      {entry.candidate_name || 'Unnamed candidate'}
                    </Link>
                    <p className="text-xs text-ink-faint">{entry.current_title || '—'}</p>
                  </td>
                  <td className="px-5 py-3 font-mono font-medium">{entry.overall_score}</td>
                  <td className="px-5 py-3">
                    <RecommendationBadge value={entry.recommendation} />
                  </td>
                  <td className="px-5 py-3 text-xs text-ink-faint">
                    {entry.missing_skills.length > 0 ? entry.missing_skills.join(', ') : '—'}
                  </td>
                  <td className="px-5 py-3">
                    <select
                      className="rounded border border-line bg-paperRaised px-1.5 py-1 text-xs"
                      value={entry.pipeline_status || 'NEW'}
                      onChange={async (e) => {
                        await api.candidates.updatePipeline(entry.candidate_id, id, e.target.value);
                        queryClient.invalidateQueries({ queryKey: ['ranking', id] });
                      }}
                    >
                      {PIPELINE_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {showUpload && (
        <ResumeUploadModal
          jobId={id}
          onClose={() => setShowUpload(false)}
          onComplete={() => {
            queryClient.invalidateQueries({ queryKey: ['ranking', id] });
          }}
        />
      )}
    </div>
  );
}

function WeightRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-ink-faint">{label}</dt>
      <dd className="font-mono">{Math.round(value * 100)}%</dd>
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

const MEDALS: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

function rankLabel(rank: number): string {
  return MEDALS[rank] ? `${MEDALS[rank]} ${rank}` : `#${rank}`;
}
