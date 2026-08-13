'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams, useSearchParams } from 'next/navigation';
import { Check, Download, Mail, Phone, MapPin, Linkedin, Github, Globe, Sparkles, X as XIcon } from 'lucide-react';
import { api } from '@/lib/api';
import { LoadingState, ErrorState } from '@/components/common/States';
import { ScoreRing } from '@/components/common/ScoreRing';
import { RecommendationBadge, SkillLevelBadge } from '@/components/common/Badges';
import { exportMatchCsv, exportMatchJson } from '@/lib/export';
import type { Match } from '@/types';

export default function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = useSearchParams().get('job');
  const [note, setNote] = useState('');
  const [match, setMatch] = useState<Match | null>(null);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [matching, setMatching] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<string | null>(null);
  const [updatingPipeline, setUpdatingPipeline] = useState(false);
  const queryClient = useQueryClient();

  const candidateQuery = useQuery({ queryKey: ['candidate', id], queryFn: () => api.candidates.get(id) });
  const notesQuery = useQuery({ queryKey: ['notes', id], queryFn: () => api.candidates.listNotes(id) });

  async function handlePipelineChange(status: string) {
    if (!jobId) return;
    setUpdatingPipeline(true);
    try {
      await api.candidates.updatePipeline(id, jobId, status);
      setPipelineStatus(status);
      queryClient.invalidateQueries({ queryKey: ['ranking', jobId] });
    } finally {
      setUpdatingPipeline(false);
    }
  }

  async function handleAddNote(e: FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    await api.candidates.addNote(id, note);
    setNote('');
    queryClient.invalidateQueries({ queryKey: ['notes', id] });
  }

  async function runMatch(targetJobId: string) {
    setMatching(true);
    setMatchError(null);
    try {
      const result = await api.matching.matchCandidate(id, targetJobId);
      setMatch(result as Match);
    } catch {
      setMatchError('Could not run matching for this job. Confirm the job ID and try again.');
    } finally {
      setMatching(false);
    }
  }

  // Opened from a job's ranking (?job=...) - load that job's existing match
  // immediately rather than making the recruiter re-paste the job ID.
  useEffect(() => {
    if (jobId) runMatch(jobId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, id]);

  if (candidateQuery.isLoading) return <LoadingState />;
  if (candidateQuery.isError || !candidateQuery.data)
    return <ErrorState message="Couldn't load this candidate." onRetry={() => candidateQuery.refetch()} />;

  const candidate = candidateQuery.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{candidate.name || 'Unnamed candidate'}</h1>
            <p className="mt-1 text-ink-soft">
              {candidate.current_title || 'No title on file'}
              {candidate.current_company ? ` at ${candidate.current_company}` : ''}
            </p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-ink-faint">
              {candidate.email && (
                <IconRow icon={Mail}>
                  <a href={`mailto:${candidate.email}`} className="hover:text-lens">
                    {candidate.email}
                  </a>
                </IconRow>
              )}
              {candidate.phone && <IconRow icon={Phone}>{candidate.phone}</IconRow>}
              {candidate.location && <IconRow icon={MapPin}>{candidate.location}</IconRow>}
              {candidate.linkedin_url && (
                <IconRow icon={Linkedin}>
                  <a href={candidate.linkedin_url} target="_blank" rel="noreferrer" className="hover:text-lens">
                    LinkedIn
                  </a>
                </IconRow>
              )}
              {candidate.github_url && (
                <IconRow icon={Github}>
                  <a href={candidate.github_url} target="_blank" rel="noreferrer" className="hover:text-lens">
                    GitHub
                  </a>
                </IconRow>
              )}
              {candidate.portfolio_url && (
                <IconRow icon={Globe}>
                  <a href={candidate.portfolio_url} target="_blank" rel="noreferrer" className="hover:text-lens">
                    Portfolio
                  </a>
                </IconRow>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
              <button
                className="btn-secondary"
                disabled={!jobId || updatingPipeline}
                onClick={() => handlePipelineChange('REJECTED')}
              >
                Reject
              </button>
              <button
                className="btn-secondary"
                disabled={!jobId || updatingPipeline}
                onClick={() => handlePipelineChange('INTERVIEW')}
              >
                Move to interview
              </button>
              <button
                className="btn-primary"
                disabled={!jobId || updatingPipeline}
                onClick={() => handlePipelineChange('SHORTLISTED')}
              >
                Shortlist
              </button>
            </div>
            {!jobId && (
              <p className="text-xs text-ink-faint">Open from a job&apos;s ranking to update pipeline status.</p>
            )}
            {pipelineStatus && <p className="text-xs text-sage">Status updated: {pipelineStatus}</p>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <MatchAnalysisCard
            candidateId={id}
            candidateName={candidate.name || 'Unnamed candidate'}
            match={match}
            initialJobId={jobId}
            onMatch={runMatch}
            matching={matching}
            matchError={matchError}
          />

          <SectionCard title="Experience">
            {candidate.experiences.length === 0 ? (
              <EmptyRow text="No experience extracted yet." />
            ) : (
              <ul className="space-y-4">
                {candidate.experiences.map((exp) => (
                  <li key={exp.id}>
                    <p className="font-medium">
                      {exp.title || 'Unknown title'} {exp.company && <span className="text-ink-faint">· {exp.company}</span>}
                    </p>
                    <p className="text-xs text-ink-faint">
                      {exp.start_date || '?'} – {exp.end_date || 'Present'} {exp.years ? `· ${exp.years} yrs` : ''}
                    </p>
                    {exp.description && <p className="mt-1 whitespace-pre-wrap text-sm text-ink-soft">{exp.description}</p>}
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>

          <SectionCard title="Education">
            {candidate.educations.length === 0 ? (
              <EmptyRow text="No education extracted yet." />
            ) : (
              <ul className="space-y-2">
                {candidate.educations.map((ed) => (
                  <li key={ed.id} className="text-sm">
                    <span className="font-medium">{ed.degree || 'Degree'}</span>
                    {ed.field && `, ${ed.field}`} <span className="text-ink-faint">— {ed.institution || 'Institution'}</span>
                    {ed.end_year && <span className="text-ink-faint"> ({ed.end_year})</span>}
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard title="Skills">
            {candidate.skills.length === 0 ? (
              <EmptyRow text="No skills extracted yet." />
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {candidate.skills.map((s) => (
                  <span key={s.skill_name} className="badge bg-line/60 text-ink-soft">
                    {s.skill_name}
                    {s.years_experience ? ` · ${s.years_experience}y` : ''}
                  </span>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Recruiter notes">
            <form onSubmit={handleAddNote} className="mb-3 space-y-2">
              <textarea
                className="input min-h-[70px] resize-y text-sm"
                placeholder="Add a note about this candidate…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <button type="submit" className="btn-secondary w-full justify-center text-sm">
                Add note
              </button>
            </form>
            {notesQuery.data && notesQuery.data.length > 0 ? (
              <ul className="space-y-3">
                {notesQuery.data.map((n) => (
                  <li key={n.id} className="border-t border-line pt-3 text-sm">
                    <p className="text-ink-soft">{n.note}</p>
                    <p className="mt-1 text-xs text-ink-faint">{new Date(n.created_at).toLocaleString()}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-ink-faint">No notes yet.</p>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

function MatchAnalysisCard({
  candidateId,
  candidateName,
  match,
  initialJobId,
  onMatch,
  matching,
  matchError,
}: {
  candidateId: string;
  candidateName: string;
  match: Match | null;
  initialJobId: string | null;
  onMatch: (jobId: string) => void;
  matching: boolean;
  matchError: string | null;
}) {
  const [jobId, setJobId] = useState(initialJobId || '');

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-medium">Match analysis</h2>
        <div className="flex items-center gap-2">
          {match && (
            <>
              <button className="btn-secondary text-xs" onClick={() => exportMatchCsv(candidateName, match)}>
                <Download size={13} />
                CSV
              </button>
              <button className="btn-secondary text-xs" onClick={() => exportMatchJson(candidateName, match)}>
                <Download size={13} />
                JSON
              </button>
            </>
          )}
          <input
            className="input w-64 text-xs"
            placeholder="Paste a job ID to compare against…"
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
          />
          <button className="btn-primary text-xs" disabled={!jobId || matching} onClick={() => onMatch(jobId)}>
            <Sparkles size={14} />
            {matching ? 'Scoring…' : 'Run match'}
          </button>
        </div>
      </div>

      {matchError && <p className="mb-3 rounded bg-clay-faint px-3 py-2 text-sm text-clay">{matchError}</p>}

      {!match ? (
        <p className="py-8 text-center text-sm text-ink-faint">
          {matching
            ? 'Scoring this candidate…'
            : "Enter a job ID above and run a match to see this candidate's compatibility score, skill matrix, and AI insights."}
        </p>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-8">
            <ScoreRing score={match.overall_score} size={110} />
            <div className="flex-1 space-y-2.5">
              <RecommendationBadge value={match.recommendation} />
              <BreakdownBar label="Skills" value={match.score_breakdown.skills} />
              <BreakdownBar label="Semantic" value={match.score_breakdown.semantic} />
              <BreakdownBar label="Experience" value={match.score_breakdown.experience} />
              <BreakdownBar label="Education" value={match.score_breakdown.education} />
              <BreakdownBar label="Projects" value={match.score_breakdown.projects} />
            </div>
          </div>

          {match.summary && (
            <div className="rounded border border-lens-faint bg-lens-faint/40 p-4">
              <h3 className="mb-1 text-sm font-medium text-lens">Why this candidate?</h3>
              <p className="text-sm text-ink-soft">{match.summary}</p>
            </div>
          )}

          {(match.matched_skills.length > 0 || match.missing_skills.length > 0) && (
            <div>
              <h3 className="mb-2 text-sm font-medium">Skill matrix</h3>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-line">
                  {match.matched_skills.map((s) => (
                    <tr key={s.skill}>
                      <td className="py-1.5 pr-3">
                        <span className="inline-flex items-center gap-1.5">
                          <Check size={14} className="text-sage" />
                          {s.skill}
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 text-ink-faint">{s.candidate_years ? `${s.candidate_years} yrs` : '—'}</td>
                      <td className="py-1.5 text-right">
                        <SkillLevelBadge level={s.level} />
                      </td>
                    </tr>
                  ))}
                  {match.missing_skills.map((skill) => (
                    <tr key={skill}>
                      <td className="py-1.5 pr-3">
                        <span className="inline-flex items-center gap-1.5">
                          <XIcon size={14} className="text-clay" />
                          {skill}
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 text-ink-faint">—</td>
                      <td className="py-1.5 text-right">
                        <SkillLevelBadge level="MISSING" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="mb-1.5 text-sm font-medium text-sage">Strengths</h3>
              <ul className="space-y-1 text-sm text-ink-soft">
                {match.strengths.map((s, i) => (
                  <li key={i}>+ {s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-1.5 text-sm font-medium text-clay">Areas to probe</h3>
              <ul className="space-y-1 text-sm text-ink-soft">
                {match.improvements.map((s, i) => (
                  <li key={i}>− {s}</li>
                ))}
              </ul>
            </div>
          </div>

          {match.interview_focus.length > 0 && (
            <div>
              <h3 className="mb-1.5 text-sm font-medium">Suggested interview focus</h3>
              <ul className="space-y-1 text-sm text-ink-soft">
                {match.interview_focus.map((f, i) => (
                  <li key={i}>? {f}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="text-[11px] text-ink-faint">
            Scored with {match.model_name} · scoring v{match.scoring_version} · this is decision support, not an automated
            hiring decision.
          </p>
        </div>
      )}
    </div>
  );
}

function BreakdownBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-ink-faint">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line">
        <div className="h-full rounded-full bg-lens" style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="w-8 text-right font-mono text-ink-soft">{Math.round(value)}</span>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card p-5">
      <h2 className="mb-3 font-medium">{title}</h2>
      {children}
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return <p className="text-sm text-ink-faint">{text}</p>;
}

function IconRow({ icon: Icon, children }: { icon: typeof Mail; children: React.ReactNode }) {
  return (
    <span className="flex items-center gap-1.5">
      <Icon size={13} />
      {children}
    </span>
  );
}
