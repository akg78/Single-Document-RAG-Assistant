import { useCallback, useRef, useState } from "react";

export function useCopyToClipboard(resetMs = 2000) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const copy = useCallback(
    async (text: string, id: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setCopiedId(id);
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => setCopiedId(null), resetMs);
      } catch {
        /* clipboard unavailable */
      }
    },
    [resetMs],
  );

  return { copy, copiedId };
}
