import { useEffect, useMemo, useState } from 'react'
import {
  createContextEntry,
  deleteContextEntry,
  fetchContextEntriesByJira,
  fetchContextEntriesByKey,
  fetchKeys,
  updateContextEntry,
} from '../api/contextApi'
import type { ContextEntry, SearchMode } from '../types'
import { filterEntries, paginateEntries } from '../utils/entries'
import { buildKeyFromTicketIds, parseTicketInput } from '../utils/ticket'

export interface UseContextManagerResult {
  searchMode: SearchMode
  setSearchMode: (mode: SearchMode) => void
  keyInput: string
  setKeyInput: (value: string) => void
  jiraInput: string
  setJiraInput: (value: string) => void
  keys: string[]
  entries: ContextEntry[]
  loading: boolean
  error: string
  statusMessage: string

  ticketInput: string
  setTicketInput: (value: string) => void
  contentInput: string
  setContentInput: (value: string) => void
  metadataInput: string
  setMetadataInput: (value: string) => void

  queryFilter: string
  setQueryFilter: (value: string) => void
  jiraFilter: string
  setJiraFilter: (value: string) => void
  page: number
  setPage: (value: number | ((current: number) => number)) => void
  pageSize: number
  setPageSize: (value: number) => void

  editingId: string | null
  setEditingId: (value: string | null) => void
  editContent: string
  setEditContent: (value: string) => void
  editMetadata: string
  setEditMetadata: (value: string) => void

  filteredEntries: ContextEntry[]
  pageItems: ContextEntry[]
  totalPages: number

  onSearch: () => Promise<void>
  onCreate: () => Promise<void>
  beginEdit: (entry: ContextEntry) => void
  onSaveEdit: (entry: ContextEntry) => Promise<void>
  onDelete: (entry: ContextEntry) => Promise<void>
  clearSearch: () => void
}

export function useContextManager(): UseContextManagerResult {
  const [searchMode, setSearchMode] = useState<SearchMode>('key')
  const [keyInput, setKeyInput] = useState('')
  const [jiraInput, setJiraInput] = useState('')
  const [keys, setKeys] = useState<string[]>([])
  const [entries, setEntries] = useState<ContextEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  const [ticketInput, setTicketInput] = useState('')
  const [contentInput, setContentInput] = useState('')
  const [metadataInput, setMetadataInput] = useState('{"source":"portal"}')

  const [queryFilter, setQueryFilter] = useState('')
  const [jiraFilter, setJiraFilter] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editMetadata, setEditMetadata] = useState('{}')

  const filteredEntries = useMemo(
    () => filterEntries(entries, queryFilter, jiraFilter),
    [entries, jiraFilter, queryFilter],
  )

  const { pageItems, totalPages } = useMemo(
    () => paginateEntries(filteredEntries, page, pageSize),
    [filteredEntries, page, pageSize],
  )

  useEffect(() => {
    void loadKeys()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [queryFilter, jiraFilter, pageSize])

  async function loadKeys() {
    try {
      const response = await fetchKeys()
      setKeys(response.keys)
    } catch {
      setError('Unable to load known Jira combinations.')
    }
  }

  function toMetadataObject(value: string): Record<string, unknown> | undefined {
    const trimmed = value.trim()
    if (!trimmed) {
      return undefined
    }

    const parsed = JSON.parse(trimmed)
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('Metadata must be a JSON object')
    }

    return parsed as Record<string, unknown>
  }

  function resolveKey(input: string): string {
    const trimmed = input.trim()
    if (!trimmed) {
      throw new Error('Enter Jira IDs or a full key to search.')
    }

    if (trimmed.includes('[') && trimmed.includes(']')) {
      return trimmed
    }

    const ids = parseTicketInput(trimmed)
    if (!ids.length) {
      throw new Error('No valid Jira IDs found in search input.')
    }

    return buildKeyFromTicketIds(ids)
  }

  async function onSearch() {
    setLoading(true)
    setError('')
    setStatusMessage('')

    try {
      let data: ContextEntry[] = []

      if (searchMode === 'jira') {
        data = await fetchContextEntriesByJira(jiraInput.trim())
      } else {
        const key = resolveKey(keyInput)
        data = await fetchContextEntriesByKey(key)
      }

      setEntries(data)
      setPage(1)
      setStatusMessage(`Loaded ${data.length} entr${data.length === 1 ? 'y' : 'ies'}.`)
    } catch (searchError) {
      setEntries([])
      setError(searchError instanceof Error ? searchError.message : 'Search failed.')
    } finally {
      setLoading(false)
    }
  }

  async function onCreate() {
    setError('')
    setStatusMessage('')

    try {
      const ticketIds = parseTicketInput(ticketInput)
      if (!ticketIds.length) {
        throw new Error('Provide at least one Jira ID.')
      }

      await createContextEntry({
        ticket_ids: ticketIds,
        content: contentInput,
        metadata: toMetadataObject(metadataInput),
      })

      setTicketInput('')
      setContentInput('')
      setMetadataInput('{"source":"portal"}')
      setStatusMessage('Entry created successfully.')
      await loadKeys()
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Create failed.')
    }
  }

  function beginEdit(entry: ContextEntry) {
    setEditingId(entry.entry_id)
    setEditContent(entry.content)
    setEditMetadata(JSON.stringify(entry.metadata ?? {}, null, 2))
  }

  async function onSaveEdit(entry: ContextEntry) {
    setError('')
    setStatusMessage('')

    try {
      const metadata = toMetadataObject(editMetadata)
      const updated = await updateContextEntry(entry.derived_key, entry.entry_id, {
        content: editContent,
        metadata,
      })

      setEntries((current) =>
        current.map((item) =>
          item.entry_id === updated.entry_id ? { ...updated, derived_key: entry.derived_key } : item,
        ),
      )

      setEditingId(null)
      setStatusMessage('Entry updated.')
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : 'Update failed.')
    }
  }

  async function onDelete(entry: ContextEntry) {
    setError('')
    setStatusMessage('')

    try {
      await deleteContextEntry(entry.derived_key, entry.entry_id)
      setEntries((current) => current.filter((item) => item.entry_id !== entry.entry_id))
      setStatusMessage('Entry deleted.')
      await loadKeys()
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : 'Delete failed.')
    }
  }

  function clearSearch() {
    setEntries([])
    setError('')
    setStatusMessage('Search cleared.')
  }

  return {
    searchMode,
    setSearchMode,
    keyInput,
    setKeyInput,
    jiraInput,
    setJiraInput,
    keys,
    entries,
    loading,
    error,
    statusMessage,
    ticketInput,
    setTicketInput,
    contentInput,
    setContentInput,
    metadataInput,
    setMetadataInput,
    queryFilter,
    setQueryFilter,
    jiraFilter,
    setJiraFilter,
    page,
    setPage,
    pageSize,
    setPageSize,
    editingId,
    setEditingId,
    editContent,
    setEditContent,
    editMetadata,
    setEditMetadata,
    filteredEntries,
    pageItems,
    totalPages,
    onSearch,
    onCreate,
    beginEdit,
    onSaveEdit,
    onDelete,
    clearSearch,
  }
}
