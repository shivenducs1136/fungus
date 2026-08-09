import { useState, useMemo } from 'react'

export interface SelectedSlot {
  scheduled_datetime: string // ISO 8601 string
  timeDisplay: string        // e.g. "10:00 AM - 10:30 AM"
  dateDisplay: string        // e.g. "Mon, Aug 10"
}

interface CalendarSchedulerProps {
  onSelectSlot: (slot: SelectedSlot) => void
  selectedSlot?: SelectedSlot | null
}

interface DayOption {
  date: Date
  dayName: string
  dateLabel: string
  isoDateStr: string
  isToday: boolean
  isPast: boolean
}

interface TimeSlot {
  index: number
  hour: number
  minute: number
  label: string
}

// Get Monday-Friday options for a specific week offset
function getWeekdays(weekOffset: number): DayOption[] {
  const days: DayOption[] = []
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // Find Monday of the target week
  const currentDay = new Date()
  const dayOfWeek = currentDay.getDay() // 0=Sun, 1=Mon, ..., 6=Sat
  
  // Calculate difference to Monday
  // If today is Sunday (0), next day (tomorrow) is Monday (1 day away)
  // If today is Monday (1), 0 days away
  // If today is Saturday (6), Monday was 5 days ago, or next week Monday is +2 days
  let diffToMon = dayOfWeek === 0 ? 1 : 1 - dayOfWeek
  if (dayOfWeek === 6) diffToMon = 2 // Skip weekend to next Monday for base week 0

  const baseMonday = new Date(currentDay)
  baseMonday.setDate(currentDay.getDate() + diffToMon + weekOffset * 7)
  baseMonday.setHours(0, 0, 0, 0)

  for (let i = 0; i < 5; i++) {
    const d = new Date(baseMonday)
    d.setDate(baseMonday.getDate() + i)

    const dayName = d.toLocaleDateString('en-US', { weekday: 'short' })
    const dateLabel = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const dayNum = String(d.getDate()).padStart(2, '0')
    const isoDateStr = `${year}-${month}-${dayNum}`

    const isToday = d.getTime() === today.getTime()
    const isPast = d.getTime() < today.getTime()

    days.push({
      date: d,
      dayName,
      dateLabel,
      isoDateStr,
      isToday,
      isPast,
    })
  }

  return days
}

// Generate slots from 09:00 to 17:30 (ending at 18:00)
function generateTimeSlots(): TimeSlot[] {
  const slots: TimeSlot[] = []
  let index = 0
  for (let h = 9; h < 18; h++) {
    for (let m of [0, 30]) {
      const displayHour = h % 12 === 0 ? 12 : h % 12
      const ampm = h >= 12 ? 'PM' : 'AM'
      const minuteStr = m === 0 ? '00' : '30'
      slots.push({
        index,
        hour: h,
        minute: m,
        label: `${displayHour}:${minuteStr} ${ampm}`,
      })
      index++
    }
  }
  return slots
}

