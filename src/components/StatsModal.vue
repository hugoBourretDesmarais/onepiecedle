<script setup>
import { computed } from 'vue'
import { loadStats, currentStreak } from '../game/state.js'

const emit = defineEmits(['close'])
const stats = loadStats()
const streak = currentStreak()

const winRate = computed(() => (stats.played ? Math.round((stats.wins / stats.played) * 100) : 0))

const distribution = computed(() => {
  const entries = Object.entries(stats.tries)
    .map(([k, v]) => [Number(k), v])
    .sort((a, b) => a[0] - b[0])
  const max = Math.max(1, ...entries.map(e => e[1]))
  return entries.map(([tries, count]) => ({ tries, count, pct: (count / max) * 100 }))
})
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal panel">
      <button class="modal-close" @click="emit('close')">×</button>
      <h2>Statistics</h2>
      <div class="stat-row">
        <div class="stat"><b>{{ stats.played }}</b><span>Played</span></div>
        <div class="stat"><b>{{ winRate }}%</b><span>Win rate</span></div>
        <div class="stat"><b>{{ streak }}</b><span>Streak</span></div>
        <div class="stat"><b>{{ stats.maxStreak }}</b><span>Max streak</span></div>
      </div>
      <h3 v-if="distribution.length">Tries distribution</h3>
      <div class="dist">
        <div v-for="d in distribution" :key="d.tries" class="dist-row">
          <span class="dist-label">{{ d.tries }}</span>
          <div class="dist-bar" :style="{ width: d.pct + '%' }">{{ d.count }}</div>
        </div>
      </div>
      <p v-if="!stats.played" class="empty">Win your first daily character to start your stats!</p>
    </div>
  </div>
</template>

<style scoped>
.stat-row {
  display: flex;
  justify-content: space-around;
  margin: 18px 0;
}
.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat b { font-size: 26px; color: var(--brown-dark); }
.stat span { font-size: 12px; text-transform: uppercase; color: var(--brown); }
h3 {
  font-family: 'Lilita One', cursive;
  color: var(--brown-dark);
  margin-bottom: 6px;
}
.dist { display: flex; flex-direction: column; gap: 4px; }
.dist-row { display: flex; align-items: center; gap: 8px; }
.dist-label { width: 20px; text-align: right; font-weight: 700; }
.dist-bar {
  background: var(--green);
  color: #fff;
  font-weight: 700;
  font-size: 13px;
  border-radius: 4px;
  padding: 2px 6px;
  min-width: 22px;
  text-align: right;
}
.empty { text-align: center; font-style: italic; color: var(--brown); }
</style>
