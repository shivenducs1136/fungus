import { useState } from 'react'
import { createDemoBooking } from '../api/contextApi'
import type { BookDemoResponse } from '../types'
import { CalendarScheduler } from './CalendarScheduler'
import type { SelectedSlot } from './CalendarScheduler'

import './BookDemoModal.css'

interface BookDemoModalProps {
  isOpen: boolean
  onClose: () => void
}

export const BookDemoModal = ({ isOpen, onClose }: BookDemoModalProps) => {
  const [name, setName] = useState('')
  const [workEmail, setWorkEmail] = useState('')
  const [contactNumber, setContactNumber] = useState('')
  const [shortNote, setShortNote] = useState('')
  const [selectedSlot, setSelectedSlot] = useState<SelectedSlot | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [bookingSuccess, setBookingSuccess] = useState<BookDemoResponse | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Basic Validation
    if (!name.trim()) {
      setError('Please provide your full name.')
      return
    }

    if (!workEmail.trim() || !workEmail.includes('@')) {
      setError('Please provide a valid work email address.')
      return
    }

    const cleanedContact = contactNumber.trim().replace(/\s+/g, '')
    if (!cleanedContact.startsWith('+')) {
      setError('Contact number must include country code (e.g. +14155552671).')
      return
    }

    if (!selectedSlot) {
      setError('Please select an available time slot from the calendar schedule.')
      return
    }

    setLoading(true)

    try {
      const response = await createDemoBooking({
        name: name.trim(),
        work_email: workEmail.trim(),
        contact_number: cleanedContact,
        time: selectedSlot.timeDisplay,
        scheduled_datetime: selectedSlot.scheduled_datetime,
        short_note: shortNote.trim() || undefined,
      })

      setBookingSuccess(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo booking failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setName('')
    setWorkEmail('')
    setContactNumber('')
    setShortNote('')
    setSelectedSlot(null)
    setError('')
    setBookingSuccess(null)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={handleReset}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Book a Demo</div>
          <button type="button" className="modal-close-btn" onClick={handleReset} title="Close">
            ✕
          </button>
        </div>

        <div className="modal-body">
          {bookingSuccess ? (
            <div className="form-success-card">
              <div className="success-icon">✦</div>
              <h3 className="success-title">Demo Scheduled</h3>
              <p style={{ fontSize: '14px', color: 'var(--ink-soft)' }}>
                Thank you, <strong>{bookingSuccess.name}</strong>! Your demo request has been recorded.
              </p>

              <div className="success-details">
                <div>
                  <strong>Booking ID:</strong> {bookingSuccess.booking_id}
                </div>
                <div>
                  <strong>Scheduled Slot:</strong> {selectedSlot?.dateDisplay} ({bookingSuccess.time})
                </div>
                <div>
                  <strong>Confirmation Sent To:</strong> {bookingSuccess.work_email} (Status:{' '}
                  {bookingSuccess.email_status})
                </div>
              </div>

              <button type="button" className="btn" onClick={handleReset} style={{ marginTop: '12px' }}>
                Close Window
              </button>
            </div>
          ) : (
            <>
              <p className="modal-subtitle">
                Schedule a 30-minute interactive walkthrough of Fungus MCP with our team. Pick an available
                time slot below.
              </p>

              {error && <div className="form-error-banner">{error}</div>}

              <form onSubmit={handleSubmit} className="demo-form">
                <div className="form-group">
                  <label className="form-label">
                    Full Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Ada Lovelace"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Work Email <span className="required">*</span>
                  </label>
                  <input
                    type="email"
                    className="form-input"
                    placeholder="ada@company.com"
                    value={workEmail}
                    onChange={(e) => setWorkEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Contact Number (With Country Code) <span className="required">*</span>
                  </label>
                  <input
                    type="tel"
                    className="form-input"
                    placeholder="+14155552671"
                    value={contactNumber}
                    onChange={(e) => setContactNumber(e.target.value)}
                    required
                  />
                  <span className="form-hint">Format: +[CountryCode][Number] (e.g. +14155552671 or +919876543210)</span>
                </div>

                {/* Calendar Scheduler */}
                <div className="form-group">
                  <label className="form-label">
                    Select Availability (Mon–Fri, 9am – 6pm) <span className="required">*</span>
                  </label>
                  <CalendarScheduler
                    onSelectSlot={(slot) => setSelectedSlot(slot)}
                    selectedSlot={selectedSlot}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Short Note (Optional)</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    placeholder="Tell us about your team size, repository stack, or specific questions..."
                    value={shortNote}
                    onChange={(e) => setShortNote(e.target.value)}
                  />
                </div>

                <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button type="button" className="btn" onClick={handleReset} style={{ background: 'transparent' }}>
                    Cancel
                  </button>
                  <button type="submit" className="btn" disabled={loading} style={{ background: 'var(--ink)', color: 'var(--paper)' }}>
                    {loading ? 'Scheduling...' : 'Confirm Demo Booking'}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
