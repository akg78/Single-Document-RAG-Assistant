/** Inline SVG icons — no emoji, consistent 20px stroke style */

type IconProps = { className?: string; size?: number };

const defaults = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
});

export function IconLogo({ className, size = 28 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M14 3v5h5M9 13h6M9 17h4" />
    </svg>
  );
}

export function IconUpload({ className, size = 24 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M12 16V4m0 0 4 4m-4-4-4 4" />
      <path d="M4 17v1a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-1" />
    </svg>
  );
}

export function IconFile({ className, size = 24 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M8 13h8M8 17h5" />
    </svg>
  );
}

export function IconChat({ className, size = 24 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
    </svg>
  );
}

export function IconMic({ className, size = 20 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 19v4M8 23h8" />
    </svg>
  );
}

export function IconSend({ className, size = 20 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="m22 2-7 20-4-9-9-4 20-7z" />
      <path d="M22 2 11 13" />
    </svg>
  );
}

export function IconVolume({ className, size = 18 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M11 5 6 9H2v6h4l5 4V5z" />
      <path d="M15.54 8.46a5 5 0 0 1 0 7.07M19.07 4.93a10 10 0 0 1 0 14.14" />
    </svg>
  );
}

export function IconStop({ className, size = 18 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  );
}

export function IconLink({ className, size = 18 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

export function IconChevron({ className, size = 16, open }: IconProps & { open?: boolean }) {
  const p = defaults(size);
  return (
    <svg
      {...p}
      className={className}
      style={{ transform: open ? "rotate(180deg)" : undefined, transition: "transform 0.2s" }}
      aria-hidden
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

export function IconSpark({ className, size = 20 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M12 3 9.5 9.5 3 12l6.5 2.5L12 21l2.5-6.5L21 12l-6.5-2.5L12 3z" />
    </svg>
  );
}

export function IconCheck({ className, size = 16 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function IconLoader({ className, size = 18 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={`icon-spin ${className ?? ""}`} aria-hidden>
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
    </svg>
  );
}

export function IconUser({ className, size = 16 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

export function IconBot({ className, size = 16 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M12 8V4H8" />
      <rect x="4" y="8" width="16" height="12" rx="2" />
      <path d="M2 14h2M20 14h2M9 13v2M15 13v2" />
    </svg>
  );
}

export function IconCopy({ className, size = 16 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

export function IconCheckCircle({ className, size = 16 }: IconProps) {
  const p = defaults(size);
  return (
    <svg {...p} className={className} aria-hidden>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="M22 4 12 14.01l-3-3" />
    </svg>
  );
}
