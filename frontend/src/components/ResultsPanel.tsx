import type { ContextEntry } from '../types'
import type { UseContextManagerResult } from '../hooks/useContextManager'

interface ResultsPanelProps {
  manager: UseContextManagerResult
}

export function ResultsPanel({ manager }: ResultsPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Results</h2>
        <p>{manager.filteredEntries.length} matching entries</p>
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

        {!manager.pageItems.length ? <p className="empty">No entries to display.</p> : null}
      </div>

      <div className="pager">
        <button
          type="button"
          className="ghost"
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
          className="ghost"
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

function EntryCard({ entry, manager }: EntryCardProps) {
  const isEditing = manager.editingId === entry.entry_id

  return (
    <article className="entry-card">
      <div className="entry-header">
        <div>
          <p className="entry-key">{entry.derived_key}</p>
          <p className="entry-id">ID: {entry.entry_id}</p>
        </div>
        <div className="entry-actions">
          <button type="button" className="ghost" onClick={() => manager.beginEdit(entry)}>
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
            />
          </label>
          <div className="entry-actions">
            <button type="button" onClick={() => void manager.onSaveEdit(entry)}>
              Save
            </button>
            <button type="button" className="ghost" onClick={() => manager.setEditingId(null)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className="entry-content">{entry.content}</p>
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
