"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Scale, Search, Upload } from "lucide-react";
import { api } from "@/lib/api";
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from "@/components/common/States";
import { ResumeUploadModal } from "@/components/common/ResumeUploadModal";

export default function CandidatesPage() {
  const [query, setQuery] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();
  const router = useRouter();
  const candidatesQuery = useQuery({
    queryKey: ["candidates", query],
    queryFn: () => api.candidates.list({ q: query || undefined }),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Candidates</h1>
          <p className="mt-1 text-sm text-ink-faint">
            Everyone who has applied across your open roles.
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowUpload(true)}>
          <Upload size={15} />
          Upload resumes
        </button>
      </div>

      <div className="flex items-center justify-between gap-3">
        <div className="relative max-w-sm flex-1">
          <Search
            size={15}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
          />
          <input
            className="input pl-9"
            placeholder="Search by name, email, or title…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {selected.size >= 2 && selected.size <= 5 && (
          <button
            className="btn-primary text-sm"
            onClick={() => router.push(`/candidates/compare?ids=${Array.from(selected).join(",")}`)}
          >
            <Scale size={14} />
            Compare {selected.size}
          </button>
        )}
        {selected.size > 5 && (
          <p className="text-xs text-clay">Select up to 5 candidates to compare.</p>
        )}
      </div>

      {candidatesQuery.isLoading && <LoadingState />}
      {candidatesQuery.isError && (
        <ErrorState
          message="Couldn't load candidates."
          onRetry={() => candidatesQuery.refetch()}
        />
      )}
      {candidatesQuery.data && candidatesQuery.data.items.length === 0 && (
        <EmptyState
          title="No candidates yet"
          description="Upload resumes to start building your candidate pool."
          action={
            <button className="btn-primary" onClick={() => setShowUpload(true)}>
              Upload resumes
            </button>
          }
        />
      )}
      {candidatesQuery.data && candidatesQuery.data.items.length > 0 && (
        <div className="card divide-y divide-line">
          {candidatesQuery.data.items.map((c) => (
            <div key={c.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-paper">
              <input
                type="checkbox"
                checked={selected.has(c.id)}
                onChange={(e) =>
                  setSelected((prev) => {
                    const next = new Set(prev);
                    if (e.target.checked) next.add(c.id);
                    else next.delete(c.id);
                    return next;
                  })
                }
              />
              <Link href={`/candidates/${c.id}`} className="flex flex-1 items-center justify-between">
                <div>
                  <p className="font-medium">{c.name || "Unnamed candidate"}</p>
                  <p className="text-sm text-ink-faint">
                    {c.current_title || "No title on file"}
                    {c.current_company ? ` at ${c.current_company}` : ""}
                  </p>
                </div>
                <p className="text-sm text-ink-faint">
                  {c.total_years_experience
                    ? `${c.total_years_experience} yrs exp.`
                    : ""}
                </p>
              </Link>
            </div>
          ))}
        </div>
      )}

      {showUpload && (
        <ResumeUploadModal
          onClose={() => setShowUpload(false)}
          onComplete={() => {
            queryClient.invalidateQueries({ queryKey: ["candidates"] });
          }}
        />
      )}
    </div>
  );
}
