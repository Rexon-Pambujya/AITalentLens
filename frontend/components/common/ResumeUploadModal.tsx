'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, XCircle, Loader2, X, Sparkles } from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import type { ResumeParsedStatus } from '@/types';

/**
 * Reusable resume upload flow (spec section 46: drag-and-drop, per-file
 * progress states, individual error display). Used from both the job
 * detail page (with `jobId` set, so completed resumes are auto-matched
 * against that job - section 7 step 18) and the candidates page (general
 * upload, no auto-match).
 *
 * ZIP upload isn't supported by the backend yet (PDF/DOCX only) - the
 * dropzone only accepts what actually works rather than silently failing
 * on a ZIP the API would reject.
 */

type FileState = {
  file: File;
  resumeId?: string;
  candidateId?: string;
  status: ResumeParsedStatus | 'UPLOADING' | 'UPLOAD_FAILED';
  error?: string;
  matchScore?: number;
  matching?: boolean;
};

const ACCEPTED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];
const ACCEPTED_EXTENSIONS = '.pdf,.docx';
const TERMINAL_STATUSES: ResumeParsedStatus[] = ['COMPLETED', 'FAILED', 'DUPLICATE'];
const POLL_INTERVAL_MS = 2000;

const STATUS_LABEL: Record<string, string> = {
  UPLOADING: 'Uploading…',
  QUEUED: 'Queued',
  PROCESSING: 'Processing…',
  EXTRACTED: 'Extracting…',
  EMBEDDED: 'Embedding…',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  UPLOAD_FAILED: 'Failed',
  DUPLICATE: 'Possible duplicate',
};

