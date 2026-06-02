"use client";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface StageProps {
  number: number;
  title: string;
  time: string;
  color: string;
  children: React.ReactNode;
}

function Stage({ number, title, time, color, children }: StageProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${color}`}>
          {number}
        </span>
        <div>
          <span className="text-sm font-semibold text-white">{title}</span>
          <span className="ml-2 text-xs text-gray-500">{time}</span>
        </div>
      </div>
      <div className="ml-8 space-y-1.5">{children}</div>
    </div>
  );
}

interface RowProps {
  section: string;
  what: string;
  rule?: string;
}

function Row({ section, what, rule }: RowProps) {
  return (
    <div className="text-xs leading-relaxed">
      <span className="text-indigo-300 font-medium">{section}</span>
      <span className="text-gray-400"> — {what}</span>
      {rule && <span className="block ml-0 mt-0.5 text-amber-500/80 italic">{rule}</span>}
    </div>
  );
}

function Divider() {
  return <div className="border-t border-gray-800 my-4" />;
}

export function HowToReadModal({ open, onClose }: Props) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/75 backdrop-blur-sm p-4 pt-10"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-gray-950 border border-gray-700 rounded-xl w-full max-w-2xl shadow-2xl mb-10">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div>
            <h2 className="text-base font-semibold text-white">How to read this analysis</h2>
            <p className="text-xs text-gray-500 mt-0.5">5-stage decision workflow · ~8 minutes total</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white transition-colors p-1"
            aria-label="Close"
          >
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5">

          <Stage number={1} title="Go / No-Go" time="30 seconds" color="bg-gray-700 text-gray-200">
            <Row
              section="Live Price Bar"
              what="Is the market open? What is the current price vs yesterday's close?"
            />
            <Row
              section="Agent Status"
              what="Are all agents green?"
              rule="2 or more agents failed → data is unreliable. Wait for a clean run before deciding."
            />
            <Row
              section="Earnings Countdown"
              what="How many days to the next earnings report?"
              rule="< 7 days → defined-risk options only, reduce size.  < 2 days → no new positions."
            />
          </Stage>

          <Divider />

          <Stage number={2} title="Stock or Options?" time="1–2 minutes" color="bg-blue-800 text-blue-200">
            <Row
              section="Verdict Card"
              what="The backend's primary call: stock / options / no_trade. Read the confidence note."
            />
            <Row
              section="Volatility → IV Rank"
              what="Where current implied vol sits in its 52-week range."
              rule="Cheap (< 40) → buying premium is relatively inexpensive.  Neutral (40–70) → let the trend decide.  Elevated (> 70) → sell premium via credit spreads."
            />
            <Row
              section="Volatility → Regime"
              what="IV vs realised HV ratio."
              rule="iv_rich → options income strategies favoured.  iv_neutral → directional bias wins.  iv_cheap → long premium or stock."
            />
            <Row
              section="Checklist"
              what="4 key conditions: trend clarity, earnings, options liquidity, vol regime."
              rule="All pass → clean setup.  Any fail → reduce position size by 50%."
            />
            <p className="text-xs text-amber-500/80 italic mt-1">
              Decision rule: If Verdict Card and Trade Guidance agree → act on it.
              If they disagree → the IV Rank resolves the tie (iv_rich overrides a bullish trend → use options/credit).
            </p>
          </Stage>

          <Divider />

          <Stage number={3} title="Confirm the Direction" time="2 minutes" color="bg-indigo-800 text-indigo-200">
            <Row
              section="Price Chart"
              what="Visually confirm the trend: higher highs / higher lows = bullish; the reverse = bearish."
            />
            <Row
              section="Trade Guidance → signal bar"
              what="Count of Stock vs Options direction indicators."
              rule="≥ 60% signals on one side = conviction.  Below 60% = wait for confirmation."
            />
            <p className="text-xs text-gray-400 mt-1">Priority order for direction signals:</p>
            <ol className="text-xs text-gray-400 list-decimal list-inside space-y-0.5 ml-1">
              <li><span className="text-gray-300">Trend hint</span> (SMA 20 vs SMA 50) — highest weight</li>
              <li><span className="text-gray-300">RSI 14</span> — above 55 = bullish momentum; below 45 = weakening</li>
              <li><span className="text-gray-300">OBV 20d Trend</span> — rising = accumulation backing the move</li>
              <li><span className="text-gray-300">MACD histogram</span> — positive and expanding = momentum confirmed</li>
              <li><span className="text-gray-300">Sector ETF alignment</span> — stock + sector same direction = stronger conviction</li>
            </ol>
            <Row
              section="Sentiment Card"
              what="News flow direction from FinBERT NLP model."
              rule="News contradicting your technical thesis → wait one session before entering."
            />
          </Stage>

          <Divider />

          <Stage number={4} title="Entry, Size &amp; Exit" time="2 minutes" color="bg-green-800 text-green-200">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">For a stock position</p>
            <Row
              section="Entry / Exit Card → Entry Zone"
              what="Price band near SMA 20 where risk/reward is best."
              rule="Extended above entry zone warning → wait for a pullback to SMA 20 or reduce size."
            />
            <Row
              section="Entry / Exit Card → R:R"
              what="Reward-to-risk ratio vs Target 1."
              rule="≥ 2:1 Favorable = full size.  1–2:1 Acceptable = half size.  < 1:1 = skip the trade."
            />
            <Row
              section="Entry / Exit Card → Stop Loss"
              what="Maximum acceptable loss level (2× ATR or SMA 50 break)."
            />
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mt-2">For an options position</p>
            <Row
              section="Trade Guidance → Options Play Card"
              what="Specific strategy (Long Call / Credit Put Spread / Iron Condor), strikes in dollars, and target DTE window."
            />
            <Row
              section="Options Metrics Table → 30% / 60% rules"
              what="Take profit targets: close at 30% of max credit for quick wins; 60% for standard exits."
            />
            <Row
              section="Position Sizing"
              what="Risk budget as % of portfolio → maximum share count or contract count."
            />
          </Stage>

          <Divider />

          <Stage number={5} title="Valuation Sanity Check" time="1 minute (swing trades only)" color="bg-amber-800 text-amber-200">
            <p className="text-xs text-gray-500 italic">Skip for intraday scalps. Required for holds longer than 1 week.</p>
            <Row
              section="Fundamentals → Forward P/E vs Trailing P/E"
              what="Forward P/E below Trailing P/E → analysts expect earnings to grow (positive). Forward P/E above 35× → stock is priced for perfection; any miss = sharp gap."
            />
            <Row
              section="Peer Comparison Table"
              what="Is this stock the sector leader or the laggard?"
              rule="Leading peers = stronger thesis.  Lagging = ask why before buying the dip."
            />
          </Stage>

          <Divider />

          {/* Quick reference */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-2">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Quick reference</p>
            <pre className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap font-mono">
{`STAGE 1  Earnings < 7d?  Agents all green?
         ↓ yes to both
STAGE 2  Verdict + IV Rank → Stock or Options?
         ↓ decided
STAGE 3  ≥60% signals same direction? Checklist all pass?
         ↓ yes
STAGE 4  Stock  → EntryExitCard R:R ≥1:1 → size from Position Sizing
         Options → Options Play Card + Metrics Table max loss
         ↓
STAGE 5  (swing only) P/E reasonable? Sector leader?
         ↓
         ENTER`}
            </pre>
          </div>

          <p className="text-xs text-amber-700 italic">
            All analysis is for informational purposes only and is not investment advice. Verify all levels at your broker before executing.
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-800 flex justify-end">
          <button
            onClick={onClose}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700 px-4 py-1.5 rounded-md transition-colors"
          >
            Got it
          </button>
        </div>

      </div>
    </div>
  );
}
