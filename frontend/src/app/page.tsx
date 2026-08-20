"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatInterface } from "@/components/ChatInterface";
import { UploadZone } from "@/components/UploadZone";
import { IconCheck, IconFile, IconLogo } from "@/components/Icons";
import { fetchSuggestions, fetchTopics, healthCheck } from "@/lib/api";
import { displayFilename } from "@/lib/format";
import type { UploadResponse } from "@/types";

const STEPS = [
  "Upload your PDF document",
  "Wait for semantic indexing",
  "Ask questions in natural language",
  "Verify answers via source citations",
];

export default function HomePage() {
  const [document, setDocument] = useState<UploadResponse | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [apiOk, setApiOk] = useState<boolean | null>(null);

  useEffect(() => {
    healthCheck()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  const onUploaded = useCallback(async (info: UploadResponse) => {
    setDocument(info);
    try {
      const [t, s] = await Promise.all([
        fetchTopics(info.document_id),
        fetchSuggestions(info.document_id),
      ]);
      setTopics(t);
      setSuggestions(s);
    } catch {
      setTopics([]);
      setSuggestions([]);
    }
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header__brand">
          <span className="header__logo">
            <IconLogo size={26} />
          </span>
          <div>
            <h1 className="header__title">DocRAG — Document Q&A</h1>
            <p className="header__tagline">Grounded answers from a single PDF</p>
          </div>
        </div>
        <div className="header__meta">
          <div className="header__stack" aria-label="Pipeline">
            <span className="stack-chip">FAISS</span>
            <span className="stack-chip">MiniLM</span>
            <span className="stack-chip">Rerank</span>
          </div>
          <div
            className={`badge ${apiOk === false ? "badge--error" : apiOk ? "badge--success" : "badge--neutral"}`}
            role="status"
          >
            <span className="badge__dot" />
            {apiOk === null ? "Connecting" : apiOk ? "Connected" : "Offline"}
          </div>
        </div>
      </header>

      <main className="workspace">
        <aside className="panel panel--sidebar">
          <section className="panel__section">
            <header className="section-head">
              <span className="section-head__step">01</span>
              <h2 className="section-head__title">Document</h2>
            </header>
            <UploadZone onUploaded={onUploaded} />
          </section>

          {document && (
            <section className="panel__section doc-preview">
              <header className="section-head">
                <span className="section-head__step section-head__step--done">
                  <IconCheck size={12} />
                </span>
                <h2 className="section-head__title">Indexed</h2>
              </header>
              <div className="doc-preview__card">
                <div className="doc-preview__icon">
                  <IconFile size={22} />
                </div>
                <div>
                  <p className="doc-preview__name" title={document.filename}>
                    {displayFilename(document.filename)}
                  </p>
                  <div className="doc-preview__meta">
                    <span>{document.num_pages} pages</span>
                    <span className="dot" />
                    <span>{document.num_chunks} chunks</span>
                  </div>
                </div>
              </div>
            </section>
          )}

          {topics.length > 0 && (
            <section className="panel__section">
              <header className="section-head">
                <span className="section-head__step">02</span>
                <h2 className="section-head__title">Topics</h2>
              </header>
              <div className="tag-list">
                {topics.slice(0, 12).map((t) => (
                  <span key={t} className="tag">
                    {t}
                  </span>
                ))}
              </div>
            </section>
          )}

          {!document && (
            <section className="panel__section">
              <header className="section-head">
                <span className="section-head__step">—</span>
                <h2 className="section-head__title">Quick start</h2>
              </header>
              <ol className="guide__list">
                {STEPS.map((step, i) => (
                  <li key={step}>
                    <span className="guide__num">{i + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
            </section>
          )}
        </aside>

        <section className="panel panel--main">
          <ChatInterface document={document} suggestions={suggestions} />
        </section>
      </main>

      <footer className="footer">
        <span>Single-Document RAG Assistant · Grounded responses with page-level citations</span>
      </footer>
    </div>
  );
}
