import { useState } from 'react'
import { PipelineForm } from './components/PipelineForm'
import { ProgressLog } from './components/ProgressLog'
import { ArtifactViewer } from './components/ArtifactViewer'
import { SessionsList } from './components/SessionsList'
import { RequirementsChecklist } from './components/RequirementsChecklist'
import { streamPipeline } from './services/pipelineApi'
import { getSession } from './services/sessionApi'
import type { PipelineRequest, RequirementResult } from './types/api'
import './App.css'

type Page = 'home' | 'sessions'
type State = 'idle' | 'streaming' | 'completed' | 'error'

// The orchestrator's first progress message names the session, so the saved results can be loaded
const SESSION_MESSAGE = /^🆔 Session ([0-9a-f-]{36})$/i

export function App() {
  const [page, setPage] = useState<Page>('home')
  const [state, setState] = useState<State>('idle')
  const [messages, setMessages] = useState<string[]>([])
  const [artifacts, setArtifacts] = useState<Record<string, string>>({})
  const [requirements, setRequirements] = useState<RequirementResult[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  async function handleSubmit(request: PipelineRequest) {
    const controller = new AbortController()
    setAbortController(controller)
    setState('streaming')
    setMessages([])
    setArtifacts({})
    setRequirements([])
    setErrorMessage(null)

    try {
      let sessionId: string | null = null
      for await (const msg of streamPipeline(request, controller.signal)) {
        const match = SESSION_MESSAGE.exec(msg)
        if (match) sessionId = match[1]
        setMessages(prev => [...prev, msg])
      }
      setState('completed')
      if (sessionId) await loadResults(sessionId)
    } catch (e) {
      if (e instanceof Error && e.name === 'AbortError') {
        setState('idle')
      } else {
        setState('error')
        setErrorMessage(e instanceof Error ? e.message : 'Unknown error')
      }
    }
  }

  async function loadResults(sessionId: string) {
    try {
      const session = await getSession(sessionId)
      if (!session) return
      setArtifacts(session.artifacts ?? {})
      setRequirements(session.requirements ?? [])
    } catch {
      // The progress log already shows the outcome; the results panel is a convenience
    }
  }

  function handleReset() {
    abortController?.abort()
    setState('idle')
    setMessages([])
    setArtifacts({})
    setRequirements([])
    setErrorMessage(null)
    setAbortController(null)
  }

  return (
    <div className="page">
      <nav className="navbar">
        <span className="navbar-brand">🤖 MultiAgent Dev Team</span>
        <div className="nav-links">
          <button className="nav-btn" onClick={() => { handleReset(); setPage('home') }}>New Pipeline</button>
          <button className="nav-btn" onClick={() => setPage('sessions')}>Past Sessions</button>
        </div>
      </nav>

      <main className="content">
        {page === 'sessions' ? (
          <>
            <h1>Past Sessions</h1>
            <SessionsList />
          </>
        ) : (
          <>
            <h1>New Pipeline</h1>
            <p>Submit a plain-English requirement and the AI team will build a complete software package.</p>

            {state === 'idle' && (
              <PipelineForm onSubmit={handleSubmit} />
            )}

            {(state === 'streaming' || state === 'completed') && (
              <ProgressLog messages={messages} running={state === 'streaming'} />
            )}

            {state === 'completed' && (
              <>
                <RequirementsChecklist requirements={requirements} />
                <ArtifactViewer artifacts={artifacts} />
                <button className="btn btn-secondary" onClick={handleReset} data-testid="new-pipeline-btn">
                  Start New Pipeline
                </button>
              </>
            )}

            {state === 'error' && (
              <div>
                <div className="alert alert-danger" data-testid="error-message">
                  <strong>Pipeline failed:</strong> {errorMessage}
                </div>
                <button className="btn btn-secondary" onClick={handleReset} data-testid="try-again-btn">
                  Try Again
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
