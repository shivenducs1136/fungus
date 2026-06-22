import type {
  ContextEntry,
  CreateContextRequest,
  ListKeysResponse,
  UpdateContextRequest,
} from '../types'
import { buildKeyFromTicketIds } from '../utils/ticket'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.toString() ?? 'http://127.0.0.1:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const fallback = `Request failed with status ${response.status}`
    let message = fallback

    try {
      const errorData = (await response.json()) as { detail?: string; message?: string }
      message = errorData.detail ?? errorData.message ?? fallback
    } catch {
      message = fallback
    }

    throw new Error(message)
  }

  return (await response.json()) as T
}

function withDerivedKey(entries: ContextEntry[]): ContextEntry[] {
  return entries.map((entry) => ({
    ...entry,
    derived_key: buildKeyFromTicketIds(entry.ticket_ids),
  }))
}

export function fetchKeys(): Promise<ListKeysResponse> {
  return request<ListKeysResponse>('/api/v1/context/')
}

export async function fetchContextEntriesByJira(jiraId: string): Promise<ContextEntry[]> {
  if (!jiraId) {
    throw new Error('Jira ID is required')
  }

  const entries = await request<ContextEntry[]>(`/api/v1/context/jira/${encodeURIComponent(jiraId)}`)
  return withDerivedKey(entries)
}

export async function fetchContextEntriesByKey(key: string): Promise<ContextEntry[]> {
  if (!key) {
    throw new Error('Key is required')
  }

  const entries = await request<ContextEntry[]>(`/api/v1/context/${encodeURIComponent(key)}`)
  return withDerivedKey(entries)
}

export function createContextEntry(payload: CreateContextRequest): Promise<{
  status: string
  key: string
  entry_id: string
  timestamp: string
}> {
  return request('/api/v1/context/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateContextEntry(
  key: string,
  entryId: string,
  payload: UpdateContextRequest,
): Promise<ContextEntry> {
  const entry = await request<ContextEntry>(`/api/v1/context/${encodeURIComponent(key)}/${encodeURIComponent(entryId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })

  return {
    ...entry,
    derived_key: key,
  }
}

export function deleteContextEntry(
  key: string,
  entryId: string,
): Promise<{ status: string; key: string; entry_id: string }> {
  return request(`/api/v1/context/${encodeURIComponent(key)}/${encodeURIComponent(entryId)}`, {
    method: 'DELETE',
  })
}
