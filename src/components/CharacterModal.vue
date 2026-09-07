<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { formatBounty, formatHeight } from '../game/compare.js'

const props = defineProps({
  character: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const base = import.meta.env.BASE_URL
const HAKI_ICONS = { Conqueror: '👑', Armament: '💪', Observation: '👀' }

const c = computed(() => props.character)

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

const heightText = computed(() => {
  const cm = c.value.heightCm
  return cm == null ? 'Unknown' : `${formatHeight(cm)} (${cm} cm)`
})

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
          <p v-if="c.aliases.length" class="aliases">{{ c.aliases.join(' · ') }}</p>
        </div>
      </div>

      <table class="details">
        <tbody>
          <tr><td>Gender</td><td>{{ c.gender }}</td></tr>
          <tr><td>Affiliation</td><td>{{ c.affiliation }}</td></tr>
          <tr>
            <td>Devil Fruit</td>
            <td>
              {{ devilFruit.type }}
              <span v-if="devilFruit.name" class="sub">— {{ devilFruit.name }}</span>
            </td>
          </tr>
          <tr><td>Haki</td><td>{{ haki }}</td></tr>
          <tr><td>Last Bounty</td><td>{{ c.bounty == null ? '฿0 (none known)' : formatBounty(c.bounty) + ' (' + c.bounty.toLocaleString('en-US') + ' berries)' }}</td></tr>
          <tr><td>Height</td><td>{{ heightText }}</td></tr>
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
