<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  characters: { type: Array, required: true },
})
const emit = defineEmits(['open'])

const base = import.meta.env.BASE_URL
const query = ref('')
const sort = ref('name')

function norm(s) {
  return String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

// Searching affiliation/origin/fruit/arc as well as the name makes the gallery
// browsable by concept ("marines", "logia", "east blue"), not just by name.
function haystack(c) {
  return norm([
    c.name, ...(c.aliases || []), c.affiliation, c.origin, c.dfName,
    ...c.dfTypes, ...c.haki, c.firstArc,
  ].filter(Boolean).join(' '))
}

const indexed = computed(() => props.characters.map(c => ({ c, hay: haystack(c) })))

const results = computed(() => {
  const q = norm(query.value.trim())
  let list = indexed.value
  if (q) {
    const terms = q.split(/\s+/)
    list = list.filter(({ hay }) => terms.every(t => hay.includes(t)))
  }
  const out = list.map(x => x.c)
  const key = sort.value
  return [...out].sort((a, b) => {
    if (key === 'name') return a.name.localeCompare(b.name)
    if (key === 'debut') return (a.firstChapter ?? 0) - (b.firstChapter ?? 0)
    if (key === 'bounty') return (b.bounty ?? -1) - (a.bounty ?? -1)
    if (key === 'height') return (b.heightCm ?? -1) - (a.heightCm ?? -1)
    return 0
  })
})
</script>

<template>
  <section class="gallery">
    <div class="controls panel">
      <input
        v-model="query" type="search" class="search"
        placeholder="Search name, crew, fruit, origin..."
        autocomplete="off" spellcheck="false" />
      <div class="controls-row">
        <label class="sort">
          Sort
          <select v-model="sort">
            <option value="name">Name (A–Z)</option>
            <option value="debut">First appearance</option>
            <option value="bounty">Highest bounty</option>
            <option value="height">Tallest</option>
          </select>
        </label>
        <span class="count">
          {{ results.length }} of {{ characters.length }} characters
        </span>
      </div>
    </div>

    <div v-if="results.length" class="cards">
      <button
        v-for="c in results" :key="c.name" class="card" :title="c.name"
        @click="emit('open', c)">
        <img :src="base + 'portraits/' + c.portrait" :alt="c.name" loading="lazy" decoding="async" />
        <span class="card-name">{{ c.name }}</span>
      </button>
    </div>
    <p v-else class="empty panel">
      No character matches “{{ query }}”.
    </p>
  </section>
</template>

<style scoped>
.gallery {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
}

.controls {
  width: min(560px, 100%);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search {
  width: 100%;
  font-family: inherit;
  font-size: 17px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 2px solid var(--tan);
  background: #fffdf5;
  color: var(--ink);
  outline: none;
}
.search::placeholder { color: #a08c66; }

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.sort {
  font-size: 13px;
  font-weight: 700;
  color: var(--brown-dark);
  display: flex;
  align-items: center;
  gap: 6px;
}
.sort select {
  font-family: inherit;
  font-size: 13px;
  padding: 4px 6px;
  border-radius: 6px;
  border: 2px solid var(--tan);
  background: var(--parchment-dark);
  color: var(--brown-dark);
  font-weight: 700;
}
.count { font-size: 13px; color: var(--brown); font-weight: 600; }

.cards {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(104px, 1fr));
  gap: 10px;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 6px 4px 8px;
  border-radius: 10px;
  border: 3px solid var(--tan);
  background: var(--parchment);
  transition: transform .12s, box-shadow .12s;
}
.card:hover, .card:focus-visible {
  transform: translateY(-3px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.3);
  outline: none;
  border-color: var(--brown);
}
.card img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  object-position: top;
  border-radius: 6px;
  background: #fff;
}
.card-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--brown-dark);
  line-height: 1.15;
  text-align: center;
  overflow-wrap: anywhere;
}

.empty {
  padding: 20px;
  font-style: italic;
  color: var(--brown);
}

@media (max-width: 760px) {
  .cards { grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 8px; }
  .card-name { font-size: 11px; }
}
</style>
