export interface PipelineRequest {
  requirement: string
  skipAgents: string[]
  maxReviewLoops: number
}

export interface PipelineResponse {
  success: boolean
  sessionId: string
  artifacts: Record<string, string>
  agentLog: string[]
  totalDuration: string
  errorMessage?: string
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
}
