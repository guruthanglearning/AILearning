import type { RequirementResult, RequirementStatus } from '../types/api'

interface Props {
  requirements: RequirementResult[]
}

const ICONS: Record<RequirementStatus, string> = {
  Passed: '✅',
  Failed: '❌',
  Manual: '🖐️',
  Unverified: '❔'
}

const ORDER: RequirementStatus[] = ['Passed', 'Failed', 'Manual', 'Unverified']

export function RequirementsChecklist({ requirements }: Props) {
  if (requirements.length === 0) return null

  const summary = ORDER
    .map(status => ({ status, count: requirements.filter(r => r.status === status).length }))
    .filter(x => x.count > 0)
    .map(x => `${x.count} ${x.status.toLowerCase()}`)
    .join(', ')

  return (
    <div className="requirements" data-testid="requirements-section">
      <h2>Requirement Checklist</h2>
      <p className="requirements-summary" data-testid="requirements-summary">{summary}</p>
      <table className="sessions-table">
        <thead>
          <tr>
            <th>Status</th>
            <th>ID</th>
            <th>Requirement</th>
            <th>Kind</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {requirements.map(r => (
            <tr key={r.id} data-testid="requirement-row">
              <td className={`req-status req-${r.status.toLowerCase()}`}>{ICONS[r.status]} {r.status}</td>
              <td className="req-id">{r.id}</td>
              <td>{r.text}</td>
              <td>{r.kind.toLowerCase()}</td>
              <td>
                {r.evidence}
                {r.coveredBy.length > 0 && <div className="hint">Covered by {r.coveredBy.join(', ')}</div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
