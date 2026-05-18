export function StaleWarning({ message }: { message: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-amber-400 text-xs">
      <span>⚠</span>
      <span>{message}</span>
    </span>
  );
}
