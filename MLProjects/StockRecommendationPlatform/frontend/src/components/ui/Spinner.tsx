const SIZE_CLASSES = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" };

export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  return (
    <div
      className={`${SIZE_CLASSES[size]} animate-spin rounded-full border-2 border-gray-600 border-t-indigo-400`}
      role="status"
      aria-label="Loading"
    />
  );
}
