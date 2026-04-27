import type { PipelineRequest } from '../types/api'

export async function* streamPipeline(
  request: PipelineRequest,
  signal?: AbortSignal
): AsyncGenerator<string> {
  const response = await fetch('/api/run/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed.startsWith('data:')) continue
        const json = trimmed.slice('data:'.length).trim()
        if (!json) continue
        try {
          const parsed = JSON.parse(json)
          if (typeof parsed.message === 'string') yield parsed.message
        } catch {
          // skip malformed lines
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
