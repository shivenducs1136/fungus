import { useState } from 'react'
import '../App.css'
import { CreateEntryPanel } from '../components/CreateEntryPanel'
import { ResultsPanel } from '../components/ResultsPanel'
import { SearchPanel } from '../components/SearchPanel'
import { useContextManager } from '../hooks/useContextManager'
import { Header } from '../components/Header'

export const DashboardPage = () => {
  const manager = useContextManager()
  const [activeTab, setActiveTab] = useState<'search' | 'create'>('search')

  return (
    <>
      <Header />
      <main className="page">
        <section className="workspace">
          <div className="tabs">
            <button 
              className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              Search Existing Context
            </button>
            <button 
              className={`tab-btn ${activeTab === 'create' ? 'active' : ''}`}
              onClick={() => setActiveTab('create')}
            >
              Create Context Entry
            </button>
          </div>

          {activeTab === 'search' && (
            <>
              <SearchPanel manager={manager} />
              <ResultsPanel manager={manager} />
            </>
          )}

          {activeTab === 'create' && (
            <CreateEntryPanel manager={manager} />
          )}
        </section>
      </main>
    </>
  )
}
