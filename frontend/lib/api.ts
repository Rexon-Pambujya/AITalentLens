import type {
  AuthResponse,
  BatchUploadResult,
  Candidate,
  CandidateDetail,
  Job,
  JobProfile,
  JobRequirementInput,
  Match,
  PaginatedResponse,
  RankingEntry,
  RecruiterNote,
  ResumeStatus,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public errorCode: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function buildQueryString(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null);
  return new URLSearchParams(entries as [string, string][]).toString();
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('talentlens_token');
}

export function setToken(token: string | null) {
  if (typeof window === 'undefined') return;
  if (token) window.localStorage.setItem('talentlens_token', token);
  else window.localStorage.removeItem('talentlens_token');
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let body: any = {};
    try {
      body = await response.json();
    } catch {
      // response wasn't JSON - fall through with a generic message
    }
    throw new ApiError(
      response.status,
      body.error_code || 'UNKNOWN_ERROR',
      body.message || `Request failed with status ${response.status}`,
      body.details
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
    register: (organization_name: string, email: string, password: string, name: string) =>
      request<AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ organization_name, email, password, name }),
      }),
    me: () => request<AuthResponse['user']>('/auth/me'),
  },

  jobs: {
    list: (params: { status?: string; page?: number } = {}) => {
      const qs = buildQueryString(params);
      return request<PaginatedResponse<Job>>(`/jobs${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<Job>(`/jobs/${id}`),
    create: (payload: Partial<Job> & { title: string; description: string }) =>
      request<Job>('/jobs', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: string, payload: Omit<Partial<Job>, 'requirements'> & { requirements?: JobRequirementInput[] }) =>
      request<Job>(`/jobs/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    archive: (id: string) => request<void>(`/jobs/${id}`, { method: 'DELETE' }),
    analyze: (id: string, description?: string) =>
      request<JobProfile>(`/jobs/${id}/analyze`, { method: 'POST', body: JSON.stringify({ description: description || null }) }),
    ranking: (id: string, sortBy = 'overall_score') =>
      request<RankingEntry[]>(`/jobs/${id}/ranking?sort_by=${sortBy}`),
    recalculate: (id: string) =>
      request<{ candidates_recalculated: number; failed: number }>(`/jobs/${id}/recalculate`, { method: 'POST' }),
  },

  candidates: {
    list: (params: { q?: string; page?: number } = {}) => {
      const qs = buildQueryString(params);
      return request<PaginatedResponse<Candidate>>(`/candidates${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<CandidateDetail>(`/candidates/${id}`),
    updatePipeline: (candidateId: string, jobId: string, status: string) =>
      request(`/candidates/${candidateId}/pipeline/${jobId}`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      }),
    addNote: (candidateId: string, note: string) =>
      request<RecruiterNote>(`/candidates/${candidateId}/notes`, { method: 'POST', body: JSON.stringify({ note }) }),
    listNotes: (candidateId: string) => request<RecruiterNote[]>(`/candidates/${candidateId}/notes`),
  },

  matching: {
    matchCandidate: (candidateId: string, jobId: string) =>
      request<Match>(`/candidates/${candidateId}/match/${jobId}`, { method: 'POST' }),
  },

  resumes: {
    upload: (files: File[]) => {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      return request<BatchUploadResult>(`/resumes/upload`, { method: 'POST', body: formData });
    },
    status: (id: string) => request<ResumeStatus>(`/resumes/${id}/status`),
  },

  search: {
    candidates: (query: string, limit = 20) =>
      request(`/search/candidates`, { method: 'POST', body: JSON.stringify({ query, limit }) }),
  },
};
