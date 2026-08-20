"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult:
    | ((
        event: {
          results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }>;
        },
      ) => void)
    | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};

declare global {
  interface Window {
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
    SpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

type Options = {
  /** Auto-submit after this many ms of silence (default 3000). */
  silenceMs?: number;
  onAutoSubmit?: (text: string) => void;
};

export function useSpeechRecognition(options: Options = {}) {
  const { silenceMs = 3000, onAutoSubmit } = options;
  const onAutoSubmitRef = useRef(onAutoSubmit);
  onAutoSubmitRef.current = onAutoSubmit;

  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const listeningRef = useRef(false);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const transcriptRef = useRef("");

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  const scheduleAutoSubmit = useCallback(() => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      const text = transcriptRef.current.trim();
      if (!listeningRef.current || !text) return;

      listeningRef.current = false;
      setListening(false);
      clearSilenceTimer();
      recognitionRef.current?.stop();

      onAutoSubmitRef.current?.(text);
      setTranscript("");
      transcriptRef.current = "";
    }, silenceMs);
  }, [clearSilenceTimer, silenceMs]);

  useEffect(() => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Ctor) return;

    setSupported(true);
    const recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const parts: string[] = [];
      for (let i = 0; i < event.results.length; i++) {
        parts.push(event.results[i][0].transcript);
      }
      const next = parts.join(" ").trim();
      transcriptRef.current = next;
      setTranscript(next);
      if (next) scheduleAutoSubmit();
    };

    recognition.onerror = (event) => {
      if (event.error === "no-speech" || event.error === "aborted") return;
      listeningRef.current = false;
      setListening(false);
      clearSilenceTimer();
    };

    recognition.onend = () => {
      if (listeningRef.current) {
        try {
          recognition.start();
        } catch {
          listeningRef.current = false;
          setListening(false);
          clearSilenceTimer();
        }
      }
    };

    recognitionRef.current = recognition;

    return () => {
      clearSilenceTimer();
      recognition.abort();
    };
  }, [clearSilenceTimer, scheduleAutoSubmit]);

  const stop = useCallback(() => {
    listeningRef.current = false;
    clearSilenceTimer();
    recognitionRef.current?.stop();
    setListening(false);
  }, [clearSilenceTimer]);

  const start = useCallback(() => {
    if (!recognitionRef.current) return;
    setTranscript("");
    transcriptRef.current = "";
    clearSilenceTimer();
    listeningRef.current = true;
    setListening(true);
    try {
      recognitionRef.current.start();
    } catch {
      listeningRef.current = false;
      setListening(false);
    }
  }, [clearSilenceTimer]);

  return { supported, listening, transcript, start, stop, setTranscript };
}
