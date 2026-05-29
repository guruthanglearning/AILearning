import type { SupervisorVerdict } from "@/types/api";

const SIGNAL_STYLE: Record<string, { bg: string; text: string; dot: string }> = {
  Bullish:  { bg: "bg-green-900/30",  text: "text-green-400",  dot: "bg-green-400" },
  Bearish:  { bg: "bg-red-900/30",    text: "text-red-400",    dot: "bg-red-400" },
  Neutral:  { bg: "bg-gray-800/60",   text: "text-gray-400",   dot: "bg-gray-400" },
};

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(((score + 1) / 2) * 100);
  const color = score > 0.15 ? "bg-green-500" : score < -0.15 ? "bg-red-500" : "bg-amber-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-gray-500">
        <span>Bearish −1</span>
        <span className="font-mono text-gray-300">{score >= 0 ? "+" : ""}{score.toFixed(3)}</span>
        <span>Bullish +1</span>
      </div>
      <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function SentimentCard({ verdict }: { verdict: SupervisorVerdict }) {
  const { sentiment_score, sentiment_forecast, sentiment_headlines } = verdict;
  if (sentiment_score == null && !sentiment_forecast) return null;

  const signal = sentiment_forecast ?? "Neutral";
  const style  = SIGNAL_STYLE[signal] ?? SIGNAL_STYLE.Neutral;

  return (
    <div className="space-y-2">
      <h2 className="text-sm font-medium text-gray-400">Market Sentiment</h2>
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-4">

        {/* Signal badge + score */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border border-transparent ${style.bg}`}>
            <span className={`w-2 h-2 rounded-full ${style.dot}`} />
            <span className={`text-sm font-bold ${style.text}`}>{signal}</span>
          </div>
          {sentiment_score != null && (
            <span className="text-xs text-gray-500">
              Sentiment score: <span className="font-mono text-gray-200">{sentiment_score >= 0 ? "+" : ""}{sentiment_score.toFixed(3)}</span>
            </span>
          )}
        </div>

        {/* Score bar */}
        {sentiment_score != null && <ScoreBar score={sentiment_score} />}

        {/* Headlines */}
        {sentiment_headlines.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Top headlines driving sentiment</p>
            <ul className="space-y-2">
              {sentiment_headlines.map((h, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-300 leading-relaxed">
                  <span className={`shrink-0 mt-0.5 font-bold ${style.text}`}>{i + 1}.</span>
                  {h}
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs text-amber-700 italic">Sentiment derived from recent news headlines via NLP model. Not investment advice.</p>
      </div>
    </div>
  );
}
