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

const post = (path, body) => call(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

// Register and login surface their error text, so they bypass the soft-fail
// wrapper — a taken name has to be shown to the player, not swallowed.
async function postStrict(path, body) {
  if (!BASE) return { error: 'Leaderboard is unavailable.' }
  try {
    const res = await fetch(BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json().catch(() => null)
    if (!res.ok) return { error: data?.error || `Request failed (${res.status}).` }
    return data
  } catch {
    return { error: 'Could not reach the leaderboard. Check your connection.' }
  }
}

export const registerPlayer = name => postStrict('/register', { name })
export const loginPlayer = (name, code) => postStrict('/login', { name, code })

export function submitResult(account, day, arcLimit, guesses, name) {
  if (!account) return Promise.resolve(null)
  return post('/result', { id: account.id, code: account.code, day, arcLimit: arcLimit || '', guesses, name })
}

export function fetchLeaderboard(sort, day) {
  return call(`/leaderboard?${new URLSearchParams({ sort, day })}`, { method: 'GET' })
}

export function fetchMe(account) {
  if (!account) return Promise.resolve(null)
  return call(`/me?${new URLSearchParams({ id: account.id, code: account.code })}`, { method: 'GET' })
}
