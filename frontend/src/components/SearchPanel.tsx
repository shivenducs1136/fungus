import type { UseContextManagerResult } from '../hooks/useContextManager'

interface SearchPanelProps {
  manager: UseContextManagerResult
}

export function SearchPanel({ manager }: SearchPanelProps) {
  const isKeyMode = manager.searchMode === 'key';

  return (
    <div className="big-search-container">
      <div className="mode-toggle" role="tablist" aria-label="Search mode" style={{ marginBottom: '10px' }}>
        <button
          type="button"
          className={isKeyMode ? 'active' : ''}
          onClick={() => manager.setSearchMode('key')}
        >
          Jira combination
        </button>
        <button
          type="button"
          className={!isKeyMode ? 'active' : ''}
          onClick={() => manager.setSearchMode('jira')}
        >
          Single Jira
        </button>
      </div>

      <div className="search-input-wrapper">
        <input
          value={isKeyMode ? manager.keyInput : manager.jiraInput}
          onChange={(event) => isKeyMode ? manager.setKeyInput(event.target.value) : manager.setJiraInput(event.target.value)}
          placeholder={isKeyMode ? "PROJ-101, PROJ-202 or [PROJ-101][PROJ-202]" : "Enter a single Jira ID (e.g. PROJ-101)"}
          list={isKeyMode ? "known-keys" : undefined}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              void manager.onSearch();
            }
          }}
        />
        {isKeyMode && (
          <datalist id="known-keys">
            {manager.keys.map((key) => (
              <option key={key} value={key} />
            ))}
          </datalist>
        )}
        <button 
          className="search-btn-big" 
          onClick={() => void manager.onSearch()} 
          disabled={manager.loading}
        >
          {manager.loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      
      <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
        <div className="hint-row">
          {isKeyMode ? (
            <>
              <span className="help-text">Examples:</span>
              <code className="inline-code">ERP-24, ERP-31</code>
              <code className="inline-code">[ERP-24][ERP-31]</code>
            </>
          ) : (
            <span className="help-text">Enter one Jira ticket ID, for example ERP-24.</span>
          )}
        </div>
        <button type="button" className="tab-btn" style={{ padding: '4px 8px', fontSize: '11px', borderBottom: 'none' }} onClick={manager.clearSearch}>
          Clear Input
        </button>
      </div>
    </div>
  )
}
