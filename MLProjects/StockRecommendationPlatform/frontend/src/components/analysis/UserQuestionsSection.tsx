export function UserQuestionsSection({
  questions,
  answers = [],
}: {
  questions: string[];
  answers?: string[];
}) {
  if (!questions.length) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-400 font-medium">
        Before sizing a position, consider:
      </p>
      <ol className="space-y-4">
        {questions.map((q, i) => (
          <li key={i} className="border-l-2 border-amber-700 pl-3 space-y-1">
            <div className="flex gap-3 text-sm text-gray-300">
              <span className="text-amber-500 font-bold shrink-0">{i + 1}.</span>
              <span>{q}</span>
            </div>
            {answers[i] && (
              <div className="flex gap-3 text-xs text-gray-400 pl-5">
                <span className="text-blue-400 shrink-0">→</span>
                <span>{answers[i]}</span>
              </div>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
