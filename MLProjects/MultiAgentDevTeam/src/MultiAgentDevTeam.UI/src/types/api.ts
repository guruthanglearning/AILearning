export interface PipelineRequest {
  requirement: string
  skipAgents: string[]
  maxReviewLoops: number
}

export type RequirementKind = 'Code' | 'Test' | 'Action'
export type RequirementStatus = 'Passed' | 'Failed' | 'Manual' | 'Unverified'

export interface RequirementResult {
  id: string
  text: string
  kind: RequirementKind
  status: RequirementStatus
  coveredBy: string[]
  evidence?: string
  source: string
}

export interface PipelineResponse {
  success: boolean
  sessionId: string
  artifacts: Record<string, string>
  agentLog: string[]
  totalDuration: string
  errorMessage?: string
  requirements?: RequirementResult[]
}

export interface SessionSummary {
  sessionId: string
  requirement: string
  startedAt: string
  completedAt?: string
  success: boolean
  totalDuration: string
  artifactCount: number
}

export interface SessionRecord {
  sessionId: string
  requirement: string
  startedAt: string
  completedAt?: string
  success: boolean
  artifacts: Record<string, string>
  agentLog: string[]
  totalDuration: string
  errorMessage?: string
  requirements?: RequirementResult[]
}
