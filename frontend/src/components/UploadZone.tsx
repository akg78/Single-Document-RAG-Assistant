"use client";

import { useCallback, useState } from "react";
import { uploadPdf } from "@/lib/api";
import { getErrorMessage } from "@/lib/format";
import { IconLoader, IconUpload } from "@/components/Icons";
import type { UploadResponse } from "@/types";

type Props = {
  onUploaded: (info: UploadResponse) => void;
};

export function UploadZone({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File | undefined) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are supported.");
        return;
      }
      setError(null);
      setBusy(true);
      try {
        const result = await uploadPdf(file);
        onUploaded(result);
      } catch (err) {
        setError(getErrorMessage(err, "Upload failed"));
      } finally {
        setBusy(false);
      }
    },
    [onUploaded],
  );

  return (
    <div
      className={`upload-zone ${dragging ? "is-dragging" : ""} ${busy ? "is-busy" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!busy) handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <div className="upload-icon-wrap">
        {busy ? <IconLoader size={28} /> : <IconUpload size={28} />}
      </div>
      <p className="upload-title">
        {busy ? "Processing document" : "Drop PDF here"}
      </p>
      <p className="upload-hint">
        {busy
          ? "Extracting text, generating embeddings, building index…"
          : "Single file · up to your backend limit · PDF only"}
      </p>
      {busy && (
        <div className="upload-progress" role="status" aria-label="Indexing">
          <span className="upload-progress-bar" />
        </div>
      )}
      <label className={`btn btn--primary upload-trigger ${busy ? "is-disabled" : ""}`}>
        {busy ? "Indexing…" : "Select file"}
        <input
          type="file"
          accept="application/pdf,.pdf"
          hidden
          disabled={busy}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </label>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
