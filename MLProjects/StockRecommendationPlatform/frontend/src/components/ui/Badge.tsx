import { clsx } from "clsx";

type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral";
type BadgeSize = "sm" | "md";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: "bg-green-900 text-green-300 border-green-700",
  warning: "bg-amber-900 text-amber-300 border-amber-700",
  error: "bg-red-900 text-red-300 border-red-700",
  info: "bg-blue-900 text-blue-300 border-blue-700",
  neutral: "bg-gray-800 text-gray-300 border-gray-700",
};

const SIZE_CLASSES: Record<BadgeSize, string> = {
  sm: "text-xs px-1.5 py-0.5",
  md: "text-sm px-2 py-1",
};

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export function Badge({
  variant = "neutral",
  size = "sm",
  children,
  className,
  title,
}: BadgeProps) {
  return (
    <span
      title={title}
      className={clsx(
        "inline-flex items-center rounded border font-medium",
        VARIANT_CLASSES[variant],
        SIZE_CLASSES[size],
        className
      )}
    >
      {children}
    </span>
  );
}
