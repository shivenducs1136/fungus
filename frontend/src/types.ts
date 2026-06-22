export type SearchMode = 'key' | 'jira'

export interface ContextEntry {
  entry_id: string
  ticket_ids: string[]
  content: string
  metadata: Record<string, unknown>
  created_at: string
  updated_at?: string
  derived_key: string
}

export interface ListKeysResponse {
  keys: string[]
}

export interface CreateContextRequest {
  ticket_ids: string[]
  content: string
  metadata?: Record<string, unknown>
}

export interface UpdateContextRequest {
  content: string
  metadata?: Record<string, unknown>
}
