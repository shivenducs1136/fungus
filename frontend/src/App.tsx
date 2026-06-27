import './App.css'
import { CreateEntryPanel } from './components/CreateEntryPanel'
import { ResultsPanel } from './components/ResultsPanel'
import { SearchPanel } from './components/SearchPanel'
import { useContextManager } from './hooks/useContextManager'

function App() {
  const manager = useContextManager()

  function fillSearchByCombination() {
    manager.setSearchMode('key')
    manager.setKeyInput('ERP-24, ERP-31')
  }

  function fillSearchByTicket() {
    manager.setSearchMode('jira')
    manager.setJiraInput('ERP-24')
  }

  function fillCreateTemplate() {
    manager.setTicketInput('ERP-24')
    manager.setContentInput(
      'Problem: Needed deterministic retrieval of architecture context.\nDecision: Use Jira-key-based context storage and retrieval.\nConstraints: Keep logic simple and avoid embeddings.',
    )
    manager.setMetadataInput('{"source":"portal","author":"team"}')
  }

  return (
    <main className="page">
      <header className="hero">
        <div className="hero-main">
          <p className="eyebrow">Fungus Context Portal</p>
          <h1>Understand why code exists, then capture what changed</h1>
          <p>
            Search historical context by Jira, review results, and save new implementation reasoning with
            friendly JSON guidance.
          </p>

          <div className="hero-stats">
            <article>
              <strong>{manager.keys.length}</strong>
              <span>Known combinations</span>
            </article>
            <article>
              <strong>{manager.filteredEntries.length}</strong>
              <span>Current results</span>
            </article>
            <article>
              <strong>{manager.loading ? 'Searching' : 'Ready'}</strong>
              <span>Workspace status</span>
            </article>
          </div>
        </div>

        <aside className="hero-guide">
          <h2>Quick Start</h2>
          <p>New here? Use a starter action, then click Search or Create.</p>
          <div className="quick-actions">
            <button type="button" className="ghost" onClick={fillSearchByCombination}>
              Sample Jira combination
            </button>
            <button type="button" className="ghost" onClick={fillSearchByTicket}>
              Sample single Jira
            </button>
            <button type="button" className="ghost" onClick={fillCreateTemplate}>
              Fill create template
            </button>
          </div>
        </aside>
      </header>

      <section className="workspace">
        <div className="workspace-top">
          <SearchPanel manager={manager} />
          <CreateEntryPanel manager={manager} />
        </div>
        <div className="workspace-results">
          <ResultsPanel manager={manager} />
        </div>
      </section>
    </main>
  )
}

export default App
