import { useEffect } from 'react'
import type { FormEvent } from 'react'
import type { UseContextManagerResult } from '../hooks/useContextManager'

interface CreateEntryPanelProps {
  manager: UseContextManagerResult
}

export function CreateEntryPanel({ manager }: CreateEntryPanelProps) {
  useEffect(() => {
    if (!manager.createError && !manager.createStatusMessage) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      manager.clearCreateFeedback()
    }, 4000)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [manager.createError, manager.createStatusMessage])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void manager.onCreate()
  }

  const createDisabled = manager.loading || Boolean(manager.metadataValidationError)

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>2. Create Context Entry</h2>
          <p className="panel-subtitle">Document your reasoning so future decisions are easier.</p>
        </div>
      </div>
      <form className="create-form" onSubmit={handleSubmit}>
        <label>
          Jira IDs
          <input
            value={manager.ticketInput}
            onChange={(event) => manager.setTicketInput(event.target.value)}
            placeholder="PROJ-101, PROJ-202"
            required
          />
          <span className="help-text">Use comma-separated IDs such as ERP-24, ERP-31.</span>
        </label>

        <label>
          Content
          <textarea
            value={manager.contentInput}
            onChange={(event) => manager.setContentInput(event.target.value)}
            placeholder="Implementation rationale, constraints, alternatives"
            rows={5}
            required
          />
          <div className="hint-row" aria-label="Suggested writing structure">
            <span>Include:</span>
            <code className="inline-code">Problem</code>
            <code className="inline-code">Decision</code>
            <code className="inline-code">Impact</code>
          </div>
        </label>

        <label>
          Metadata (JSON object)
          <textarea
            value={manager.metadataInput}
            onChange={(event) => manager.setMetadataInput(event.target.value)}
            rows={4}
            className={manager.metadataValidationError ? 'field-error' : ''}
            aria-describedby="metadata-help"
          />
          <span className="help-text" id="metadata-help">
            Example: <code className="inline-code">{`{"source":"portal","service":"context-api"}`}</code>
          </span>
          {manager.metadataValidationError ? (
            <span className="inline-error" role="alert">
              {manager.metadataValidationError}
            </span>
          ) : (
            <span className="inline-success">Metadata JSON looks valid.</span>
          )}
        </label>

        <button type="submit" disabled={createDisabled}>
          {createDisabled ? 'Fix metadata JSON to continue' : 'Create'}
        </button>

        {manager.createError ? (
          <p className="feedback error" role="alert">
            {manager.createError}
          </p>
        ) : null}

        {manager.createStatusMessage ? (
          <p className="feedback ok" role="status">
            {manager.createStatusMessage}
          </p>
        ) : null}
      </form>
    </section>
  )
}
