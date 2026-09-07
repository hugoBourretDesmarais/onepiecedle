<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import characters from './data/characters.json'
import arcs from './data/arcs.json'
import { COLUMNS, compareGuess } from './game/compare.js'
import {
  dailyIndex, dailyNumber, loadDailyState, loadArcLimit, loadExcluded, localDateString,
  msUntilMidnight, randomIndex, recordWin, saveArcLimit, saveDailyState, saveExcluded,
  currentStreak,
} from './game/state.js'
import GuessInput from './components/GuessInput.vue'
import GuessRow from './components/GuessRow.vue'
import WinPanel from './components/WinPanel.vue'
import HelpModal from './components/HelpModal.vue'
import StatsModal from './components/StatsModal.vue'
import CluesPanel from './components/CluesPanel.vue'
import GalleryPanel from './components/GalleryPanel.vue'
import CharacterModal from './components/CharacterModal.vue'
import SettingsModal from './components/SettingsModal.vue'

const arcOrder = arcs.map(a => a.name)
const byName = new Map(characters.map(c => [c.name, c]))

const mode = ref('daily') // 'daily' | 'practice' | 'gallery'
const showHelp = ref(false)
const showStats = ref(false)
const showSettings = ref(false)
const galleryPick = ref(null)
const streak = ref(currentStreak())
const arcLimit = ref(loadArcLimit())
const excluded = ref(loadExcluded())

// Everything the player can meet — answers, suggestions, gallery — comes from here.
const pool = computed(() => {
  if (!arcLimit.value) return characters
  const arc = arcs.find(a => a.name === arcLimit.value)
  if (!arc) return characters
  return characters.filter(c => c.firstChapter <= arc.endChapter)
})

// Exclusions only narrow practice; the daily stays shared between players.
const practicePool = computed(() => pool.value.filter(c => !excluded.value.has(c.name)))

function toggleExcluded(c) {
  const next = new Set(excluded.value)
  if (next.has(c.name)) next.delete(c.name)
  else next.add(c.name)
  excluded.value = next
  saveExcluded(next)
}

function setAllExcluded({ chars, included }) {
  const next = new Set(excluded.value)
  for (const c of chars) {
    if (included) next.delete(c.name)
    else next.add(c.name)
  }
  excluded.value = next
  saveExcluded(next)
}

const daily = reactive({
  number: dailyNumber(),
  answer: null,
  guesses: [], // {char, cells}
  won: false,
  triesAtWin: 0,
})
const practice = reactive({ answer: null, guesses: [], won: false })

const yesterdayAnswer = computed(
  () => pool.value[dailyIndex(pool.value.length, localDateString(-1))])

const game = computed(() => (mode.value === 'practice' ? practice : daily))
const guessedNames = computed(() => new Set(game.value.guesses.map(g => g.char.name)))

function restoreDaily() {
  daily.answer = pool.value[dailyIndex(pool.value.length)]
  daily.guesses = []
  daily.won = false
  const s = loadDailyState(arcLimit.value)
  for (const name of s.guesses) {
    const char = byName.get(name)
    if (char) daily.guesses.unshift({ char, cells: compareGuess(char, daily.answer, arcOrder), animate: false })
  }
  daily.won = s.won
  daily.triesAtWin = s.guesses.length
}

function persistDaily() {
  saveDailyState({
    date: localDateString(),
    arcLimit: arcLimit.value,
    guesses: [...daily.guesses].reverse().map(g => g.char.name),
    won: daily.won,
  })
}

function applyArcLimit(next) {
  arcLimit.value = next
  saveArcLimit(next)
  restoreDaily()
  newPractice()
  galleryPick.value = null
}

function submitGuess(char) {
  const g = game.value
  if (g.won || guessedNames.value.has(char.name)) return
  const cells = compareGuess(char, g.answer, arcOrder)
  g.guesses.unshift({ char, cells, animate: true })
  if (char.name === g.answer.name) {
    g.won = true
    if (mode.value === 'daily') {
      daily.triesAtWin = daily.guesses.length
      recordWin(daily.guesses.length)
      streak.value = currentStreak()
    }
  }
  if (mode.value === 'daily') persistDaily()
}

function newPractice() {
  const src = practicePool.value.length ? practicePool.value : pool.value
  practice.answer = src[randomIndex(src.length)]
  practice.guesses = []
  practice.won = false
}

// countdown to next daily
const countdown = ref('')
let timer = null
function tick() {
  const ms = msUntilMidnight()
  const h = String(Math.floor(ms / 3600000)).padStart(2, '0')
  const m = String(Math.floor((ms % 3600000) / 60000)).padStart(2, '0')
  const s = String(Math.floor((ms % 60000) / 1000)).padStart(2, '0')
  countdown.value = `${h}:${m}:${s}`
}

