interface ScoreMeterProps {
  score: number; // -1.0 to +1.0
}

export function ScoreMeter({ score }: ScoreMeterProps) {
  const clamped = Math.max(-1, Math.min(1, score));
  // Convert [-1,1] to [0,100] percent for the fill
  const pct = ((clamped + 1) / 2) * 100;
  const fillColor =
    clamped < -0.2 ? "bg-blue-500" : clamped > 0.2 ? "bg-green-500" : "bg-gray-500";

  return (
    <div className="flex items-center gap-2 text-xs text-gray-400 w-full">
      <span className="shrink-0 text-blue-400">Options</span>
      <div className="relative flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        {/* Center marker */}
        <div className="absolute left-1/2 top-0 h-full w-px bg-gray-500" />
        {/* Fill bar from center to score */}
        {clamped >= 0 ? (
          <div
            className={`absolute top-0 h-full ${fillColor}`}
            style={{ left: "50%", width: `${pct - 50}%` }}
          />
        ) : (
          <div
            className={`absolute top-0 h-full ${fillColor}`}
            style={{ left: `${pct}%`, width: `${50 - pct}%` }}
          />
        )}
      </div>
      <span className="shrink-0 text-green-400">Stock</span>
      <span className="shrink-0 text-gray-300 font-mono ml-1">
        {clamped > 0 ? "+" : ""}
        {clamped.toFixed(2)}
      </span>
    </div>
  );
}
