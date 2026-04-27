import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProgressLog } from './ProgressLog'

describe('ProgressLog', () => {
  it('renders all messages', () => {
    render(<ProgressLog messages={['🤖 PM started', '✅ PM done']} running={false} />)
    const entries = screen.getAllByTestId('log-entry')
    expect(entries).toHaveLength(2)
    expect(entries[0]).toHaveTextContent('🤖 PM started')
  })

  it('shows spinner when running', () => {
    render(<ProgressLog messages={[]} running={true} />)
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
  })

  it('hides spinner when not running', () => {
    render(<ProgressLog messages={[]} running={false} />)
    expect(screen.queryByTestId('spinner')).not.toBeInTheDocument()
  })

  it('renders empty state with no messages', () => {
    render(<ProgressLog messages={[]} running={false} />)
    expect(screen.queryAllByTestId('log-entry')).toHaveLength(0)
  })
})
