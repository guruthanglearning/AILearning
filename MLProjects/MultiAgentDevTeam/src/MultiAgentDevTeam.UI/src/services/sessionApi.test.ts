import { describe, it, expect, vi, beforeEach } from 'vitest'
import { listSessions, getSession } from './sessionApi'

describe('listSessions', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('returns session list', async () => {
    const data = [{ sessionId: '1', requirement: 'Build API', success: true, artifactCount: 3 }]
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(data), { status: 200 }))
    const result = await listSessions()
    expect(result).toHaveLength(1)
    expect(result[0].requirement).toBe('Build API')
  })

  it('throws on non-OK response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 500 }))
    await expect(listSessions()).rejects.toThrow('Failed to list sessions')
  })

  it('passes limit param', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('[]', { status: 200 }))
    await listSessions(5)
    expect(fetchSpy.mock.calls[0][0]).toContain('limit=5')
  })
})

describe('getSession', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('returns session record', async () => {
    const data = { sessionId: 'abc', requirement: 'Build TODO', success: true }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(data), { status: 200 }))
    const result = await getSession('abc')
    expect(result).not.toBeNull()
    expect(result!.sessionId).toBe('abc')
  })

  it('returns null on 404', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 404 }))
    const result = await getSession('nonexistent')
    expect(result).toBeNull()
  })

  it('throws on server error', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('', { status: 500 }))
    await expect(getSession('abc')).rejects.toThrow('Failed to get session')
  })
})