onMounted(() => {
  restoreDaily()
  newPractice()
  tick()
  timer = setInterval(tick, 1000)
  if (!localStorage.getItem('opdle:visited')) {
    showHelp.value = true
    localStorage.setItem('opdle:visited', '1')
  }
})
onUnmounted(() => clearInterval(timer))

const base = import.meta.env.BASE_URL
</script>

<template>
  <div class="page">
    <header class="header">
      <h1 class="logo" aria-label="One Piece Dle">
        <span v-for="(ch, i) in 'ONEPIECEDLE'" :key="i" :class="i % 2 ? 'lb' : 'lr'">{{ ch }}</span>
      </h1>

      <div class="modes">
        <button class="mode-btn" :class="{ active: mode === 'daily' }" title="Classic (daily)"
          @click="mode = 'daily'">
          <span class="mode-ico">☠️</span>
          <span v-if="daily.won" class="mode-check">✔</span>
        </button>
        <button class="mode-btn" :class="{ active: mode === 'practice' }" title="Practice (unlimited)"
          @click="mode = 'practice'">
          <span class="mode-ico">🎲</span>
          <span v-if="practice.won" class="mode-check">✔</span>
        </button>
        <button class="mode-btn" :class="{ active: mode === 'gallery' }" title="Character gallery"
          @click="mode = 'gallery'">
          <span class="mode-ico">📖</span>
        </button>
      </div>

      <div class="toolbar panel">
        <button class="tool" title="Statistics" @click="showStats = true">📊</button>
        <span class="tool streak" title="Daily win streak">🔥<b>{{ streak }}</b></span>
        <span class="tool daily-num" :title="`Daily character #${daily.number}`">#{{ daily.number }}</span>
        <button
          class="tool" :class="{ 'tool-on': arcLimit }"
          :title="arcLimit ? `Spoiler limit: up to ${arcLimit}` : 'Settings'"
          @click="showSettings = true">⚙️</button>
        <button class="tool" title="How to play" @click="showHelp = true">❓</button>
      </div>

      <p v-if="arcLimit" class="arc-banner">
        📖 Spoiler-safe up to <b>{{ arcLimit }}</b> — {{ pool.length }} of {{ characters.length }} characters
        <button class="arc-clear" @click="applyArcLimit(null)">clear</button>
      </p>
    </header>

    <main class="game">
      <template v-if="mode === 'gallery'">
        <section class="panel intro">
          <h2>CHARACTER GALLERY</h2>
          <p class="gallery-hint">
            {{ arcLimit ? `The ${pool.length} characters seen up to ${arcLimit}` : `All ${characters.length} characters in the game` }}.
            Search by name, crew, devil fruit, haki or origin — then tap a card for the full details.
          </p>
        </section>
        <GalleryPanel
          :characters="pool" :excluded="excluded" :arc-limit="arcLimit"
          @open="galleryPick = $event" @toggle="toggleExcluded" @set-all="setAllExcluded" />
      </template>

      <template v-else>
        <section class="panel intro">
          <h2 v-if="mode === 'daily'">GUESS TODAY'S ONE PIECE CHARACTER!</h2>
          <h2 v-else>PRACTICE MODE — GUESS THE CHARACTER!</h2>
          <CluesPanel :answer="game.answer" :tries="game.guesses.length" :won="game.won" />
          <button v-if="mode === 'practice'" class="reset-btn" @click="newPractice">
            🎲 New character
          </button>
          <p v-if="mode === 'practice' && excluded.size" class="practice-pool">
            Drawing from <b>{{ practicePool.length }}</b> of {{ pool.length }} characters
            <template v-if="!practicePool.length">— none selected, using all</template>
            <span class="pool-hint">· change this in the 📖 gallery</span>
          </p>
        </section>

        <WinPanel
          v-if="game.won" :answer="game.answer" :tries="game.guesses.length" :mode="mode"
          :countdown="countdown" :guesses="game.guesses" :daily-number="daily.number"
          @practice="mode = 'practice'"
          @replay="newPractice" />

        <GuessInput
          v-if="!game.won" :characters="pool" :guessed="guessedNames"
          @guess="submitGuess" />

        <section v-if="game.guesses.length" class="grid-wrap">
          <div class="grid">
            <div class="grid-head">
              <div v-for="col in COLUMNS" :key="col.key" class="head-cell">{{ col.label }}</div>
            </div>
            <GuessRow v-for="g in game.guesses" :key="g.char.name" :guess="g" :base="base" />
          </div>
        </section>

        <p class="yesterday" v-if="mode === 'daily' && daily.number > 1">
          Yesterday's character #{{ daily.number - 1 }} was <b>{{ yesterdayAnswer.name }}</b>
        </p>
      </template>

      <footer class="footer">
        Fan-made recreation of <a href="https://onepiecedle.net" target="_blank" rel="noreferrer">onepiecedle.net</a>
        · data from the <a href="https://onepiece.fandom.com" target="_blank" rel="noreferrer">One Piece Wiki</a>
        · One Piece © Eiichiro Oda / Shueisha
      </footer>
    </main>

    <HelpModal v-if="showHelp" @close="showHelp = false" />
    <StatsModal v-if="showStats" @close="showStats = false" />
    <CharacterModal v-if="galleryPick" :character="galleryPick" @close="galleryPick = null" />
    <SettingsModal
      v-if="showSettings" :arcs="arcs" :characters="characters" :arc-limit="arcLimit"
      @update:arc-limit="applyArcLimit" @close="showSettings = false" />
  </div>
