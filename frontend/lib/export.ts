import type { CandidateDetail, Match, RankingEntry } from '@/types';

function downloadBlob(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function csvCell(value: unknown): string {
  const s = String(value ?? '');
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function slug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

export function exportRankingCsv(jobTitle: string, ranking: RankingEntry[]) {
  const header = ['Rank', 'Candidate', 'Title', 'Overall score', 'Skill score', 'Experience score', 'Semantic score', 'Recommendation', 'Missing skills', 'Pipeline status'];
  const rows = ranking.map((r) => [
    r.rank,
    r.candidate_name || 'Unnamed candidate',
    r.current_title || '',
    r.overall_score,
    r.skill_score,
    r.experience_score,
    r.semantic_score,
    r.recommendation,
    r.missing_skills.join('; '),
    r.pipeline_status || 'NEW',
  ]);
  const csv = [header, ...rows].map((row) => row.map(csvCell).join(',')).join('\r\n');
  downloadBlob(`${slug(jobTitle)}-ranking.csv`, csv, 'text/csv;charset=utf-8');
}

export function exportRankingJson(jobTitle: string, ranking: RankingEntry[]) {
  downloadBlob(`${slug(jobTitle)}-ranking.json`, JSON.stringify(ranking, null, 2), 'application/json');
}

export function exportMatchJson(candidateName: string, match: Match) {
  downloadBlob(`${slug(candidateName)}-match-report.json`, JSON.stringify(match, null, 2), 'application/json');
}

export function downloadComparisonCsv(candidates: CandidateDetail[], matches: Record<string, Match | null>) {
  const header = ['Field', ...candidates.map((c) => c.name || 'Unnamed candidate')];
  const rows = [
    header,
    ['Current role', ...candidates.map((c) => `${c.current_title || ''}${c.current_company ? ` at ${c.current_company}` : ''}`)],
    ['Experience (yrs)', ...candidates.map((c) => c.total_years_experience ?? '')],
    ['Education', ...candidates.map((c) => (c.educations[0] ? `${c.educations[0].degree || ''} — ${c.educations[0].institution || ''}` : ''))],
    ['Skills', ...candidates.map((c) => c.skills.map((s) => s.skill_name).join('; '))],
    ['Overall score', ...candidates.map((c) => matches[c.id]?.overall_score ?? '')],
    ['Recommendation', ...candidates.map((c) => matches[c.id]?.recommendation ?? '')],
    ['Missing skills', ...candidates.map((c) => matches[c.id]?.missing_skills.join('; ') ?? '')],
    ['Strengths', ...candidates.map((c) => matches[c.id]?.strengths.join('; ') ?? '')],
  ];
  const csv = rows.map((row) => row.map(csvCell).join(',')).join('\r\n');
  downloadBlob('candidate-comparison.csv', csv, 'text/csv;charset=utf-8');
}

export function exportMatchCsv(candidateName: string, match: Match) {
  const rows = [
    ['Field', 'Value'],
    ['Candidate', candidateName],
    ['Overall score', match.overall_score],
    ['Recommendation', match.recommendation],
    ['Skill score', match.score_breakdown.skills],
    ['Semantic score', match.score_breakdown.semantic],
    ['Experience score', match.score_breakdown.experience],
    ['Education score', match.score_breakdown.education],
    ['Project score', match.score_breakdown.projects],
    ['Matched skills', match.matched_skills.map((s) => s.skill).join('; ')],
    ['Missing skills', match.missing_skills.join('; ')],
    ['Strengths', match.strengths.join('; ')],
    ['Areas to probe', match.improvements.join('; ')],
    ['Why this candidate', match.summary || ''],
    ['Model', match.model_name],
  ];
  const csv = rows.map((row) => row.map(csvCell).join(',')).join('\r\n');
  downloadBlob(`${slug(candidateName)}-match-report.csv`, csv, 'text/csv;charset=utf-8');
}
