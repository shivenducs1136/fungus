import './App.css'
import { CreateEntryPanel } from './components/CreateEntryPanel'
import { ResultsPanel } from './components/ResultsPanel'
import { SearchPanel } from './components/SearchPanel'
import { useContextManager } from './hooks/useContextManager'

function App() {
  const manager = useContextManager()

  return (
    <main className="page">
      <header className="hero">
        <p className="eyebrow">Fungus Context Portal</p>
        <h1>Search and manage Jira-linked architecture context</h1>
        <p>
          Supports key-combination and single Jira search with full create, update, and delete flows.
        </p>
      </header>

      <SearchPanel manager={manager} />
      <CreateEntryPanel manager={manager} />
      <ResultsPanel manager={manager} />
    </main>
  )
}

export default App