</template>

<style scoped>
.page {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.logo {
  font-family: 'Lilita One', cursive;
  font-size: clamp(38px, 8vw, 64px);
  margin: 4px 0 0;
  letter-spacing: 2px;
  user-select: none;
}
.logo span {
  -webkit-text-stroke: 2px #fff;
  paint-order: stroke fill;
  text-shadow: 2px 3px 0 rgba(0, 0, 0, 0.35);
}
.logo .lr { color: #d23f3f; }
.logo .lb { color: #3f6fd2; }

.modes { display: flex; gap: 16px; }
.mode-btn {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 3px solid #1c1712;
  background: radial-gradient(circle at 35% 30%, #4a3b28, #211a12 70%);
  font-size: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: grayscale(.7) brightness(.85);
  transition: transform .12s, filter .12s;
}
.mode-btn.active { filter: none; transform: scale(1.08); border-color: #caa96b; }
.mode-btn:hover { filter: none; }
.mode-ico { pointer-events: none; }
.mode-check {
  position: absolute;
  bottom: -6px;
  right: -6px;
  background: var(--green);
  color: #fff;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
}
.tool {
  background: none;
  border: none;
  font-size: 20px;
  padding: 4px 8px;
  color: var(--brown-dark);
}
.streak b { font-size: 15px; margin-left: 2px; }
.daily-num {
  font-weight: 700;
  font-size: 15px;
  color: var(--brown-dark);
  background: var(--parchment-dark);
  border-radius: 12px;
  padding: 4px 10px;
}

.game {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 18px;
  gap: 16px;
}

.intro {
  width: min(560px, 100%);
  padding: 18px 22px;
  text-align: center;
}
.intro h2 {
  font-family: 'Lilita One', cursive;
  color: var(--brown-dark);
  letter-spacing: 1px;
  font-size: 22px;
  margin: 0 0 14px;
}

.reset-btn {
  margin-top: 14px;
  border: 2px solid var(--tan);
  background: var(--parchment-dark);
  color: var(--brown-dark);
  font-weight: 700;
  border-radius: 8px;
  padding: 9px 16px;
  font-size: 15px;
}
.reset-btn:hover { filter: brightness(.96); }

.gallery-hint {
  margin: 0;
  font-size: 14px;
  color: var(--brown);
}

.practice-pool {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--brown);
}
.pool-hint { opacity: .8; }

.tool-on {
  background: var(--parchment-dark);
  border-radius: 12px;
}

.arc-banner {
  margin: 0;
  padding: 6px 12px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.28);
  color: #fff;
  font-size: 13px;
  text-align: center;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.arc-clear {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.6);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  padding: 2px 8px;
}
.arc-clear:hover { background: rgba(255, 255, 255, 0.15); }

.grid-wrap {
  width: 100%;
  overflow-x: auto;
  padding-bottom: 6px;
}
.grid {
  display: flex;
  flex-direction: column;
  gap: var(--tile-gap);
  width: max-content;
  margin: 0 auto;
}
.grid-head {
  display: flex;
  gap: var(--tile-gap);
}
.head-cell {
  width: var(--tile-size);
  font-weight: 700;
  font-size: clamp(8px, calc(var(--tile-size) * 0.14), 12px);
  text-transform: uppercase;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  text-align: center;
  border-bottom: 2px solid #fff;
  padding-bottom: 4px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  line-height: 1.15;
}

.yesterday {
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  font-size: 15px;
  margin: 4px 0 0;
}

.footer {
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
  font-size: 12px;
  text-align: center;
  margin-top: 26px;
}
.footer a { color: #ffe9a8; }
</style>
