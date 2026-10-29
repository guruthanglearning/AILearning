import { useEffect, useState } from 'react'
import type { SessionRecord } from '../types/api'
import { getSession } from '../services/sessionApi'
import { RequirementsChecklist } from './RequirementsChecklist'
import { ArtifactViewer } from './ArtifactViewer'
import { ProgressLog } from './ProgressLog'

interface Props {
  sessionId: string
  onBack: () => void
}

export function SessionDetail({ sessionId, onBack }: Props) {
  const [session, setSession] = useState<SessionRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getSession(sessionId)
      .then(s => s ? setSession(s) : setError(`Session ${sessionId} was not found.`))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [sessionId])

  const back = <button className="btn btn-secondary" onClick={onBack} data-testid="back-btn">← Back to sessions</button>

  if (loading) return <p data-testid="loading">Loading session...</p>
  if (error || !session) return <div><p className="error" data-testid="session-error">{error}</p>{back}</div>

  return (
    <div data-testid="session-detail">
      <p><strong>Requirement:</strong> {session.requirement}</p>
      <p>
        <span className={`badge ${session.success ? 'badge-success' : 'badge-danger'}`}>
          {session.success ? '✅ Success' : '❌ Failed'}
        </span>
        <span className="hint"> {session.totalDuration} · started {new Date(session.startedAt).toLocaleString()}</span>
      </p>
      {session.errorMessage && <div className="alert alert-danger">{session.errorMessage}</div>}
      <RequirementsChecklist requirements={session.requirements ?? []} />
      <ArtifactViewer artifacts={session.artifacts ?? {}} />
      {/* Collapsed so the log's auto-scroll doesn't jump past the checklist */}
      {session.agentLog?.length > 0 && (
        <details className="agent-log">
          <summary>Agent log ({session.agentLog.length} messages)</summary>
          <ProgressLog messages={session.agentLog} running={false} />
        </details>
      )}
      {back}
    </div>
  )
}
