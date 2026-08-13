'use client';

import { useState, type FormEvent } from 'react';
import Link from 'next/link';
import { Search as SearchIcon, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';
import { LoadingState, EmptyState } from '@/components/common/States';

interface SearchResultItem {
  candidate_id: string;
  candidate_name: string | null;
  current_title: string | null;
  similarity: number;
  matching_evidence: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[] | null>(null);
  const [aiAvailable, setAiAvailable] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setMessage(null);
    try {
      const res: any = await api.search.candidates(query);
      setResults(res.results);
      setAiAvailable(res.ai_available);
      setMessage(res.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Search</h1>
        <p className="mt-1 text-sm text-ink-faint">
          Describe who you&apos;re looking for in plain language - TalentLens searches resume content semantically.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <SearchIcon size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint" />
          <input
            className="input pl-9"
            placeholder="e.g. Backend engineers with Python, AWS, and distributed systems experience"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          <Sparkles size={15} />
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {message && <p className="rounded bg-amber-faint px-3 py-2 text-sm text-amber">{message}</p>}
      {loading && <LoadingState label="Searching candidate resumes…" />}

      {results && results.length === 0 && !loading && (
        <EmptyState title="No matches found" description="Try a broader or differently-worded query." />
      )}

      {results && results.length > 0 && (
        <div className="card divide-y divide-line">
          {results.map((r) => (
            <Link key={r.candidate_id} href={`/candidates/${r.candidate_id}`} className="block px-5 py-4 hover:bg-paper">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{r.candidate_name || 'Unnamed candidate'}</p>
                  <p className="text-sm text-ink-faint">{r.current_title || '—'}</p>
                </div>
                <span className="font-mono text-sm text-lens">{Math.round(r.similarity * 100)}% match</span>
              </div>
              <p className="mt-2 line-clamp-2 text-xs text-ink-faint">&quot;{r.matching_evidence}&quot;</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
