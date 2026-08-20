"use client";

import { useCallback, useRef, useState } from "react";

export function useTextToSpeech() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const utterRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stop = useCallback(() => {
    if (typeof window === "undefined") return;
    window.speechSynthesis.cancel();
    setActiveId(null);
    utterRef.current = null;
  }, []);

  const speak = useCallback(
    (text: string, messageId?: string) => {
      if (typeof window === "undefined" || !window.speechSynthesis) return;

      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1;
      utter.pitch = 1;
      utter.lang = "en-US";

      utter.onstart = () => setActiveId(messageId ?? "__active__");
      utter.onend = () => {
        setActiveId(null);
        utterRef.current = null;
      };
      utter.onerror = () => {
        setActiveId(null);
        utterRef.current = null;
      };

      utterRef.current = utter;
      window.speechSynthesis.speak(utter);
    },
    [],
  );

  const toggle = useCallback(
    (text: string, messageId: string) => {
      if (activeId === messageId) {
        stop();
      } else {
        speak(text, messageId);
      }
    },
    [activeId, speak, stop],
  );

  const isSpeaking = useCallback(
    (messageId: string) => activeId === messageId,
    [activeId],
  );

  return { toggle, isSpeaking };
}
