import { FormEvent, useState } from 'react'
import type { PipelineRequest } from '../types/api'

interface Props {
  onSubmit: (request: PipelineRequest) => void
  disabled?: boolean
}

export function PipelineForm({ onSubmit, disabled = false }: Props) {
  const [requirement, setRequirement] = useState('')
  const [skipAgents, setSkipAgents] = useState('')
  const [maxReviewLoops, setMaxReviewLoops] = useState(3)
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!requirement.trim()) {
      setError('Requirement is required.')
      return
    }
    if (requirement.trim().length < 10) {
      setError('Requirement must be at least 10 characters.')
      return
    }
    setError(null)
    const parsedSkipAgents = skipAgents
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
    onSubmit({ requirement: requirement.trim(), skipAgents: parsedSkipAgents, maxReviewLoops })
  }

  return (
    <form onSubmit={handleSubmit} data-testid="pipeline-form">
      <div className="form-group">
        <label htmlFor="requirement">
          Requirement <span className="required">*</span>
        </label>
        <textarea
          id="requirement"
          data-testid="requirement-input"
          rows={6}
          className="form-control"
          placeholder="e.g. Build a REST API for managing a TODO list with JWT authentication..."
          value={requirement}
          onChange={e => setRequirement(e.target.value)}
          disabled={disabled}
        />
        {error && <span className="validation-error" data-testid="validation-error">{error}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="skipAgents">
          Skip Agents <span className="hint">(optional, comma-separated)</span>
        </label>
        <input
          id="skipAgents"
          data-testid="skip-agents-input"
          type="text"
          className="form-control"
          placeholder="e.g. devops,docs"
          value={skipAgents}
          onChange={e => setSkipAgents(e.target.value)}
          disabled={disabled}
        />
        <small className="hint">Available: pm, architect, developer, reviewer, qa, security, devops, docs</small>
      </div>

      <div className="form-group">
        <label htmlFor="maxLoops">Max Review Loops</label>
        <input
          id="maxLoops"
          data-testid="max-loops-input"
          type="number"
          className="form-control"
          min={1}
          max={10}
          value={maxReviewLoops}
          onChange={e => setMaxReviewLoops(Number(e.target.value))}
          disabled={disabled}
        />
      </div>

      <button
        type="submit"
        className="btn btn-primary"
        data-testid="submit-btn"
        disabled={disabled}
      >
        Submit to AI Team
      </button>
    </form>
  )
}
