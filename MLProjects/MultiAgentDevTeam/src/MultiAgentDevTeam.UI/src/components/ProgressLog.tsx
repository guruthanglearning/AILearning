import { useEffect, useRef } from 'react'

interface Props {
  messages: string[]
  running: boolean
}

export function ProgressLog({ messages, running }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="progress-log" data-testid="progress-log">
      {messages.map((msg, i) => (
        <div key={i} className="log-entry" data-testid="log-entry">
          {msg}
        </div>
      ))}
      {running && (
        <div className="spinner" data-testid="spinner">
          ⏳ Pipeline running...
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
