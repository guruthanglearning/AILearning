import { describe, it, expect, vi, beforeEach } from 'vitest'
import { streamPipeline } from './pipelineApi'

function makeSseResponse(messages: string[]): Response {
  const body = messages
    .map(m => `data: {"message": "${m.replace(/"/g, '\\"')}"}\n\n`)
    .join('')
  return new Response(body, {
    status: 200,
    headers: { 'Content-Type': 'text/event-stream' }
  })
}

describe('streamPipeline', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('yields messages from SSE stream', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      makeSseResponse(['🤖 PM started', '✅ PM done', '🤖 Architect started'])
    )
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toEqual(['🤖 PM started', '✅ PM done', '🤖 Architect started'])
  })

  it('throws on non-OK response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response('error', { status: 400, statusText: 'Bad Request' })
    )
    const gen = streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })
    await expect(gen.next()).rejects.toThrow('API error: 400')
  })

  it('skips non-data lines', async () => {
    const body = ': keep-alive\n\ndata: {"message": "hello"}\n\n: comment\n\ndata: {"message": "world"}\n\n'
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
    )
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toEqual(['hello', 'world'])
  })

  it('skips malformed JSON lines', async () => {
    const body = 'data: {"message": "valid"}\n\ndata: NOT_JSON\n\ndata: {"message": "also valid"}\n\n'
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
    )
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toEqual(['valid', 'also valid'])
  })

  it('skips events without message field', async () => {
    const body = 'data: {"other": "field"}\n\ndata: {"message": "valid"}\n\n'
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
    )
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toEqual(['valid'])
  })

  it('returns empty for empty stream', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(makeSseResponse([]))
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toHaveLength(0)
  })

  it('throws when response body is null', async () => {
    const resp = new Response('', { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
    Object.defineProperty(resp, 'body', { get: () => null })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(resp)
    const gen = streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })
    await expect(gen.next()).rejects.toThrow('No response body')
  })

  it('skips empty data lines', async () => {
    const body = 'data: {"message": "first"}\n\ndata: \n\ndata: {"message": "second"}\n\n'
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
    )
    const results: string[] = []
    for await (const msg of streamPipeline({ requirement: 'test', skipAgents: [], maxReviewLoops: 3 })) {
      results.push(msg)
    }
    expect(results).toEqual(['first', 'second'])
  })

  it('sends correct request body', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(makeSseResponse([]))
    for await (const _ of streamPipeline({ requirement: 'Build something', skipAgents: ['devops'], maxReviewLoops: 2 })) { }
    const [, init] = fetchSpy.mock.calls[0]
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body.requirement).toBe('Build something')
    expect(body.skipAgents).toEqual(['devops'])
    expect(body.maxReviewLoops).toBe(2)
  })
})
