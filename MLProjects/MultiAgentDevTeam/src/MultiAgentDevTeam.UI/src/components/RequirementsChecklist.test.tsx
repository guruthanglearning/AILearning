import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RequirementsChecklist } from './RequirementsChecklist'
import type { RequirementResult } from '../types/api'

const requirements: RequirementResult[] = [
  { id: 'FR-1', text: 'Print Hello, World!', kind: 'Code', status: 'Passed', coveredBy: ['Developer'], evidence: 'Program.cs', source: 'Product Manager' },
  { id: 'FR-2', text: 'Create it under D:\\Temp', kind: 'Action', status: 'Manual', coveredBy: [], source: 'Product Manager' },
  { id: 'MISSED-1', text: 'Use .NET 10', kind: 'Code', status: 'Failed', coveredBy: [], evidence: 'targets net8.0', source: 'Acceptance Verifier' }
]

describe('RequirementsChecklist', () => {
  it('renders nothing when there are no requirements', () => {
    const { container } = render(<RequirementsChecklist requirements={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders one row per requirement', () => {
    render(<RequirementsChecklist requirements={requirements} />)
    expect(screen.getAllByTestId('requirement-row')).toHaveLength(3)
  })

  it('summarises the statuses', () => {
    render(<RequirementsChecklist requirements={requirements} />)
    expect(screen.getByTestId('requirements-summary')).toHaveTextContent('1 passed, 1 failed, 1 manual')
  })

  it('shows status, evidence and who covered it', () => {
    render(<RequirementsChecklist requirements={requirements} />)
    const [first, , last] = screen.getAllByTestId('requirement-row')
    expect(first).toHaveTextContent('✅ Passed')
    expect(first).toHaveTextContent('Covered by Developer')
    expect(last).toHaveTextContent('❌ Failed')
    expect(last).toHaveTextContent('targets net8.0')
  })
})
