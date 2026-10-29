import { useEffect, useState } from 'react'
import { PipelineForm } from './components/PipelineForm'
import { ProgressLog } from './components/ProgressLog'
import { ArtifactViewer } from './components/ArtifactViewer'
import { SessionsList } from './components/SessionsList'
import { RequirementsChecklist } from './components/RequirementsChecklist'
import { SessionDetail } from './components/SessionDetail'
import { streamPipeline } from './services/pipelineApi'
import { getSession } from './services/sessionApi'
import type { PipelineRequest, RequirementResult } from './types/api'
import './App.css'

type Page = 'home' | 'sessions' | 'session'
type State = 'idle' | 'streaming' | 'completed' | 'error'

// The orchestrator's first progress message names the session, so the saved results can be loaded
const SESSION_MESSAGE = /^🆔 Session ([0-9a-f-]{36})$/i
const SESSION_PATH = /^\/sessions\/([0-9a-f-]{36})\/?$/i

// The URL picks the page so session links can be bookmarked and the back button works
function routeFromPath(path: string): { page: Page; sessionId: string | null } {
  const match = SESSION_PATH.exec(path)
  if (match) return { page: 'session', sessionId: match[1] }
  if (/^\/sessions\/?$/.test(path)) return { page: 'sessions', sessionId: null }
  return { page: 'home', sessionId: null }
}

export function App() {
  const [route, setRoute] = useState(() => routeFromPath(window.location.pathname))
  const { page, sessionId: viewedSessionId } = route
  const [state, setState] = useState<State>('idle')
  const [messages, setMessages] = useState<string[]>([])
  const [artifacts, setArtifacts] = useState<Record<string, string>>({})
  const [requirements, setRequirements] = useState<RequirementResult[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  useEffect(() => {
    const onPopState = () => setRoute(routeFromPath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function navigate(path: string) {
    if (window.location.pathname !== path) window.history.pushState(null, '', path)
    setRoute(routeFromPath(path))
  }

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
          <button className="nav-btn" onClick={() => { handleReset(); navigate('/') }}>New Pipeline</button>
          <button className="nav-btn" onClick={() => navigate('/sessions')}>Past Sessions</button>
        </div>
      </nav>

      <main className="content">
        {page === 'session' && viewedSessionId ? (
          <>
            <h1>Session {viewedSessionId.slice(0, 8)}</h1>
            <SessionDetail sessionId={viewedSessionId} onBack={() => navigate('/sessions')} />
          </>
        ) : page === 'sessions' ? (
          <>
            <h1>Past Sessions</h1>
            <SessionsList onSelect={id => navigate(`/sessions/${id}`)} />
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
