import type { RecommendationLabel } from '@/types';

const RECOMMENDATION_STYLES: Record<RecommendationLabel, string> = {
  STRONG_MATCH: 'bg-sage-faint text-sage',
  GOOD_MATCH: 'bg-lens-faint text-lens',
  MODERATE_MATCH: 'bg-amber-faint text-amber',
  NOT_SUITABLE: 'bg-clay-faint text-clay',
};

const RECOMMENDATION_LABELS: Record<RecommendationLabel, string> = {
  STRONG_MATCH: 'Strong match',
  GOOD_MATCH: 'Good match',
  MODERATE_MATCH: 'Moderate match',
  NOT_SUITABLE: 'Not suitable',
};

export function RecommendationBadge({ value }: { value: RecommendationLabel }) {
  return <span className={`badge ${RECOMMENDATION_STYLES[value]}`}>{RECOMMENDATION_LABELS[value]}</span>;
}

const SKILL_LEVEL_STYLES: Record<string, string> = {
  EXACT: 'bg-sage-faint text-sage',
  RELATED: 'bg-amber-faint text-amber',
  PARTIAL: 'bg-amber-faint text-amber',
  MISSING: 'bg-clay-faint text-clay',
};

const SKILL_LEVEL_LABELS: Record<string, string> = {
  EXACT: 'Match',
  RELATED: 'Related',
  PARTIAL: 'Partial',
  MISSING: 'Missing',
};

export function SkillLevelBadge({ level }: { level: string }) {
  return <span className={`badge ${SKILL_LEVEL_STYLES[level] || ''}`}>{SKILL_LEVEL_LABELS[level] || level}</span>;
}

const PIPELINE_STYLES: Record<string, string> = {
  NEW: 'bg-line/60 text-ink-soft',
  SCREENING: 'bg-lens-faint text-lens',
  SHORTLISTED: 'bg-sage-faint text-sage',
  INTERVIEW: 'bg-amber-faint text-amber',
  OFFER: 'bg-sage-faint text-sage',
  HIRED: 'bg-sage text-white',
  REJECTED: 'bg-clay-faint text-clay',
};

export function PipelineBadge({ status }: { status: string | null }) {
  if (!status) return <span className="badge bg-line/60 text-ink-faint">New</span>;
  return <span className={`badge ${PIPELINE_STYLES[status] || ''}`}>{status.charAt(0) + status.slice(1).toLowerCase()}</span>;
}
