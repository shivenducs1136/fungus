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
  createError: string
  createStatusMessage: string

  ticketInput: string
  setTicketInput: (value: string) => void
  contentInput: string
  setContentInput: (value: string) => void
  metadataInput: string
  setMetadataInput: (value: string) => void
  metadataValidationError: string

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
  editMetadataValidationError: string

  filteredEntries: ContextEntry[]
  pageItems: ContextEntry[]
  totalPages: number

  onSearch: () => Promise<void>
  onCreate: () => Promise<void>
  clearCreateFeedback: () => void
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
  const [createError, setCreateError] = useState('')
  const [createStatusMessage, setCreateStatusMessage] = useState('')

  const [ticketInput, setTicketInput] = useState('')
  const [contentInput, setContentInput] = useState('')
  const [metadataInput, setMetadataInputState] = useState('{"source":"portal"}')
  const [metadataValidationError, setMetadataValidationError] = useState('')

  const [queryFilter, setQueryFilter] = useState('')
  const [jiraFilter, setJiraFilter] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editMetadata, setEditMetadataState] = useState('{}')
  const [editMetadataValidationError, setEditMetadataValidationError] = useState('')

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
    } catch (err) {
      console.warn('Unable to load known Jira combinations.', err)
    }
  }

  function parseJsonSyntaxError(error: unknown): string {
    const fallback = 'Invalid JSON. Check quotes, commas, and braces.'
    if (!(error instanceof SyntaxError)) {
      return fallback
    }

    const message = error.message
    const tokenMatch = message.match(/position\s+(\d+)/i)
    if (tokenMatch) {
      return `Invalid JSON near character ${tokenMatch[1]}. Check quotes, commas, and braces.`
    }

    return fallback
  }

  function toMetadataObject(value: string): Record<string, unknown> | undefined {
    const trimmed = value.trim()
    if (!trimmed) {
      return undefined
    }

    let parsed: unknown
    try {
      parsed = JSON.parse(trimmed)
    } catch (error) {
      throw new Error(parseJsonSyntaxError(error))
    }

    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
      throw new Error('Metadata must be a JSON object, for example {"source": "portal"}.')
    }

    return parsed as Record<string, unknown>
  }

  function validateMetadataInput(value: string): string {
    try {
      void toMetadataObject(value)
      return ''
    } catch (error) {
      return error instanceof Error ? error.message : 'Metadata is invalid.'
    }
  }

  function handleMetadataInputChange(value: string) {
    setMetadataInputState(value)
    setMetadataValidationError(validateMetadataInput(value))
  }

  function handleEditMetadataChange(value: string) {
    setEditMetadataState(value)
    setEditMetadataValidationError(validateMetadataInput(value))
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
    setCreateError('')
    setCreateStatusMessage('')
    setError('')
    setStatusMessage('')

    try {
      const metadataError = validateMetadataInput(metadataInput)
      if (metadataError) {
        throw new Error(metadataError)
      }

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
      setMetadataInputState('{"source":"portal"}')
      setMetadataValidationError('')
      setCreateStatusMessage('Entry created successfully.')
      setStatusMessage('Entry created successfully.')
      await loadKeys()
    } catch (createError) {
      const message = createError instanceof Error ? createError.message : 'Create failed.'
      setCreateError(message)
      setError(message)
    }
  }

  function clearCreateFeedback() {
    setCreateError('')
    setCreateStatusMessage('')
  }

  function beginEdit(entry: ContextEntry) {
    setEditingId(entry.entry_id)
    setEditContent(entry.content)
    const nextMetadata = JSON.stringify(entry.metadata ?? {}, null, 2)
    setEditMetadataState(nextMetadata)
    setEditMetadataValidationError(validateMetadataInput(nextMetadata))
  }

  async function onSaveEdit(entry: ContextEntry) {
    setError('')
    setStatusMessage('')

    try {
      const metadataError = validateMetadataInput(editMetadata)
      if (metadataError) {
        throw new Error(metadataError)
      }

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
        setEditMetadataValidationError('')
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
    createError,
    createStatusMessage,
    ticketInput,
    setTicketInput,
    contentInput,
    setContentInput,
    metadataInput,
    metadataValidationError,
    setMetadataInput: handleMetadataInputChange,
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
    setEditMetadata: handleEditMetadataChange,
    editMetadataValidationError,
    filteredEntries,
    pageItems,
    totalPages,
    onSearch,
    onCreate,
    clearCreateFeedback,
    beginEdit,
    onSaveEdit,
    onDelete,
    clearSearch,
  }
}
