import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ArtifactViewer } from './ArtifactViewer'

describe('ArtifactViewer', () => {
  it('renders nothing when artifacts is empty', () => {
    const { container } = render(<ArtifactViewer artifacts={{}} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders artifact items', () => {
    render(<ArtifactViewer artifacts={{ Requirements: '# Reqs', SourceCode: 'public class Foo {}' }} />)
    const items = screen.getAllByTestId('artifact-item')
    expect(items).toHaveLength(2)
  })

  it('renders artifact names in summaries', () => {
    render(<ArtifactViewer artifacts={{ Requirements: '# content' }} />)
    expect(screen.getByText(/Requirements/)).toBeInTheDocument()
  })

  it('shows correct artifact count in heading', () => {
    render(<ArtifactViewer artifacts={{ A: '1', B: '2', C: '3' }} />)
    expect(screen.getByRole('heading', { name: /Generated Artifacts \(3\)/ })).toBeInTheDocument()
  })
})
