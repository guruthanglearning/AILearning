interface Props {
  artifacts: Record<string, string>
}

export function ArtifactViewer({ artifacts }: Props) {
  const entries = Object.entries(artifacts)

  if (entries.length === 0) return null

  return (
    <div className="artifacts" data-testid="artifacts-section">
      <h2>Generated Artifacts ({entries.length})</h2>
      {entries.map(([name, content]) => (
        <details key={name} data-testid="artifact-item">
          <summary>📄 {name}</summary>
          <pre>{content}</pre>
        </details>
      ))}
    </div>
  )
}
