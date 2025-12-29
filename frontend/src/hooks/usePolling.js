import { useState, useEffect, useCallback, useRef } from 'react'

export function usePolling(fetchFn, interval = 2000, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const intervalRef = useRef(null)
  const fetchFnRef = useRef(fetchFn)
  const isMountedRef = useRef(true)

  // Keep fetchFn ref updated
  useEffect(() => {
    fetchFnRef.current = fetchFn
  }, [fetchFn])

  // Track mounted state to prevent state updates after unmount
  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const poll = useCallback(async () => {
    try {
      setLoading(true)
      const result = await fetchFnRef.current()
      if (isMountedRef.current) {
        setData(result)
        setError(null)
      }
      return result
    } catch (err) {
      if (isMountedRef.current) {
        setError(err)
      }
      return null
    } finally {
      if (isMountedRef.current) {
        setLoading(false)
      }
    }
  }, [])

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const start = useCallback(() => {
    // Always clear existing interval first to prevent duplicates
    stop()
    poll() // Initial fetch
    intervalRef.current = setInterval(poll, interval)
  }, [poll, interval, stop])

  // Main effect: handles enabled state and interval changes
  // By including interval in deps, we restart polling when interval changes
  useEffect(() => {
    if (!enabled) {
      stop()
      return
    }

    // Clear any existing interval before starting new one
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    // Start polling
    poll()
    intervalRef.current = setInterval(poll, interval)

    // Cleanup on unmount or when deps change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, interval, poll])

  return { data, error, loading, poll, start, stop }
}
