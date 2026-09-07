import { NAMES, DEBUT, ARCS } from './data.js'

// Must stay byte-identical to the client's hash in src/game/state.js —
// the worker recomputes the day's answer to verify a claimed solve.
function hashString(s) {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function poolFor(arcLimit) {
  if (!arcLimit) return NAMES
  const arc = ARCS.find(([name]) => name === arcLimit)
  if (!arc) return NAMES
  const end = arc[1]
  return NAMES.filter((_, i) => DEBUT[i] <= end)
}

function answerFor(day, arcLimit) {
  const pool = poolFor(arcLimit)
  return pool[hashString('opdle:' + day) % pool.length]
}

const DAY_RE = /^\d{4}-\d{2}-\d{2}$/

// The client's day is its own local date, so accept a small window around UTC
// rather than trusting or rejecting it outright.
function dayIsPlausible(day) {
  if (!DAY_RE.test(day)) return false
  const t = Date.parse(day + 'T00:00:00Z')
  if (Number.isNaN(t)) return false
  const drift = Math.abs(Date.now() - t)
  return drift < 3 * 86400000
}

function cors(origin, env) {
  const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean)
  const ok = allowed.includes('*') || (origin && allowed.includes(origin))
  return {
    'Access-Control-Allow-Origin': ok ? origin || '*' : allowed[0] || '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    Vary: 'Origin',
  }
}

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...headers },
  })
}

async function ipHash(request, env) {
  const ip = request.headers.get('CF-Connecting-IP') || '0.0.0.0'
  const data = new TextEncoder().encode(`${env.IP_SALT || 'opdle'}:${ip}`)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return [...new Uint8Array(digest)].slice(0, 16).map(b => b.toString(16).padStart(2, '0')).join('')
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const headers = cors(request.headers.get('Origin'), env)

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers })

    // GET /count?day=YYYY-MM-DD&arc=<arc name> -> how many solved that day
    if (request.method === 'GET' && url.pathname === '/count') {
      const day = url.searchParams.get('day') || ''
      const arcLimit = url.searchParams.get('arc') || ''
      if (!DAY_RE.test(day)) return json({ error: 'bad day' }, 400, headers)
      const row = await env.DB.prepare(
        'SELECT count FROM solves WHERE day = ? AND arc_limit = ?'
      ).bind(day, arcLimit).first()
      return json({ day, arcLimit, count: row?.count ?? 0 }, 200, headers)
    }

    // POST /solve { day, arcLimit, name } -> verifies, counts once per address
    if (request.method === 'POST' && url.pathname === '/solve') {
      let body
      try {
        body = await request.json()
      } catch {
        return json({ error: 'bad json' }, 400, headers)
      }
      const day = String(body.day || '')
      const arcLimit = String(body.arcLimit || '')
      const name = String(body.name || '')
      if (!dayIsPlausible(day)) return json({ error: 'bad day' }, 400, headers)
      // Only a correct answer counts, so the tally can't be inflated by
      // anyone who hasn't actually solved it.
      if (name !== answerFor(day, arcLimit)) {
        return json({ error: 'wrong answer', counted: false }, 403, headers)
      }
      const hash = await ipHash(request, env)
      const first = await env.DB.prepare(
        'INSERT OR IGNORE INTO counted (day, arc_limit, ip_hash) VALUES (?, ?, ?)'
      ).bind(day, arcLimit, hash).run()
      const isNew = (first.meta?.changes ?? 0) > 0
      if (isNew) {
        await env.DB.prepare(
          `INSERT INTO solves (day, arc_limit, count) VALUES (?, ?, 1)
           ON CONFLICT(day, arc_limit) DO UPDATE SET count = count + 1`
        ).bind(day, arcLimit).run()
      }
      const row = await env.DB.prepare(
        'SELECT count FROM solves WHERE day = ? AND arc_limit = ?'
      ).bind(day, arcLimit).first()
      return json({ day, arcLimit, count: row?.count ?? 0, counted: isNew }, 200, headers)
    }

    if (url.pathname === '/health') return json({ ok: true }, 200, headers)

    return json({ error: 'not found' }, 404, headers)
  },
}
