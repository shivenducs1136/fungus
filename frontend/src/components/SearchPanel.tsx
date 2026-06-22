import type { UseContextManagerResult } from '../hooks/useContextManager'

interface SearchPanelProps {
  manager: UseContextManagerResult
}

export function SearchPanel({ manager }: SearchPanelProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Find context</h2>
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
          </label>
        ) : (
          <label>
            Jira ID
            <input
              value={manager.jiraInput}
              onChange={(event) => manager.setJiraInput(event.target.value)}
              placeholder="PROJ-101"
            />
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
