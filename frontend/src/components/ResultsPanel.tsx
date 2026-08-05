import type { ContextEntry } from '../types'
import type { UseContextManagerResult } from '../hooks/useContextManager'

interface ResultsPanelProps {
  manager: UseContextManagerResult
}

export function ResultsPanel({ manager }: ResultsPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Search Results</h2>
        </div>
        <p className="results-count">{manager.filteredEntries.length} matching entries</p>
      </div>

      <div className="filters-grid">
        <label>
          Text filter
          <input
            value={manager.queryFilter}
            onChange={(event) => manager.setQueryFilter(event.target.value)}
            placeholder="Filter by content or metadata"
          />
        </label>

        <label>
          Jira filter
          <input
            value={manager.jiraFilter}
            onChange={(event) => manager.setJiraFilter(event.target.value)}
            placeholder="Narrow by Jira ID"
          />
        </label>

        <label>
          Page size
          <select
            value={manager.pageSize}
            onChange={(event) => manager.setPageSize(Number(event.target.value))}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
          </select>
        </label>
      </div>

      {manager.error ? <p className="feedback error">{manager.error}</p> : null}
      {manager.statusMessage ? <p className="feedback ok">{manager.statusMessage}</p> : null}

      <div className="results-list">
        {manager.pageItems.map((entry) => (
          <EntryCard key={entry.entry_id} entry={entry} manager={manager} />
        ))}

        {!manager.pageItems.length ? (
          <div className="empty">
            <h3>No entries yet</h3>
            <p>Run a search, or create your first context entry from the left panel.</p>
          </div>
        ) : null}
      </div>

      <div className="pager">
        <button
          type="button"
          className="btn-secondary"
          onClick={() => manager.setPage((current) => Math.max(1, current - 1))}
          disabled={manager.page <= 1}
        >
          Previous
        </button>
        <p>
          Page {Math.min(manager.page, manager.totalPages)} / {manager.totalPages}
        </p>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => manager.setPage((current) => Math.min(manager.totalPages, current + 1))}
          disabled={manager.page >= manager.totalPages}
        >
          Next
        </button>
      </div>
    </section>
  )
}

interface EntryCardProps {
  entry: ContextEntry
  manager: UseContextManagerResult
}

const SECTION_TITLES = [
  'Problem',
  'Proposed direction',
  'Decision',
  'Alternatives considered',
  'Constraints',
  'Impact/risk',
  'Validation performed',
]

interface EntrySection {
  title: string
  paragraphs: string[]
}

function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function toParagraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
}

function parseEntrySections(content: string): EntrySection[] {
  const normalized = content.replace(/\r\n/g, '\n').trim()
  if (!normalized) {
    return []
  }

  const titlePattern = new RegExp(`\\b(${SECTION_TITLES.map(escapeRegex).join('|')})\\s*:`, 'gi')
  const marked = normalized.replace(titlePattern, (_match, title: string) => `\n\n@@SECTION@@${title}:`)

  const rawSections = marked
    .split('@@SECTION@@')
    .map((chunk) => chunk.trim())
    .filter(Boolean)

  const sections: EntrySection[] = []
  for (const rawSection of rawSections) {
    const separatorIndex = rawSection.indexOf(':')
    if (separatorIndex <= 0) {
      continue
    }

    const title = rawSection.slice(0, separatorIndex).trim()
    if (!SECTION_TITLES.includes(title)) {
      continue
    }

    const body = rawSection.slice(separatorIndex + 1).trim()
    if (!body) {
      continue
    }

    sections.push({
      title,
      paragraphs: toParagraphs(body),
    })
  }

  return sections
}

function FormattedEntryContent({ content }: { content: string }) {
  const sections = parseEntrySections(content)

  if (!sections.length) {
    return <p className="entry-content">{content}</p>
  }

  return (
    <div className="entry-content structured-content">
      {sections.map((section) => (
        <section key={section.title} className="entry-section">
          <h4>{section.title}</h4>
          {section.paragraphs.map((paragraph, index) => (
            <p key={`${section.title}-${index}`}>{paragraph}</p>
          ))}
        </section>
      ))}
    </div>
  )
}

function EntryCard({ entry, manager }: EntryCardProps) {
  const isEditing = manager.editingId === entry.entry_id
  const saveDisabled = Boolean(manager.editMetadataValidationError)

  return (
    <article className="entry-card">
      <div className="entry-header">
        <div>
          <p className="entry-key">{entry.derived_key}</p>
          <p className="entry-id">ID: {entry.entry_id}</p>
        </div>
        <div className="entry-actions">
          <button type="button" className="btn-secondary" onClick={() => manager.beginEdit(entry)}>
            Edit
          </button>
          <button type="button" className="danger" onClick={() => void manager.onDelete(entry)}>
            Delete
          </button>
        </div>
      </div>

      <p className="chips">{entry.ticket_ids.join(', ')}</p>

      {isEditing ? (
        <div className="edit-block">
          <label>
            Content
            <textarea
              rows={4}
              value={manager.editContent}
              onChange={(event) => manager.setEditContent(event.target.value)}
            />
          </label>
          <label>
            Metadata
            <textarea
              rows={4}
              value={manager.editMetadata}
              onChange={(event) => manager.setEditMetadata(event.target.value)}
              className={manager.editMetadataValidationError ? 'field-error' : ''}
            />
            {manager.editMetadataValidationError ? (
              <span className="inline-error" role="alert">
                {manager.editMetadataValidationError}
              </span>
            ) : (
              <span className="inline-success">Metadata JSON looks valid.</span>
            )}
          </label>
          <div className="entry-actions">
            <button type="button" onClick={() => void manager.onSaveEdit(entry)} disabled={saveDisabled}>
              {saveDisabled ? 'Fix JSON to save' : 'Save'}
            </button>
            <button type="button" className="btn-secondary" onClick={() => manager.setEditingId(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <FormattedEntryContent content={entry.content} />
          <pre>{JSON.stringify(entry.metadata ?? {}, null, 2)}</pre>
        </>
      )}

      <p className="entry-meta">Created: {new Date(entry.created_at).toLocaleString()}</p>
      {entry.updated_at ? (
        <p className="entry-meta">Updated: {new Date(entry.updated_at).toLocaleString()}</p>
      ) : null}
    </article>
  )
}
