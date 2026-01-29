import { useState, useEffect } from 'react'

export function useApi(endpoint) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api${endpoint}`)
      if (!res.ok) throw new Error('API error')
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refetch() }, [endpoint])

  return { data, loading, error, refetch }
}

export async function apiPost(endpoint, body) {
  const res = await fetch(`/api${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error('API error')
  return res.json()
}

export async function apiDelete(endpoint) {
  const res = await fetch(`/api${endpoint}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('API error')
  return res.json()
}

export async function apiGet(endpoint) {
  const res = await fetch(`/api${endpoint}`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'API error')
  }
  return res.json()
}
