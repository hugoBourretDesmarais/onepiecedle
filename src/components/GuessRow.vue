<script setup>
import { displayName } from '../game/compare.js'

const props = defineProps({
  guess: { type: Object, required: true },
  base: { type: String, required: true },
})

const HAKI_ICONS = { Conqueror: '👑', Armament: '💪', Observation: '👀' }

const order = ['portrait', 'gender', 'affiliation', 'devilFruit', 'haki', 'bounty', 'height', 'origin', 'firstArc']

function cellClass(key) {
  const c = props.guess.cells[key]
  return [c.result, { animate: props.guess.animate }]
}

function textSize(text) {
  const len = String(text ?? '').length
  if (len <= 6) return 'lg'
  if (len <= 12) return 'md'
  if (len <= 20) return 'sm'
  return 'xs'
}
</script>

<template>
  <div class="row">
    <div
      v-for="(key, i) in order" :key="key"
      class="tile" :class="cellClass(key)" :style="{ '--d': i * 0.28 + 's' }">
      <template v-if="key === 'portrait'">
        <img
          class="portrait" :src="base + 'portraits/' + guess.char.portrait"
          :alt="guess.char.name" :title="displayName(guess.char)" />
      </template>
      <template v-else-if="key === 'haki'">
        <span v-if="guess.cells.haki.haki.includes('Unknown')" class="txt lg">?</span>
        <span v-else-if="!guess.cells.haki.haki.length" class="txt lg">✖</span>
        <span v-else class="haki-icons">
          <span v-for="h in guess.cells.haki.haki" :key="h" :title="h + ' Haki'">{{ HAKI_ICONS[h] }}</span>
        </span>
      </template>
      <template v-else>
        <span v-if="guess.cells[key].arrow === 'up'" class="arrow" aria-hidden="true">▲</span>
        <span v-if="guess.cells[key].arrow === 'down'" class="arrow" aria-hidden="true">▼</span>
        <span class="txt" :class="textSize(guess.cells[key].text)">{{ guess.cells[key].text }}</span>
      </template>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  gap: var(--tile-gap);
}

.tile {
  position: relative;
  width: var(--tile-size);
  height: var(--tile-size);
  border-radius: 8px;
  border: 2px solid rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #fff;
  font-weight: 700;
  overflow: hidden;
  padding: 3px;
}
.tile.exact { background: var(--green); }
.tile.partial { background: var(--yellow); }
.tile.wrong { background: var(--red); }
.tile.neutral { background: #2f2a22; padding: 0; }

.tile.animate {
  animation: flip .5s ease both;
  animation-delay: var(--d);
}
@keyframes flip {
  0% { transform: rotateY(90deg); opacity: .2; }
  100% { transform: rotateY(0); opacity: 1; }
}

.portrait {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top;
}

.txt {
  position: relative;
  z-index: 1;
  line-height: 1.08;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
  overflow-wrap: anywhere;
  hyphens: auto;
}
.txt.lg { font-size: clamp(9px, calc(var(--tile-size) * 0.24), 19px); }
.txt.md { font-size: clamp(8px, calc(var(--tile-size) * 0.19), 14px); }
.txt.sm { font-size: clamp(7px, calc(var(--tile-size) * 0.16), 12px); }
.txt.xs { font-size: clamp(6px, calc(var(--tile-size) * 0.14), 10px); }

.arrow {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: calc(var(--tile-size) * 0.92);
  line-height: 1;
  color: rgba(0, 0, 0, 0.34);
  z-index: 0;
}

.haki-icons {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1px;
  font-size: clamp(11px, calc(var(--tile-size) * 0.26), 20px);
  z-index: 1;
}
</style>