export function ResumeUploadModal({
  jobId,
  onClose,
  onComplete,
}: {
  jobId?: string;
  onClose: () => void;
  onComplete?: () => void;
}) {
  const [files, setFiles] = useState<FileState[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [started, setStarted] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function addFiles(newFiles: FileList | File[]) {
    const accepted = Array.from(newFiles).filter((f) => ACCEPTED_TYPES.includes(f.type));
    const rejected = Array.from(newFiles).length - accepted.length;
    setFiles((prev) => [...prev, ...accepted.map((file) => ({ file, status: 'QUEUED' as const }))]);
    if (rejected > 0) {
      // Surfaced inline rather than a toast, since this happens at
      // selection time before any upload has started.
      setRejectionNotice(`${rejected} file(s) skipped - only PDF and DOCX are supported.`);
    }
  }

  const [rejectionNotice, setRejectionNotice] = useState<string | null>(null);

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  }, []);

  async function handleUpload() {
    setStarted(true);
    setFiles((prev) => prev.map((f) => ({ ...f, status: 'UPLOADING' })));

    try {
      const result = await api.resumes.upload(files.map((f) => f.file));
      setFiles((prev) =>
        prev.map((f) => {
          const match = result.results.find((r) => r.file_name === f.file.name);
          if (!match) return { ...f, status: 'UPLOAD_FAILED', error: 'No response for this file.' };
          if (match.status === 'FAILED') return { ...f, status: 'UPLOAD_FAILED', error: match.message };
          return {
            ...f,
            resumeId: match.resume_id,
            candidateId: match.candidate_id,
            status: match.duplicate_of_resume_id ? 'DUPLICATE' : match.status,
          };
        })
      );
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Upload failed. Please try again.';
      setFiles((prev) => prev.map((f) => ({ ...f, status: 'UPLOAD_FAILED', error: message })));
    }
  }

  // Poll each non-terminal, successfully-queued resume until it finishes
  // processing, then (if a jobId was supplied) trigger a match.
  useEffect(() => {
    if (!started) return;
    const interval = setInterval(async () => {
      setFiles((prev) => {
        const pending = prev.filter(
          (f) => f.resumeId && !TERMINAL_STATUSES.includes(f.status as ResumeParsedStatus)
        );
        if (pending.length === 0) return prev;
        pending.forEach(async (f) => {
          try {
            const status = await api.resumes.status(f.resumeId!);
            setFiles((current) =>
              current.map((c) => (c.resumeId === f.resumeId ? { ...c, status: status.parsed_status, error: status.processing_error || undefined } : c))
            );
          } catch {
            // Transient poll failure - next tick will retry; don't flip to an error state on one miss.
          }
        });
        return prev;
      });
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [started]);

  // Auto-match against the job once a resume completes, if jobId is set.
  useEffect(() => {
    if (!jobId) return;
    files
      .filter((f) => f.status === 'COMPLETED' && f.candidateId && !f.matching && f.matchScore === undefined)
      .forEach((f) => {
        setFiles((prev) => prev.map((c) => (c.resumeId === f.resumeId ? { ...c, matching: true } : c)));
        api.matching
          .matchCandidate(f.candidateId!, jobId)
          .then((match) => {
            setFiles((prev) =>
              prev.map((c) => (c.resumeId === f.resumeId ? { ...c, matching: false, matchScore: match.overall_score } : c))
            );
          })
          .catch(() => {
            setFiles((prev) => prev.map((c) => (c.resumeId === f.resumeId ? { ...c, matching: false } : c)));
          });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [files, jobId]);

  const allTerminal =
    started && files.length > 0 && files.every((f) => TERMINAL_STATUSES.includes(f.status as ResumeParsedStatus) || f.status === 'UPLOAD_FAILED');

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-ink/30 px-4" role="dialog" aria-modal="true">
      <div className="card w-full max-w-lg p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold">Upload resumes</h2>
            {jobId && <p className="text-xs text-ink-faint">Completed resumes will be automatically matched against this job.</p>}
          </div>
          <button onClick={onClose} aria-label="Close" className="text-ink-faint hover:text-ink">
            <X size={18} />
          </button>
        </div>

        {!started && (
          <>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed py-10 text-center transition-colors ${
                dragActive ? 'border-lens bg-lens-faint' : 'border-line hover:bg-paper'
              }`}
            >
              <UploadCloud size={26} className="text-ink-faint" />
              <p className="text-sm font-medium">Drag and drop resumes here, or click to browse</p>
              <p className="text-xs text-ink-faint">PDF or DOCX, up to 10MB each</p>
              <input
                ref={inputRef}
                type="file"
                multiple
                accept={ACCEPTED_EXTENSIONS}
                className="hidden"
                onChange={(e) => e.target.files && addFiles(e.target.files)}
              />
            </div>

            {rejectionNotice && <p className="mt-2 text-xs text-clay">{rejectionNotice}</p>}

            {files.length > 0 && (
              <ul className="mt-4 max-h-48 space-y-1.5 overflow-y-auto">
                {files.map((f, i) => (
                  <li key={i} className="flex items-center justify-between rounded bg-paper px-3 py-1.5 text-sm">
                    <span className="flex items-center gap-2 truncate">
                      <FileText size={14} className="shrink-0 text-ink-faint" />
                      <span className="truncate">{f.file.name}</span>
                    </span>
                    <button onClick={() => removeFile(i)} aria-label={`Remove ${f.file.name}`} className="text-ink-faint hover:text-clay">
                      <X size={14} />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="mt-5 flex justify-end gap-2">
              <button className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button className="btn-primary" disabled={files.length === 0} onClick={handleUpload}>
                Upload {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : ''}
              </button>
            </div>
          </>
        )}

        {started && (
          <>
            <ul className="max-h-72 space-y-2 overflow-y-auto">
              {files.map((f, i) => (
                <li key={i} className="rounded border border-line px-3 py-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 truncate">
                      <FileText size={14} className="shrink-0 text-ink-faint" />
                      <span className="truncate">{f.file.name}</span>
                    </span>
                    <StatusIndicator status={f.status} />
                  </div>
                  {f.error && <p className="mt-1 text-xs text-clay">{f.error}</p>}
                  {f.matching && (
                    <p className="mt-1 flex items-center gap-1 text-xs text-lens">
                      <Sparkles size={11} /> Matching against job…
                    </p>
                  )}
                  {f.matchScore !== undefined && (
                    <p className="mt-1 text-xs text-sage">Match score: {f.matchScore}</p>
                  )}
                </li>
              ))}
            </ul>

            <div className="mt-5 flex justify-end gap-2">
              <button
                className="btn-primary"
                onClick={() => {
                  onComplete?.();
                  onClose();
                }}
                disabled={!allTerminal}
              >
                {allTerminal ? 'Done' : 'Processing…'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function StatusIndicator({ status }: { status: FileState['status'] }) {
  if (status === 'COMPLETED') {
    return (
      <span className="flex items-center gap-1 text-xs text-sage">
        <CheckCircle2 size={13} /> {STATUS_LABEL[status]}
      </span>
    );
  }
  if (status === 'FAILED' || status === 'UPLOAD_FAILED') {
    return (
      <span className="flex items-center gap-1 text-xs text-clay">
        <XCircle size={13} /> {STATUS_LABEL[status]}
      </span>
    );
  }
  if (status === 'DUPLICATE') {
    return <span className="text-xs text-amber">{STATUS_LABEL[status]}</span>;
  }
  return (
    <span className="flex items-center gap-1 text-xs text-ink-faint">
      <Loader2 size={13} className="animate-spin" /> {STATUS_LABEL[status] || status}
    </span>
  );
}
