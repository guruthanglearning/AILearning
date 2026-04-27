import { useEffect, useState } from 'react'
import type { SessionSummary } from '../types/api'
import { listSessions } from '../services/sessionApi'

export function SessionsList() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p data-testid="loading">Loading sessions...</p>
  if (error) return <p className="error" data-testid="sessions-error">{error}</p>
  if (sessions.length === 0) return <p data-testid="no-sessions">No sessions found. <a href="/">Start your first pipeline!</a></p>

  return (
    <table className="sessions-table" data-testid="sessions-table">
      <thead>
        <tr>
          <th>Session ID</th>
          <th>Requirement</th>
          <th>Status</th>
          <th>Artifacts</th>
          <th>Duration</th>
          <th>Started</th>
        </tr>
      </thead>
      <tbody>
        {sessions.map(s => (
          <tr key={s.sessionId} data-testid="session-row">
            <td><a href={`/sessions/${s.sessionId}`}>{s.sessionId.slice(0, 8)}…</a></td>
            <td>{s.requirement}</td>
            <td>
              <span className={`badge ${s.success ? 'badge-success' : 'badge-danger'}`}>
                {s.success ? '✅ Success' : '❌ Failed'}
              </span>
            </td>
            <td>{s.artifactCount}</td>
            <td>{s.totalDuration}</td>
            <td>{new Date(s.startedAt).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
