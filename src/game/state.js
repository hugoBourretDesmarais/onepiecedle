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
// answer depends on the spoiler limit, so today's boards are kept per limit.
function arcKey(arcLimit) {
  return arcLimit ?? '*'
}

function loadDailyBoards() {
  const all = load('daily', null)
  if (!all || all.date !== localDateString() || !all.boards) {
    return { date: localDateString(), boards: {} }
  }
  return all
}

export function loadDailyState(arcLimit) {
  const s = loadDailyBoards().boards[arcKey(arcLimit)]
  return s ?? { date: localDateString(), arcLimit, guesses: [], won: false }
}

export function saveDailyState(s) {
  const all = loadDailyBoards()
  all.boards[arcKey(s.arcLimit)] = s
  save('daily', all)
}

// null = no limit (full roster)
export function loadArcLimit() {
  return load('arcLimit', null)
}

export function saveArcLimit(arcName) {
  save('arcLimit', arcName)
}

// { id, name, code } — the code is the only credential, so losing it means
// losing the account; the UI makes the player save it before continuing.
export function loadAccount() {
  return load('account', null)
}

export function saveAccount(account) {
  if (account) save('account', account)
  else localStorage.removeItem(`${KEY}:account`)
}

// The day a signed-out winner was last invited to sign up, so the prompt comes
// back tomorrow rather than on every reload of a day already won.
export function loadPromptedDay() {
  return load('promptedDay', null)
}

export function savePromptedDay(day) {
  save('promptedDay', day)
}

// Stored as exclusions so characters added to the roster later default to in.
export function loadExcluded() {
  return new Set(load('excluded', []))
}

export function saveExcluded(set) {
  save('excluded', [...set])
}

function emptyMode() {
  return { played: 0, wins: 0, guesses: 0, tries: {}, guessed: {} }
}

function normalizeMode(m) {
  return { ...emptyMode(), ...(m || {}), tries: { ...(m?.tries || {}) }, guessed: { ...(m?.guessed || {}) } }
}

export function loadStats() {
  const raw = load('stats', null)
  const classicExtras = { streak: 0, maxStreak: 0, lastWinDate: null, lastPlayedDate: null }
  if (!raw) {
    return { classic: { ...emptyMode(), ...classicExtras }, practice: emptyMode() }
  }
  // Pre-split stats were a single flat object; those games were all classic.
  const legacy = raw.classic || raw.practice ? null : raw
  return {
    classic: {
      ...classicExtras,
      ...normalizeMode(legacy || raw.classic),
      ...(legacy
        ? {
            streak: legacy.streak ?? 0,
            maxStreak: legacy.maxStreak ?? 0,
            lastWinDate: legacy.lastWinDate ?? null,
            lastPlayedDate: legacy.lastWinDate ?? null,
          }
        : {
            streak: raw.classic?.streak ?? 0,
            maxStreak: raw.classic?.maxStreak ?? 0,
            lastWinDate: raw.classic?.lastWinDate ?? null,
            lastPlayedDate: raw.classic?.lastPlayedDate ?? null,
          }),
    },
    practice: normalizeMode(legacy ? null : raw.practice),
  }
}

export function recordGuess(mode, charName) {
  const stats = loadStats()
  const m = stats[mode]
  m.guesses += 1
  m.guessed[charName] = (m.guessed[charName] || 0) + 1
  // A classic game is one per calendar day however many times the board resets.
  if (mode === 'classic') {
    const today = localDateString()
    if (m.lastPlayedDate !== today) {
      m.played += 1
      m.lastPlayedDate = today
    }
  }
  save('stats', stats)
  return stats
}

export function recordPracticeStart() {
  const stats = loadStats()
  stats.practice.played += 1
  save('stats', stats)
  return stats
}

export function recordWin(mode, numGuesses) {
  const stats = loadStats()
  const m = stats[mode]
  if (mode === 'classic') {
    const today = localDateString()
    // Already credited today — a second win (e.g. after changing the spoiler
    // limit) must not inflate wins or the streak.
    if (m.lastWinDate === today) return stats
    m.streak = m.lastWinDate === localDateString(-1) ? m.streak + 1 : 1
    m.maxStreak = Math.max(m.maxStreak, m.streak)
    m.lastWinDate = today
  }
  m.wins += 1
  m.tries[numGuesses] = (m.tries[numGuesses] || 0) + 1
  save('stats', stats)
  return stats
}

// A streak is only live if the last win was today or yesterday; any longer gap
// breaks it, regardless of how many wins came before.
export function currentStreak() {
  const { classic } = loadStats()
  if (classic.lastWinDate === localDateString() || classic.lastWinDate === localDateString(-1)) {
    return classic.streak
  }
  return 0
}
