// Daily selection, persistence, stats.
const EPOCH = '2026-09-06' // daily #1

function hashString(s) {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

export function localDateString(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function dailyNumber(dateStr = localDateString()) {
  const ms = new Date(dateStr) - new Date(EPOCH)
  return Math.round(ms / 86400000) + 1
}

export function dailyIndex(count, dateStr = localDateString()) {
  return hashString('opdle:' + dateStr) % count
}

export function randomIndex(count, avoid = -1) {
  let i = Math.floor(Math.random() * count)
  if (count > 1 && i === avoid) i = (i + 1) % count
  return i
}

export function msUntilMidnight() {
  const now = new Date()
  const next = new Date(now)
  next.setHours(24, 0, 0, 0)
  return next - now
}

const KEY = 'opdle'

function load(key, fallback) {
  try {
    const v = JSON.parse(localStorage.getItem(`${KEY}:${key}`))
    return v ?? fallback
  } catch {
    return fallback
  }
}

function save(key, value) {
  localStorage.setItem(`${KEY}:${key}`, JSON.stringify(value))
}

// Guesses are only meaningful against the answer they were made on, and the
// answer depends on the spoiler limit, so a saved board is scoped to both.
export function loadDailyState(arcLimit) {
  const s = load('daily', null)
  if (!s || s.date !== localDateString() || s.arcLimit !== arcLimit) {
    return { date: localDateString(), arcLimit, guesses: [], won: false }
  }
  return s
}

export function saveDailyState(s) {
  save('daily', s)
}

// null = no limit (full roster)
export function loadArcLimit() {
  return load('arcLimit', null)
}

export function saveArcLimit(arcName) {
  save('arcLimit', arcName)
}

// Stored as exclusions so characters added to the roster later default to in.
export function loadExcluded() {
  return new Set(load('excluded', []))
}

export function saveExcluded(set) {
  save('excluded', [...set])
}

export function loadStats() {
  return load('stats', { played: 0, wins: 0, streak: 0, maxStreak: 0, lastWinDate: null, tries: {} })
}

export function recordWin(numGuesses) {
  const stats = loadStats()
  stats.played += 1
  stats.wins += 1
  const yesterday = localDateString(-1)
  stats.streak = stats.lastWinDate === yesterday || stats.lastWinDate === localDateString()
    ? stats.streak + 1 : 1
  stats.maxStreak = Math.max(stats.maxStreak, stats.streak)
  stats.lastWinDate = localDateString()
  stats.tries[numGuesses] = (stats.tries[numGuesses] || 0) + 1
  save('stats', stats)
  return stats
}

export function currentStreak() {
  const stats = loadStats()
  const today = localDateString()
  const yesterday = localDateString(-1)
  if (stats.lastWinDate === today || stats.lastWinDate === yesterday) return stats.streak
  return 0
}
