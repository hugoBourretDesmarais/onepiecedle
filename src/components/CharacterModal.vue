<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { formatBounty, formatHeight } from '../game/compare.js'

const props = defineProps({
  character: { type: Object, required: true },
  // The arc the player has read up to, or null for the whole story.
  limitArc: { type: Object, default: null },
})
const emit = defineEmits(['close'])

const base = import.meta.env.BASE_URL
const HAKI_ICONS = { Conqueror: '👑', Armament: '💪', Observation: '👀' }

const c = computed(() => props.character)
const otherAliases = computed(() => c.value.aliases.filter(a => a !== c.value.codename))

const devilFruit = computed(() => {
  const x = c.value
  if (!x.dfTypes.length) return { type: 'None', name: null }
  return { type: x.dfTypes.join(' / '), name: x.dfName }
})

const haki = computed(() => {
  const h = c.value.haki
  if (!h.length) return 'None'
  if (h.includes('Unknown')) return 'Unknown'
  return h.map(t => `${HAKI_ICONS[t]} ${t}`).join(', ')
})

const bountyText = computed(() => {
  const b = c.value.bounty
  return b == null ? '฿0 (none known)' : `${formatBounty(b)} (${b.toLocaleString('en-US')} berries)`
})

// Only the raises the player has read; the rest of the history is a spoiler.
const bountyHistory = computed(() => {
  const cap = props.limitArc?.endChapter
  return (c.value.bounties ?? []).filter(
    b => b.chapter != null && (cap == null || b.chapter <= cap))
})

const heightText = computed(() => {
  const cm = c.value.heightCm
  return cm == null ? 'Unknown' : `${formatHeight(cm)} (${cm} cm)`
})

// True when the card is showing an older value than the wiki's latest, so only
// the rows that actually moved get flagged rather than every row on the card.
function rewound(field) {
  const cap = props.limitArc?.endChapter
  if (cap == null) return false
  const list = field === 'bounty' ? c.value.bounties : c.value.history?.[field]
  return (list ?? []).some(e => e.chapter == null || e.chapter > cap)
}

const debut = computed(() => {
  const x = c.value
  const ch = x.firstChapter != null ? `Chapter ${x.firstChapter}` : 'Unknown chapter'
  const ep = x.firstEpisode != null ? `Episode ${x.firstEpisode}` : 'not yet animated'
  return `${ch} · ${ep}`
})

const wikiUrl = computed(
  () => 'https://onepiece.fandom.com/wiki/' + encodeURIComponent(c.value.wikiPage.replace(/ /g, '_')))

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal panel char-modal">
      <button class="modal-close" @click="emit('close')">×</button>

      <div class="char-head">
        <img class="char-portrait" :src="base + 'portraits/' + c.portrait" :alt="c.name" />
        <div class="char-id">
          <h2>{{ c.name }}</h2>
          <p v-if="c.codename" class="codename">{{ c.codename }}</p>
          <p v-if="otherAliases.length" class="aliases">{{ otherAliases.join(' · ') }}</p>
        </div>
      </div>

      <p v-if="limitArc" class="as-of">
        Shown as known by the end of <b>{{ limitArc.name }}</b>. Rows marked
        <span class="flag">then</span> changed later in the story.
      </p>

      <table class="details">
        <tbody>
          <tr><td>Gender</td><td>{{ c.gender }}</td></tr>
          <tr>
            <td>Affiliation</td>
            <td>{{ c.affiliation }}<span v-if="rewound('affiliation')" class="flag">then</span></td>
          </tr>
          <tr>
            <td>Devil Fruit</td>
            <td>
              {{ devilFruit.type }}
              <span v-if="devilFruit.name" class="sub">— {{ devilFruit.name }}</span>
              <span v-if="rewound('devilFruit')" class="flag">then</span>
            </td>
          </tr>
          <tr>
            <td>Haki</td>
            <td>{{ haki }}<span v-if="rewound('haki')" class="flag">then</span></td>
          </tr>
          <tr>
            <td>Last Bounty</td>
            <td>
              {{ bountyText }}
              <span v-if="rewound('bounty')" class="flag">then</span>
              <div v-if="bountyHistory.length > 1" class="history">
                previously
                <span v-for="b in bountyHistory.slice(1)" :key="b.chapter" class="history-item">
                  {{ formatBounty(b.amount) }}<span class="chap">ch. {{ b.chapter }}</span>
                </span>
              </div>
            </td>
          </tr>
          <tr>
            <td>Height</td>
            <td>{{ heightText }}<span v-if="rewound('heightCm')" class="flag">then</span></td>
          </tr>
          <tr><td>Origin</td><td>{{ c.origin }}</td></tr>
          <tr><td>First arc</td><td>{{ c.firstArc ?? 'Unknown' }}</td></tr>
          <tr><td>Debut</td><td>{{ debut }}</td></tr>
        </tbody>
      </table>

      <a class="wiki-link" :href="wikiUrl" target="_blank" rel="noreferrer">
        Read more on the One Piece Wiki ↗
      </a>
    </div>
  </div>
</template>

<style scoped>
.char-modal { max-width: 480px; }

.char-head {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}
.char-portrait {
  width: 108px;
  height: 108px;
  flex: none;
  object-fit: cover;
  object-position: top;
  border-radius: 10px;
  border: 3px solid var(--tan);
  background: #fff;
}
.char-id { min-width: 0; }
.char-id h2 {
  text-align: left;
  margin: 0 0 4px;
  font-size: 24px;
  line-height: 1.1;
}
.codename {
  margin: 0 0 3px;
  font-size: 14px;
  font-weight: 700;
  color: var(--brown-dark);
}
.aliases {
  margin: 0;
  font-size: 13px;
  font-style: italic;
  color: var(--brown);
  overflow-wrap: anywhere;
}

.details {
  width: 100%;
  border-collapse: collapse;
  font-size: 15px;
}
.details td {
  border-top: 1px solid var(--tan);
  padding: 7px 8px 7px 0;
  vertical-align: top;
}
.details td:first-child {
  font-weight: 700;
  white-space: nowrap;
  color: var(--brown-dark);
  width: 38%;
}
.sub { color: var(--brown); }

.as-of {
  margin: 0 0 10px;
  font-size: 12.5px;
  color: var(--brown);
  background: var(--parchment-dark);
  border-radius: 8px;
  padding: 6px 10px;
}
.flag {
  display: inline-block;
  margin-left: 6px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: #6b4f27;
  background: var(--parchment-dark);
  border: 1px solid var(--tan);
  border-radius: 6px;
  padding: 0 5px;
  vertical-align: 1px;
}

.history {
  margin-top: 4px;
  font-size: 12.5px;
  color: var(--brown);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
}
.history-item {
  background: var(--parchment-dark);
  border-radius: 8px;
  padding: 1px 7px;
  white-space: nowrap;
}
.chap { opacity: .75; margin-left: 4px; font-size: 11px; }

.wiki-link {
  display: inline-block;
  margin-top: 16px;
  font-weight: 700;
  color: var(--brown-dark);
}

@media (max-width: 480px) {
  .char-head { flex-direction: column; text-align: center; gap: 10px; }
  .char-id h2 { text-align: center; }
}
</style>
