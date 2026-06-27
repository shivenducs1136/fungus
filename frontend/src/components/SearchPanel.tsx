import type { UseContextManagerResult } from '../hooks/useContextManager'

interface SearchPanelProps {
  manager: UseContextManagerResult
}

export function SearchPanel({ manager }: SearchPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>1. Search Existing Context</h2>
          <p className="panel-subtitle">Start here to avoid duplicating decisions.</p>
        </div>
        <div className="mode-toggle" role="tablist" aria-label="Search mode">
          <button
            type="button"
            className={manager.searchMode === 'key' ? 'active' : ''}
            onClick={() => manager.setSearchMode('key')}
          >
            Jira combination
          </button>
          <button
            type="button"
            className={manager.searchMode === 'jira' ? 'active' : ''}
            onClick={() => manager.setSearchMode('jira')}
          >
            Single Jira
          </button>
        </div>
      </div>

      <div className="search-grid">
        {manager.searchMode === 'key' ? (
          <label>
            Jira IDs or key
            <input
              value={manager.keyInput}
              onChange={(event) => manager.setKeyInput(event.target.value)}
              placeholder="PROJ-101, PROJ-202 or [PROJ-101][PROJ-202]"
              list="known-keys"
            />
            <datalist id="known-keys">
              {manager.keys.map((key) => (
                <option key={key} value={key} />
              ))}
            </datalist>
            <span className="help-text">Use comma-separated IDs or a full key format.</span>
            <div className="hint-row" aria-label="Search examples">
              <span>Examples:</span>
              <code className="inline-code">ERP-24, ERP-31</code>
              <code className="inline-code">[ERP-24][ERP-31]</code>
            </div>
          </label>
        ) : (
          <label>
            Jira ID
            <input
              value={manager.jiraInput}
              onChange={(event) => manager.setJiraInput(event.target.value)}
              placeholder="PROJ-101"
            />
            <span className="help-text">Enter one Jira ticket ID, for example ERP-24.</span>
          </label>
        )}

        <div className="search-actions">
          <button type="button" onClick={() => void manager.onSearch()} disabled={manager.loading}>
            {manager.loading ? 'Searching...' : 'Search'}
          </button>
          <button type="button" className="ghost" onClick={manager.clearSearch}>
            Clear
          </button>
        </div>
      </div>
    </section>
  )
}