export const CalendarScheduler = ({ onSelectSlot, selectedSlot }: CalendarSchedulerProps) => {
  const [weekOffset, setWeekOffset] = useState<number>(0)
  const weekdays = useMemo(() => getWeekdays(weekOffset), [weekOffset])
  const timeSlots = useMemo(() => generateTimeSlots(), [])

  // Find first valid (non-past) day or default to first tab
  const defaultDateStr = useMemo(() => {
    const validDay = weekdays.find((d) => !d.isPast)
    return validDay ? validDay.isoDateStr : weekdays[0]?.isoDateStr ?? ''
  }, [weekdays])

  const [activeDateStr, setActiveDateStr] = useState<string>(defaultDateStr)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStartIdx, setDragStartIdx] = useState<number | null>(null)
  const [dragEndIdx, setDragEndIdx] = useState<number | null>(null)

  // Ensure active day stays synced when switching weeks
  const activeDay = weekdays.find((d) => d.isoDateStr === activeDateStr) || weekdays.find((d) => !d.isPast) || weekdays[0]

  // Month & Year header label (e.g. "August 2026" or "Aug – Sep 2026")
  const monthYearLabel = useMemo(() => {
    if (!weekdays.length) return ''
    const start = weekdays[0].date
    const end = weekdays[weekdays.length - 1].date
    const startMonth = start.toLocaleDateString('en-US', { month: 'long' })
    const endMonth = end.toLocaleDateString('en-US', { month: 'long' })
    const startYear = start.getFullYear()
    const endYear = end.getFullYear()

    if (startMonth === endMonth) {
      return `${startMonth} ${startYear}`
    } else if (startYear === endYear) {
      return `${start.toLocaleDateString('en-US', { month: 'short' })} – ${end.toLocaleDateString('en-US', { month: 'short' })} ${startYear}`
    }
    return `${start.toLocaleDateString('en-US', { month: 'short' })} ${startYear} – ${end.toLocaleDateString('en-US', { month: 'short' })} ${endYear}`
  }, [weekdays])

  // Get user's timezone label
  const userTimezone = useMemo(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Local Time'
    } catch {
      return 'Local Time'
    }
  }, [])

  const handleMouseDown = (index: number) => {
    setIsDragging(true)
    setDragStartIdx(index)
    setDragEndIdx(index)
    commitSelection(index, index)
  }

  const handleMouseEnter = (index: number) => {
    if (isDragging && dragStartIdx !== null) {
      setDragEndIdx(index)
      commitSelection(dragStartIdx, index)
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const commitSelection = (startIdx: number, endIdx: number) => {
    const minIdx = Math.min(startIdx, endIdx)
    const maxIdx = Math.max(startIdx, endIdx)

    const startSlot = timeSlots[minIdx]
    const endSlot = timeSlots[maxIdx]

    // Construct scheduled_datetime ISO string
    const [year, month, day] = activeDay.isoDateStr.split('-').map(Number)
    const scheduledDate = new Date(Date.UTC(year, month - 1, day, startSlot.hour, startSlot.minute, 0))

    let endHour = endSlot.hour
    let endMinute = endSlot.minute + 30
    if (endMinute >= 60) {
      endHour += 1
      endMinute -= 60
    }
    const endAmpm = endHour >= 12 ? 'PM' : 'AM'
    const endDisplayHour = endHour % 12 === 0 ? 12 : endHour % 12
    const endMinuteStr = endMinute === 0 ? '00' : '30'
    const endLabel = `${endDisplayHour}:${endMinuteStr} ${endAmpm}`

    const timeDisplay = `${startSlot.label} - ${endLabel}`
    const dateDisplay = `${activeDay.dayName}, ${activeDay.dateLabel}`

    onSelectSlot({
      scheduled_datetime: scheduledDate.toISOString(),
      timeDisplay,
      dateDisplay,
    })
  }

  const isSelected = (slotIndex: number) => {
    if (!selectedSlot || !activeDay) return false

    if (dragStartIdx !== null && dragEndIdx !== null) {
      const min = Math.min(dragStartIdx, dragEndIdx)
      const max = Math.max(dragStartIdx, dragEndIdx)
      if (slotIndex >= min && slotIndex <= max) return true
    }

    const slot = timeSlots[slotIndex]
    const [year, month, day] = activeDay.isoDateStr.split('-').map(Number)
    const slotDate = new Date(Date.UTC(year, month - 1, day, slot.hour, slot.minute, 0))
    return selectedSlot.scheduled_datetime === slotDate.toISOString()
  }

  const morningSlots = useMemo(() => timeSlots.filter((s) => s.hour < 12), [timeSlots])
  const afternoonSlots = useMemo(() => timeSlots.filter((s) => s.hour >= 12), [timeSlots])

  return (
    <div className="gcal-scheduler" onMouseLeave={handleMouseUp} onMouseUp={handleMouseUp}>
      {/* Google Calendar Header Bar */}
      <div className="gcal-header">
        <div className="gcal-header-left">
          <button
            type="button"
            className="gcal-today-btn"
            onClick={() => {
              setWeekOffset(0)
              const currentWeek = getWeekdays(0)
              const todayOption = currentWeek.find((d) => d.isToday) || currentWeek.find((d) => !d.isPast) || currentWeek[0]
              setActiveDateStr(todayOption.isoDateStr)
              setDragStartIdx(null)
              setDragEndIdx(null)
            }}
          >
            Today
          </button>
          <div className="gcal-nav-arrows">
            <button
              type="button"
              className="gcal-nav-btn"
              disabled={weekOffset <= 0}
              onClick={() => {
                const nextOffset = Math.max(0, weekOffset - 1)
                setWeekOffset(nextOffset)
                const prevWeek = getWeekdays(nextOffset)
                const validDay = prevWeek.find((d) => !d.isPast) || prevWeek[0]
                setActiveDateStr(validDay.isoDateStr)
                setDragStartIdx(null)
                setDragEndIdx(null)
              }}
              title="Previous week"
            >
              ‹
            </button>
            <button
              type="button"
              className="gcal-nav-btn"
              onClick={() => {
                const nextOffset = weekOffset + 1
                setWeekOffset(nextOffset)
                const nextWeek = getWeekdays(nextOffset)
                setActiveDateStr(nextWeek[0].isoDateStr)
                setDragStartIdx(null)
                setDragEndIdx(null)
              }}
              title="Next week"
            >
              ›
            </button>
          </div>
          <span className="gcal-month-title">{monthYearLabel}</span>
        </div>
        <div className="gcal-timezone-badge" title="Detected timezone">
          <span className="gcal-tz-icon">🌐</span> {userTimezone}
        </div>
      </div>

      {/* Weekday Selector Tabs */}
      <div className="gcal-day-tabs">
        {weekdays.map((day) => {
          const isActive = activeDay.isoDateStr === day.isoDateStr
          return (
            <button
              key={day.isoDateStr}
              type="button"
              disabled={day.isPast}
              className={`gcal-day-tab ${isActive ? 'active' : ''} ${day.isToday ? 'is-today' : ''} ${
                day.isPast ? 'is-past' : ''
              }`}
              onClick={() => {
                if (day.isPast) return
                setActiveDateStr(day.isoDateStr)
                setDragStartIdx(null)
                setDragEndIdx(null)
              }}
            >
              <span className="gcal-day-name">{day.dayName}</span>
              <span className={`gcal-date-badge ${day.isToday ? 'today-badge' : ''}`}>
                {day.date.getDate()}
              </span>
            </button>
          )
        })}
      </div>

      {/* Grouped Time Slots */}
      <div className="gcal-slots-container">
        <div className="gcal-slot-section">
          <div className="gcal-section-title">
            <span className="gcal-section-icon">🌅</span> Morning
          </div>
          <div className="gcal-slots-grid">
            {morningSlots.map((slot) => {
              const active = isSelected(slot.index)
              return (
                <div
                  key={slot.label}
                  className={`gcal-time-pill ${active ? 'selected' : ''}`}
                  onMouseDown={() => handleMouseDown(slot.index)}
                  onMouseEnter={() => handleMouseEnter(slot.index)}
                >
                  <span className="gcal-slot-time">{slot.label}</span>
                  <span className="gcal-slot-dur">30m</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="gcal-slot-section" style={{ marginTop: '14px' }}>
          <div className="gcal-section-title">
            <span className="gcal-section-icon">☀️</span> Afternoon
          </div>
          <div className="gcal-slots-grid">
            {afternoonSlots.map((slot) => {
              const active = isSelected(slot.index)
              return (
                <div
                  key={slot.label}
                  className={`gcal-time-pill ${active ? 'selected' : ''}`}
                  onMouseDown={() => handleMouseDown(slot.index)}
                  onMouseEnter={() => handleMouseEnter(slot.index)}
                >
                  <span className="gcal-slot-time">{slot.label}</span>
                  <span className="gcal-slot-dur">30m</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Selected Slot Summary Card */}
      {selectedSlot && (
        <div className="gcal-selection-summary">
          <div className="gcal-summary-left">
            <span className="gcal-summary-check">✓</span>
            <div>
              <div className="gcal-summary-date">{selectedSlot.dateDisplay}</div>
              <div className="gcal-summary-time">{selectedSlot.timeDisplay} ({userTimezone})</div>
            </div>
          </div>
          <span className="gcal-summary-badge">30 Min Demo</span>
        </div>
      )}
    </div>
  )
}

