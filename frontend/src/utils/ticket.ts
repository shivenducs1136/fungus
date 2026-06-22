export function parseTicketInput(input: string): string[] {
  return input
    .split(/[,\s]+/)
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => token.replace(/^\[|\]$/g, ''))
    .map((token) => token.toUpperCase())
}

export function buildKeyFromTicketIds(ticketIds: string[]): string {
  const normalize = (id: string) => id.trim().replace(/^\[(.*)\]$/, '$1').trim().toUpperCase()
  const unique = Array.from(new Set(ticketIds.map(normalize).filter(Boolean)))
  const sorted = unique.sort((a, b) => a.localeCompare(b))

  return sorted.map((id) => `[${id}]`).join('')
}
