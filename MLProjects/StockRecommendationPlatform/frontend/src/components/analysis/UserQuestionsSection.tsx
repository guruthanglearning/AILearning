export function UserQuestionsSection({ questions }: { questions: string[] }) {
  if (!questions.length) return null;
  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-400 font-medium">
        Before sizing a position, consider:
      </p>
      <ol className="space-y-2">
        {questions.map((q, i) => (
          <li
            key={i}
            className="flex gap-3 border-l-2 border-amber-700 pl-3 text-sm text-gray-300"
          >
            <span className="text-amber-500 font-bold shrink-0">{i + 1}.</span>
            {q}
          </li>
        ))}
      </ol>
    </div>
  );
}
