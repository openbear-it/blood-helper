import { useEffect, useRef, useState } from 'react'

interface AlertPayload {
  expiring_units?: Array<{
    hospital_id: string
    hospital_name: string
    blood_type: string
    units: number
    expiry_date: string
  }>
  critical_levels?: Array<{
    hospital_id: string
    hospital_name: string
    blood_type: string
    units_available: number
    status: string
  }>
}

export function useAlertsWebSocket() {
  const [alerts, setAlerts] = useState<AlertPayload | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/alerts`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data) as AlertPayload
        setAlerts(data)
      } catch {
        // ignore malformed messages
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  return { alerts, connected }
}
