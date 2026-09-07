export const COLUMNS = [
  { key: 'portrait', label: 'Character' },
  { key: 'gender', label: 'Gender' },
  { key: 'affiliation', label: 'Affiliation' },
  { key: 'devilFruit', label: 'Devil Fruit' },
  { key: 'haki', label: 'Haki' },
  { key: 'bounty', label: 'Last Bounty' },
  { key: 'height', label: 'Height' },
  { key: 'origin', label: 'Origin' },
  { key: 'firstArc', label: 'First Arc' },
]

const ZOAN_FAMILY = new Set(['Zoan', 'Ancient Zoan', 'Mythical Zoan'])
const PARAMECIA_FAMILY = new Set(['Paramecia', 'Special Paramecia'])

function setResult(guessArr, answerArr) {
  const g = new Set(guessArr)
  const a = new Set(answerArr)
  if (g.size === a.size && [...g].every(x => a.has(x))) return 'exact'
  if ([...g].some(x => a.has(x))) return 'partial'
  return 'wrong'
}

function dfResult(guessArr, answerArr) {
  const base = setResult(guessArr, answerArr)
  if (base !== 'wrong') return base
  const sameFamily = (fam) => guessArr.some(t => fam.has(t)) && answerArr.some(t => fam.has(t))
  if (sameFamily(ZOAN_FAMILY) || sameFamily(PARAMECIA_FAMILY)) return 'partial'
  return 'wrong'
}

function numResult(guess, answer) {
  if (guess == null && answer == null) return { result: 'exact', arrow: null }
  if (guess == null || answer == null) return { result: 'wrong', arrow: null }
  if (guess === answer) return { result: 'exact', arrow: null }
  return { result: 'wrong', arrow: answer > guess ? 'up' : 'down' }
}

export function compareGuess(guess, answer, arcOrder) {
  const cells = {}
  cells.portrait = { result: guess.name === answer.name ? 'exact' : 'neutral' }
  cells.gender = { result: guess.gender === answer.gender ? 'exact' : 'wrong', text: guess.gender }
  cells.affiliation = {
    result: guess.affiliation === answer.affiliation ? 'exact' : 'wrong',
    text: guess.affiliation,
  }
  const gdf = guess.dfTypes.length ? guess.dfTypes : ['None']
  const adf = answer.dfTypes.length ? answer.dfTypes : ['None']
  cells.devilFruit = { result: dfResult(gdf, adf), text: gdf.join(' / ') }
  cells.haki = { result: setResult(guess.haki, answer.haki), haki: guess.haki }

  const b = numResult(guess.bounty ?? 0, answer.bounty ?? 0)
  cells.bounty = { ...b, text: formatBounty(guess.bounty) }
  const h = numResult(guess.heightCm, answer.heightCm)
  cells.height = { ...h, text: formatHeight(guess.heightCm) }

  cells.origin = { result: guess.origin === answer.origin ? 'exact' : 'wrong', text: guess.origin }

  const gi = arcOrder.indexOf(guess.firstArc)
  const ai = arcOrder.indexOf(answer.firstArc)
  const a = numResult(gi < 0 ? null : gi, ai < 0 ? null : ai)
  cells.firstArc = { ...a, text: guess.firstArc ?? 'Unknown' }
  return cells
}

export function formatBounty(b) {
  if (b == null) return '฿0'
  if (b === 0) return '฿0'
  if (b >= 1e9) return '฿' + trim(b / 1e9) + 'B'
  if (b >= 1e6) return '฿' + trim(b / 1e6) + 'M'
  if (b >= 1e3) return '฿' + trim(b / 1e3) + 'K'
  return '฿' + b
}

function trim(x) {
  const s = x.toFixed(2)
  return s.replace(/\.?0+$/, '')
}

export function displayName(c) {
  return c.codename ? `${c.name} (${c.codename})` : c.name
}

export function formatHeight(cm) {
  if (cm == null) return '?'
  const m = Math.floor(cm / 100)
  const rest = Math.round(cm % 100)
  if (m === 0) return `0m${String(rest).padStart(2, '0')}`
  return `${m}m${String(rest).padStart(2, '0')}`
}
