import type { SessionRecord, SessionSummary } from '../types/api'

export async function listSessions(limit = 20): Promise<SessionSummary[]> {
  const response = await fetch(`/api/sessions?limit=${limit}`)
  if (!response.ok) throw new Error(`Failed to list sessions: ${response.status}`)
  return response.json()
}

export async function getSession(sessionId: string): Promise<SessionRecord | null> {
  const response = await fetch(`/api/sessions/${sessionId}`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`Failed to get session: ${response.status}`)
  return response.json()
}
