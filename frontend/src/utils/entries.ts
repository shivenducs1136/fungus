import type { ContextEntry } from '../types'

export function filterEntries(
  entries: ContextEntry[],
  queryFilter: string,
  jiraFilter: string,
): ContextEntry[] {
  const query = queryFilter.trim().toLowerCase()
  const jira = jiraFilter.trim().toLowerCase()

  return entries.filter((entry) => {
    const metadata = JSON.stringify(entry.metadata ?? {}).toLowerCase()
    const inQuery =
      !query ||
      entry.content.toLowerCase().includes(query) ||
      metadata.includes(query) ||
      entry.ticket_ids.some((ticket) => ticket.toLowerCase().includes(query))

    const inJira =
      !jira || entry.ticket_ids.some((ticket) => ticket.toLowerCase().includes(jira))

    return inQuery && inJira
  })
}

export function paginateEntries(entries: ContextEntry[], page: number, pageSize: number) {
  const safePageSize = Math.max(1, pageSize)
  const totalPages = Math.max(1, Math.ceil(entries.length / safePageSize))
  const safePage = Math.min(Math.max(1, page), totalPages)
  const start = (safePage - 1) * safePageSize

  return {
    pageItems: entries.slice(start, start + safePageSize),
    totalPages,
  }
}
