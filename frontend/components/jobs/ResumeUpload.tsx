"use client";

import { useState, useRef } from "react";
import { Upload, X, Check, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

interface ResumeUploadProps {
  jobId: string;
  onSuccess?: () => void;
}

export function ResumeUpload({ jobId, onSuccess }: ResumeUploadProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    success: number;
    failed: number;
    errors: string[];
  }>({ success: 0, failed: 0, errors: [] });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = Array.from(e.target.files || []);
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    const token =
      typeof window !== "undefined"
        ? window.localStorage.getItem("talentlens_token")
        : null;
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

    setIsUploading(true);
    setUploadStatus({ success: 0, failed: 0, errors: [] });

    const newErrors: string[] = [];
    let successCount = 0;
    let failCount = 0;

    for (const file of files) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("job_id", jobId);

        const response = await fetch(`${apiBaseUrl}/resumes/upload`, {
          method: "POST",
          body: formData,
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        if (response.ok) {
          successCount++;
        } else {
          failCount++;
          const error = await response.json();
          newErrors.push(`${file.name}: ${error.message || "Upload failed"}`);
        }
      } catch (error) {
        failCount++;
        newErrors.push(
          `${file.name}: ${error instanceof Error ? error.message : "Unknown error"}`,
        );
      }
    }

    setUploadStatus({
      success: successCount,
      failed: failCount,
      errors: newErrors,
    });
    setFiles([]);
    setIsUploading(false);

    if (successCount > 0 && onSuccess) {
      setTimeout(onSuccess, 1000);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg bg-lens px-4 py-2 text-sm font-medium text-white hover:bg-lens/90 transition-colors"
      >
        <Upload size={16} />
        Upload Resumes
      </button>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="card max-w-lg w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="font-medium text-lg">Upload Resumes</h2>
          <button
            onClick={() => {
              setIsOpen(false);
              setFiles([]);
              setUploadStatus({ success: 0, failed: 0, errors: [] });
            }}
            className="text-ink-faint hover:text-ink transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Upload Area */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-line rounded-lg p-8 text-center cursor-pointer hover:bg-paper transition-colors"
          >
            <Upload className="mx-auto mb-2 text-ink-faint" size={32} />
            <p className="font-medium mb-1">
              Drop files here or click to browse
            </p>
            <p className="text-sm text-ink-faint">
              Supports PDF and DOCX files (max 10MB each)
            </p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">
                Files selected: {files.length}
              </p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-paper p-3 rounded-lg"
                  >
                    <p className="text-sm truncate">{file.name}</p>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-ink-faint hover:text-ink transition-colors flex-shrink-0"
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Upload Status */}
          {uploadStatus.success > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex gap-3">
              <Check className="text-green-600 flex-shrink-0" size={20} />
              <div>
                <p className="font-medium text-green-900">
                  {uploadStatus.success} resume(s) uploaded successfully
                </p>
              </div>
            </div>
          )}

          {uploadStatus.failed > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex gap-3 mb-2">
                <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
                <p className="font-medium text-red-900">
                  {uploadStatus.failed} upload(s) failed
                </p>
              </div>
              <ul className="text-sm text-red-800 space-y-1 ml-7">
                {uploadStatus.errors.map((error, idx) => (
                  <li key={idx}>• {error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => {
                setIsOpen(false);
                setFiles([]);
                setUploadStatus({ success: 0, failed: 0, errors: [] });
              }}
              className="flex-1 px-4 py-2 rounded-lg border border-line text-sm font-medium hover:bg-paper transition-colors"
            >
              Close
            </button>
            <button
              onClick={handleUpload}
              disabled={files.length === 0 || isUploading}
              className="flex-1 px-4 py-2 rounded-lg bg-lens text-white text-sm font-medium hover:bg-lens/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isUploading
                ? "Uploading..."
                : `Upload ${files.length} file${files.length !== 1 ? "s" : ""}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
