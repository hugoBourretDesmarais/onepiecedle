// Solve counter backed by the Cloudflare Worker in api/. Every call fails
// soft: the counter is a nicety, so a backend outage must never block play.
const BASE = import.meta.env.VITE_API_URL || ''

export const apiEnabled = Boolean(BASE)

async function call(path, options, timeoutMs = 6000) {
  if (!BASE) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const res = await fetch(BASE + path, { ...options, signal: ctrl.signal })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export function fetchCount(day, arcLimit) {
  const q = new URLSearchParams({ day, arc: arcLimit || '' })
  return call(`/count?${q}`, { method: 'GET' })
}

export function reportSolve(day, arcLimit, name) {
  return call('/solve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ day, arcLimit: arcLimit || '', name }),
  })
}
