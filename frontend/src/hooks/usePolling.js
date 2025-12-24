import { useState, useEffect, useCallback, useRef } from 'react'

export function usePolling(fetchFn, interval = 2000, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const intervalRef = useRef(null)
  const fetchFnRef = useRef(fetchFn)

  // Keep fetchFn ref updated
  useEffect(() => {
    fetchFnRef.current = fetchFn
  }, [fetchFn])

  const poll = useCallback(async () => {
    try {
      setLoading(true)
      const result = await fetchFnRef.current()
      setData(result)
      setError(null)
      return result
    } catch (err) {
      setError(err)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const start = useCallback(() => {
    if (intervalRef.current) return
    poll() // Initial fetch
    intervalRef.current = setInterval(poll, interval)
  }, [poll, interval])

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  useEffect(() => {
    if (enabled) {
      start()
    } else {
      stop()
    }
    return stop
  }, [enabled, start, stop])

  return { data, error, loading, poll, start, stop }
}
