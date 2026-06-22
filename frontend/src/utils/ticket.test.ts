import { describe, expect, it } from 'vitest'
import { buildKeyFromTicketIds, parseTicketInput } from './ticket'

describe('parseTicketInput', () => {
  it('splits comma and whitespace separated jira IDs', () => {
    expect(parseTicketInput('proj-1, proj-2 PROJ-3')).toEqual(['PROJ-1', 'PROJ-2', 'PROJ-3'])
  })

  it('supports bracketed jira IDs', () => {
    expect(parseTicketInput('[ERP-24] [ERP-25]')).toEqual(['ERP-24', 'ERP-25'])
  })
})

describe('buildKeyFromTicketIds', () => {
  it('sorts and deduplicates jira IDs in generated key', () => {
    expect(buildKeyFromTicketIds(['PROJ-2', 'PROJ-1', 'PROJ-1'])).toBe('[PROJ-1][PROJ-2]')
  })

  it('normalizes already bracketed ticket IDs', () => {
    expect(buildKeyFromTicketIds(['[ERP-2]', '[ERP-1]'])).toBe('[ERP-1][ERP-2]')
  })

  it('returns empty string for no IDs', () => {
    expect(buildKeyFromTicketIds([])).toBe('')
  })
})
