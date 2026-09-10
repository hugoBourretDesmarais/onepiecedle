// Asserts that a spoiler-limited card shows what a reader at that point knows.
// Run with: node tools/check_spoilers.mjs
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const src = resolve(dirname(fileURLToPath(import.meta.url)), '..', 'src')
const chars = JSON.parse(readFileSync(resolve(src, 'data/characters.json'), 'utf8'))
const arcs = JSON.parse(readFileSync(resolve(src, 'data/arcs.json'), 'utf8'))
const compare = await import('data:text/javascript;base64,' +
  Buffer.from(readFileSync(resolve(src, 'game/compare.js'), 'utf8')).toString('base64'))

const byName = Object.fromEntries(chars.map(c => [c.name, c]))
const endOf = name => {
  if (name === null) return null
  const a = arcs.find(x => x.name === name)
  if (!a) throw new Error(`no such arc: ${name}`)
  return a.endChapter
}

// [character, arc limit (null = whole story), expected fields]
const CASES = [
  ['Monkey D. Luffy', 'Loguetown', { bounty: 30000000, haki: [], dfTypes: ['Paramecia'],
    dfName: 'Gum-Gum Fruit', heightCm: 172, affiliation: 'Straw Hat Pirates' }],
  ['Monkey D. Luffy', 'Alabasta', { bounty: 100000000, haki: [], heightCm: 172 }],
  ['Monkey D. Luffy', 'Dressrosa', { bounty: 500000000, heightCm: 174 }],
  ['Monkey D. Luffy', null, { bounty: 3000000000, dfTypes: ['Mythical Zoan', 'Paramecia'],
    heightCm: 174 }],

  ['Nico Robin', 'Alabasta', { affiliation: 'Baroque Works' }],
  ['Nico Robin', 'Enies Lobby', { affiliation: 'Straw Hat Pirates' }],

  ['Marshall D. Teach', 'Jaya', { dfTypes: [], dfName: null }],
  ['Marshall D. Teach', 'Impel Down', { dfTypes: ['Logia'], dfName: 'Dark-Dark Fruit' }],
  ['Marshall D. Teach', null, { dfTypes: ['Logia', 'Paramecia'] }],

  ['X Drake', 'Sabaody Archipelago', { affiliation: 'Drake Pirates' }],
  ['Buggy', 'Orange Town', { affiliation: 'Buggy Pirates' }],
  ['Rob Lucci', 'Enies Lobby', { affiliation: 'CP9' }],

  ['Roronoa Zoro', 'Alabasta', { haki: [], heightCm: 178 }],
  // Koby enlists in chapter 7 and Brook joins in 489, both exactly on an arc
  // boundary, so these read as the later value at the end of that arc.
  ['Koby', 'Romance Dawn', { affiliation: 'Marines' }],
  ['Brook', 'Thriller Bark', { affiliation: 'Straw Hat Pirates', heightCm: 266 }],
  ['Franky', 'Water 7', { affiliation: 'Franky Family' }],
]

let failed = 0
for (const [name, arc, expected] of CASES) {
  const c = byName[name]
  if (!c) { console.log(`MISSING ${name}`); failed++; continue }
  const got = compare.atChapter(c, endOf(arc))
  for (const [k, want] of Object.entries(expected)) {
    const have = got[k]
    const ok = JSON.stringify(have) === JSON.stringify(want)
    if (!ok) {
      console.log(`FAIL ${name} @ ${arc ?? 'no limit'}: ${k} = ` +
        `${JSON.stringify(have)}, expected ${JSON.stringify(want)}`)
      failed++
    }
  }
}

// Invariants that must hold for every character at every arc.
for (const c of chars) {
  for (const arc of arcs) {
    if (c.firstChapter > arc.endChapter) continue
    const got = compare.atChapter(c, arc.endChapter)
    if (!got.affiliation) {
      console.log(`FAIL ${c.name} @ ${arc.name}: no affiliation`); failed++
    }
    if (got.haki.some(h => !c.haki.includes(h))) {
      console.log(`FAIL ${c.name} @ ${arc.name}: haki not a subset of the latest`); failed++
    }
    if (got.bounty != null && !c.bounties.some(b => b.amount === got.bounty)) {
      console.log(`FAIL ${c.name} @ ${arc.name}: bounty not from its own history`); failed++
    }
    if (got.dfTypes.length && !c.dfTypes.length) {
      console.log(`FAIL ${c.name} @ ${arc.name}: invented a devil fruit`); failed++
    }
  }
}

console.log(failed ? `\n${failed} failures` : `\nall ${CASES.length} cases + invariants pass`)
process.exit(failed ? 1 : 0)
