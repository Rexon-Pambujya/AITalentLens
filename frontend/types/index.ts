export type UserRole = 'ADMIN' | 'RECRUITER' | 'HIRING_MANAGER';

export interface User {
  id: string;
  organization_id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type JobStatus = 'DRAFT' | 'ANALYZING' | 'ACTIVE' | 'ARCHIVED';

export interface JobRequirement {
  id: string;
  skill: string;
  normalized_skill: string;
  importance: number;
  required: boolean;
  minimum_years: number | null;
}

export interface Job {
  id: string;
  organization_id: string;
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string | null;
  description: string;
  status: JobStatus;
  seniority: string | null;
  min_experience_years: number | null;
  preferred_experience_years: number | null;
  weight_skills: number;
  weight_semantic: number;
  weight_experience: number;
  weight_education: number;
  weight_projects: number;
  requirements: JobRequirement[];
  created_at: string;
  updated_at: string;
}

export type RecommendationLabel = 'STRONG_MATCH' | 'GOOD_MATCH' | 'MODERATE_MATCH' | 'NOT_SUITABLE';

export interface RankingEntry {
  rank: number;
  candidate_id: string;
  candidate_name: string | null;
  current_title: string | null;
  overall_score: number;
  skill_score: number;
  experience_score: number;
  semantic_score: number;
  recommendation: RecommendationLabel;
  missing_skills: string[];
  pipeline_status: string | null;
}

export interface ScoreBreakdown {
  skills: number;
  semantic: number;
  experience: number;
  education: number;
  projects: number;
}

export interface Evidence {
  claim: string;
  source: string;
  text: string | null;
}

export interface MatchedSkill {
  skill: string;
  level: 'EXACT' | 'RELATED' | 'PARTIAL' | 'MISSING';
  candidate_years: number | null;
}

export interface Match {
  id: string;
  job_id: string;
  candidate_id: string;
  overall_score: number;
  recommendation: RecommendationLabel;
  score_breakdown: ScoreBreakdown;
  matched_skills: MatchedSkill[];
  missing_skills: string[];
  partial_skills: string[];
  strengths: string[];
  improvements: string[];
  interview_focus: string[];
  evidence: Evidence[];
  reasoning: Record<string, string>;
  summary: string | null;
  model_name: string;
  embedding_model: string;
  prompt_version: string;
  scoring_version: string;
  created_at: string;
}

export interface Experience {
  id: string;
  company: string | null;
  title: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  years: number | null;
}

export interface Education {
  id: string;
  institution: string | null;
  degree: string | null;
  field: string | null;
  start_year: number | null;
  end_year: number | null;
}

export interface CandidateSkill {
  skill_name: string;
  proficiency: string | null;
  years_experience: number | null;
}

export interface Candidate {
  id: string;
  organization_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  total_years_experience: number | null;
  current_title: string | null;
  current_company: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateDetail extends Candidate {
  experiences: Experience[];
  educations: Education[];
  certifications: { id: string; name: string; issuer: string | null; issue_date: string | null }[];
  projects: { id: string; name: string; description: string | null; technologies: string[] | null }[];
  skills: CandidateSkill[];
}

export interface RecruiterNote {
  id: string;
  note: string;
  user_id: string | null;
  created_at: string;
}

export type ResumeParsedStatus =
  | 'QUEUED'
  | 'PROCESSING'
  | 'EXTRACTED'
  | 'EMBEDDED'
  | 'COMPLETED'
  | 'FAILED'
  | 'DUPLICATE';

export interface ResumeUploadResult {
  resume_id: string;
  candidate_id: string;
  file_name: string;
  status: ResumeParsedStatus | 'FAILED';
  duplicate_of_resume_id: string | null;
  message: string;
}

export interface BatchUploadResult {
  total: number;
  queued: number;
  duplicates: number;
  rejected: number;
  results: ResumeUploadResult[];
}

export interface ResumeStatus {
  id: string;
  candidate_id: string;
  file_name: string;
  mime_type: string;
  parsed_status: ResumeParsedStatus;
  processing_error: string | null;
  created_at: string;
}

export interface ExtractedRequirement {
  skill: string;
  importance: number;
  required: boolean;
  minimum_years: number | null;
}

export interface JobProfile {
  title: string | null;
  seniority: string | null;
  department: string | null;
  required_skills: ExtractedRequirement[];
  preferred_skills: ExtractedRequirement[];
  min_experience_years: number | null;
  preferred_experience_years: number | null;
  ambiguous_requirements: string[];
}

export interface JobRequirementInput {
  skill: string;
  importance?: number;
  required: boolean;
  minimum_years?: number | null;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}
