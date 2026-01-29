import { useState, useEffect, useCallback } from 'react'

const API_BASE = '/api'

async function handleResponse(res) {
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    const message = data.detail || data.message || `HTTP ${res.status}`
    throw new Error(message)
  }
  return res.json()
}

export function useApi(endpoint, options = {}) {
  const { pollInterval, skip } = options
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(!skip)
  const [error, setError] = useState(null)

  const refetch = useCallback(async () => {
    if (skip) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}${endpoint}`)
      setData(await handleResponse(res))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [endpoint, skip])

  useEffect(() => {
    refetch()
  }, [refetch])

  useEffect(() => {
    if (!pollInterval || skip) return
    const interval = setInterval(refetch, pollInterval)
    return () => clearInterval(interval)
  }, [pollInterval, refetch, skip])

  return { data, loading, error, refetch }
}

export async function apiPost(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  return handleResponse(res)
}

export async function apiPatch(endpoint, body) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  return handleResponse(res)
}

export async function apiDelete(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' })
  return handleResponse(res)
}

export async function apiGet(endpoint) {
  const res = await fetch(`${API_BASE}${endpoint}`)
  return handleResponse(res)
}
