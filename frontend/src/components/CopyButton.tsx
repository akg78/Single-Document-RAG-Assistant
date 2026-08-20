import { IconCheckCircle, IconCopy } from "@/components/Icons";

type Props = {
  text: string;
  copyId: string;
  copiedId: string | null;
  onCopy: (text: string, id: string) => void;
  variant?: "button" | "icon";
  className?: string;
  label?: string;
};

export function CopyButton({
  text,
  copyId,
  copiedId,
  onCopy,
  variant = "button",
  className = "",
  label = "Copy",
}: Props) {
  const copied = copiedId === copyId;
  const iconSize = variant === "icon" ? 14 : 16;

  if (variant === "icon") {
    return (
      <button
        type="button"
        className={`source-card__copy ${className}`.trim()}
        onClick={() => void onCopy(text, copyId)}
        aria-label={copied ? "Copied" : label}
      >
        {copied ? <IconCheckCircle size={iconSize} /> : <IconCopy size={iconSize} />}
      </button>
    );
  }

  return (
    <button
      type="button"
      className={`btn btn--ghost btn--sm ${copied ? "is-success" : ""} ${className}`.trim()}
      onClick={() => void onCopy(text, copyId)}
    >
      {copied ? <IconCheckCircle size={iconSize} /> : <IconCopy size={iconSize} />}
      {copied ? "Copied" : label}
    </button>
  );
}
