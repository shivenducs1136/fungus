import { describe, expect, it } from 'vitest'
import type { ContextEntry } from '../types'
import { filterEntries, paginateEntries } from './entries'

const entries: ContextEntry[] = [
  {
    entry_id: 'a',
    ticket_ids: ['ERP-1'],
    content: 'Store context hash in commit message',
    metadata: { source: 'chat' },
    created_at: '2026-01-01T00:00:00Z',
    derived_key: '[ERP-1]',
  },
  {
    entry_id: 'b',
    ticket_ids: ['ERP-1', 'ERP-2'],
    content: 'Use deterministic key strategy',
    metadata: { owner: 'platform' },
    created_at: '2026-01-02T00:00:00Z',
    derived_key: '[ERP-1][ERP-2]',
  },
  {
    entry_id: 'c',
    ticket_ids: ['ERP-3'],
    content: 'Fallback when metadata missing',
    metadata: {},
    created_at: '2026-01-03T00:00:00Z',
    derived_key: '[ERP-3]',
  },
]

describe('filterEntries', () => {
  it('filters by free-text query against content and metadata', () => {
    expect(filterEntries(entries, 'deterministic', '')).toHaveLength(1)
    expect(filterEntries(entries, 'platform', '')).toHaveLength(1)
  })

  it('filters by jira ID', () => {
    expect(filterEntries(entries, '', 'ERP-1')).toHaveLength(2)
  })

  it('combines query and jira filter', () => {
    const result = filterEntries(entries, 'key strategy', 'ERP-2')
    expect(result).toHaveLength(1)
    expect(result[0].entry_id).toBe('b')
  })
})

describe('paginateEntries', () => {
  it('returns requested page and total pages', () => {
    const { pageItems, totalPages } = paginateEntries(entries, 2, 2)
    expect(totalPages).toBe(2)
    expect(pageItems).toHaveLength(1)
    expect(pageItems[0].entry_id).toBe('c')
  })

  it('clamps invalid page values', () => {
    const { pageItems } = paginateEntries(entries, 99, 2)
    expect(pageItems[0].entry_id).toBe('c')
  })
})
