"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { askQuestion } from "@/lib/api";
import { CopyButton } from "@/components/CopyButton";
import {
  IconBot,
  IconChat,
  IconChevron,
  IconLink,
  IconMic,
  IconSend,
  IconSpark,
  IconStop,
  IconUser,
  IconVolume,
} from "@/components/Icons";
import { VOICE_SILENCE_MS, VOICE_SILENCE_SECONDS } from "@/lib/constants";
import { displayFilename, formatPercent, formatRouteType, getErrorMessage, scoreTone } from "@/lib/format";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { useTextToSpeech } from "@/hooks/useTextToSpeech";
import type { ChatMessage, UploadResponse } from "@/types";

type Props = {
  document: UploadResponse | null;
  suggestions?: string[];
};

export function ChatInterface({ document, suggestions = [] }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [openSources, setOpenSources] = useState<Record<string, boolean>>({});
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toggle, isSpeaking } = useTextToSpeech();
  const { copy, copiedId } = useCopyToClipboard();
  const submitRef = useRef<(q: string) => Promise<void>>(async () => {});

  const handleVoiceAutoSubmit = useCallback((text: string) => {
    setInput("");
    void submitRef.current(text);
  }, []);

  const { supported, listening, transcript, start, stop, setTranscript } =
    useSpeechRecognition({
      silenceMs: VOICE_SILENCE_MS,
      onAutoSubmit: handleVoiceAutoSubmit,
    });

  useEffect(() => {
    if (transcript) setInput(transcript);
  }, [transcript]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    setMessages([]);
    setError(null);
    setOpenSources({});
  }, [document?.document_id]);

  async function submitQuestion(question: string) {
    const q = question.trim();
    if (!q || !document || loading) return;

    if (listening) stop();
    setError(null);
    setInput("");
    setTranscript("");
    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: q,
    };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    try {
      const res = await askQuestion(q, document.document_id);
      const assistant: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        sources: res.sources,
        ragas: res.ragas,
        route: res.route,
      };
      setMessages((m) => [...m, assistant]);
      setOpenSources((s) => ({ ...s, [assistant.id]: true }));
    } catch (err) {
      setError(getErrorMessage(err, "Query failed"));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  submitRef.current = submitQuestion;

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void submitQuestion(input);
  }

  const docName = document ? displayFilename(document.filename) : null;

  return (
    <div className="chat">
      <header className="chat__header">
        <div>
          <h2 className="chat__title">Conversation</h2>
          <p className="chat__subtitle">
            {document
              ? `Searching · ${docName}`
              : "Upload a document to start"}
          </p>
        </div>
        {document && (
          <span className="badge badge--success badge--sm">
            <span className="badge__dot" />
            Ready
          </span>
        )}
      </header>

      <div className="chat__feed">
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty__icon">
              {document ? <IconChat size={32} /> : <IconSpark size={32} />}
            </div>
            <h3 className="empty__title">
              {document ? "Start a conversation" : "No document loaded"}
            </h3>
            <p className="empty__desc">
              {document
                ? "Ask anything about your PDF. Responses include retrieved passages with page citations."
                : "Upload a PDF in the sidebar. Indexing typically completes within a minute."}
            </p>
            {document && suggestions.length > 0 && (
              <div className="empty__suggestions">
                {suggestions.slice(0, 3).map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="empty__cta"
                    disabled={loading}
                    onClick={() => void submitQuestion(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <article key={msg.id} className={`msg msg--${msg.role}`}>
            <div className="msg__avatar" aria-hidden>
              {msg.role === "user" ? <IconUser size={15} /> : <IconBot size={15} />}
            </div>
            <div className="msg__content">
              <header className="msg__head">
                <span className="msg__author">
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
                {msg.role === "assistant" && msg.route && (
                  <span className="msg__type">
                    {formatRouteType(msg.route.query_type)}
                  </span>
                )}
              </header>
              <div className="msg__body">{msg.content}</div>

              {msg.role === "assistant" && (
                <div className="msg__toolbar">
                  <CopyButton
                    text={msg.content}
                    copyId={msg.id}
                    copiedId={copiedId}
                    onCopy={copy}
                  />

                  <button
                    type="button"
                    className={`btn btn--ghost btn--sm ${isSpeaking(msg.id) ? "is-active" : ""}`}
                    onClick={() => toggle(msg.content, msg.id)}
                    aria-pressed={isSpeaking(msg.id)}
                  >
                    {isSpeaking(msg.id) ? (
                      <IconStop size={16} />
                    ) : (
                      <IconVolume size={16} />
                    )}
                    {isSpeaking(msg.id) ? "Stop" : "Read aloud"}
                  </button>

                  {msg.sources && msg.sources.length > 0 && (
                    <button
                      type="button"
                      className="btn btn--ghost btn--sm"
                      onClick={() =>
                        setOpenSources((s) => ({ ...s, [msg.id]: !s[msg.id] }))
                      }
                      aria-expanded={openSources[msg.id] ?? false}
                    >
                      <IconLink size={16} />
                      Sources ({msg.sources.length})
                      <IconChevron open={openSources[msg.id]} />
                    </button>
                  )}
                </div>
              )}

              {msg.role === "assistant" &&
                msg.sources &&
                msg.sources.length > 0 &&
                openSources[msg.id] && (
                  <ul className="sources">
                    {msg.sources.map((s) => (
                      <li key={s.id} className="source-card">
                        <div className="source-card__head">
                          <span className="source-card__page">Page {s.page}</span>
                          <span className="source-card__meta">
                            Chunk {s.chunk_index}
                            {s.score != null && ` · ${formatPercent(s.score)}% match`}
                          </span>
                          <CopyButton
                            text={s.snippet}
                            copyId={`src-${s.id}`}
                            copiedId={copiedId}
                            onCopy={copy}
                            variant="icon"
                            label="Copy snippet"
                          />
                        </div>
                        <p className="source-card__text">{s.snippet}</p>
                      </li>
                    ))}
                  </ul>
                )}

              {msg.role === "assistant" && msg.ragas && (
                <details className="metrics">
                  <summary>RAG evaluation</summary>
                  <div className="metrics__grid">
                    {(
                      [
                        ["Faithfulness", msg.ragas.faithfulness],
                        ["Relevancy", msg.ragas.answer_relevancy],
                        ["Precision", msg.ragas.context_precision],
                      ] as const
                    ).map(([label, value]) => (
                      <div key={label} className="metric">
                        <div className="metric__head">
                          <span className="metric__label">{label}</span>
                          <span className="metric__value">
                            {value != null ? value.toFixed(2) : "—"}
                          </span>
                        </div>
                        {value != null && (
                          <div className="metric__track">
                            <span
                              className={`metric__fill metric__fill--${scoreTone(value)}`}
                              style={{ width: `${formatPercent(value)}%` }}
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </article>
        ))}

        {loading && (
          <article className="msg msg--assistant">
            <div className="msg__avatar" aria-hidden>
              <IconBot size={15} />
            </div>
            <div className="msg__content msg__content--loading">
              <span className="typing" aria-hidden>
                <span />
                <span />
                <span />
              </span>
              <span>Retrieving context and generating response…</span>
            </div>
          </article>
        )}
        <div ref={bottomRef} />
      </div>

      {suggestions.length > 0 && document && messages.length > 0 && (
        <div className="prompts">
          <span className="prompts__label">Suggestions</span>
          <div className="prompts__list">
            {suggestions.slice(0, 4).map((s) => (
              <button
                key={s}
                type="button"
                className="prompt-chip"
                disabled={loading}
                onClick={() => void submitQuestion(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert--error" role="alert">
          <span>{error}</span>
          <button type="button" className="alert__close" onClick={() => setError(null)} aria-label="Dismiss">
            ×
          </button>
        </div>
      )}

      {listening && (
        <div className="voice-banner" role="status">
          <span className="voice-banner__pulse" />
          Listening — pause for {VOICE_SILENCE_SECONDS} seconds to send automatically
        </div>
      )}

      <form className="composer" onSubmit={onSubmit}>
        <div className={`composer__field ${listening ? "composer__field--active" : ""}`}>
          <input
            ref={inputRef}
            className="composer__input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              listening
                ? "Speak now…"
                : document
                  ? "Ask a question about your document"
                  : "Upload a PDF to enable chat"
            }
            disabled={!document || loading}
            aria-label="Message"
          />
          <div className="composer__actions">
            {supported && (
              <button
                type="button"
                className={`btn btn--icon ${listening ? "is-recording" : ""}`}
                disabled={!document || loading}
                onClick={() => (listening ? stop() : start())}
                title={listening ? "Cancel" : "Voice input"}
                aria-label={listening ? "Cancel voice input" : "Voice input"}
              >
                <IconMic size={18} />
              </button>
            )}
            <button
              type="submit"
              className="btn btn--primary btn--icon"
              disabled={!document || loading || !input.trim()}
              aria-label="Send message"
            >
              <IconSend size={18} />
            </button>
          </div>
        </div>
        <p className="composer__hint">
          Press Enter to send · Voice auto-submits after {VOICE_SILENCE_SECONDS}s silence
        </p>
      </form>
    </div>
  );
}
