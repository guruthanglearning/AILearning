import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PipelineForm } from './PipelineForm'

describe('PipelineForm', () => {
  it('renders requirement textarea', () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    expect(screen.getByTestId('requirement-input')).toBeInTheDocument()
  })

  it('renders skip agents input', () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    expect(screen.getByTestId('skip-agents-input')).toBeInTheDocument()
  })

  it('renders max loops input', () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    expect(screen.getByTestId('max-loops-input')).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    expect(screen.getByTestId('submit-btn')).toBeInTheDocument()
  })

  it('shows error when requirement is empty', async () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    expect(screen.getByTestId('validation-error')).toHaveTextContent('Requirement is required')
  })

  it('shows error when requirement is too short', async () => {
    render(<PipelineForm onSubmit={vi.fn()} />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'short')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    expect(screen.getByTestId('validation-error')).toHaveTextContent('at least 10 characters')
  })

  it('calls onSubmit with correct data on valid submit', async () => {
    const onSubmit = vi.fn()
    render(<PipelineForm onSubmit={onSubmit} />)
    await userEvent.type(screen.getByTestId('requirement-input'), 'Build a TODO REST API with authentication')
    await userEvent.clear(screen.getByTestId('skip-agents-input'))
    await userEvent.type(screen.getByTestId('skip-agents-input'), 'devops,docs')
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    expect(onSubmit).toHaveBeenCalledWith({
      requirement: 'Build a TODO REST API with authentication',
      skipAgents: ['devops', 'docs'],
      maxReviewLoops: 3
    })
  })

  it('disables inputs when disabled prop is true', () => {
    render(<PipelineForm onSubmit={vi.fn()} disabled />)
    expect(screen.getByTestId('requirement-input')).toBeDisabled()
    expect(screen.getByTestId('submit-btn')).toBeDisabled()
  })

  it('does not call onSubmit when form is invalid', () => {
    const onSubmit = vi.fn()
    render(<PipelineForm onSubmit={onSubmit} />)
    fireEvent.submit(screen.getByTestId('pipeline-form'))
    expect(onSubmit).not.toHaveBeenCalled()
  })
})
