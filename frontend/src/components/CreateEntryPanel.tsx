import type { FormEvent } from 'react'
import type { UseContextManagerResult } from '../hooks/useContextManager'

interface CreateEntryPanelProps {
  manager: UseContextManagerResult
}

export function CreateEntryPanel({ manager }: CreateEntryPanelProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void manager.onCreate()
  }

  return (
    <section className="panel">
      <h2>Create entry</h2>
      <form className="create-form" onSubmit={handleSubmit}>
        <label>
          Jira IDs
          <input
            value={manager.ticketInput}
            onChange={(event) => manager.setTicketInput(event.target.value)}
            placeholder="PROJ-101, PROJ-202"
            required
          />
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
        </label>

        <label>
          Metadata (JSON object)
          <textarea
            value={manager.metadataInput}
            onChange={(event) => manager.setMetadataInput(event.target.value)}
            rows={4}
          />
        </label>

        <button type="submit">Create</button>
      </form>
    </section>
  )
}
