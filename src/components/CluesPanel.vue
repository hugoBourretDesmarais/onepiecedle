<script setup>
import { computed, ref, watch } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  answer: { type: Object, required: true },
  tries: { type: Number, required: true },
  won: { type: Boolean, required: true },
})

const FIRST_AT = 5
const FRUIT_AT = 8

const showFirst = ref(false)
const showFruit = ref(false)
watch(() => props.answer, () => {
  showFirst.value = false
  showFruit.value = false
})

const firstUnlocked = computed(() => props.won || props.tries >= FIRST_AT)
const fruitUnlocked = computed(() => props.won || props.tries >= FRUIT_AT)
const firstLeft = computed(() => Math.max(0, FIRST_AT - props.tries))
const fruitLeft = computed(() => Math.max(0, FRUIT_AT - props.tries))

const fruitText = computed(() => {
  const a = props.answer
  if (!a.dfTypes.length) return 'No devil fruit'
  return a.dfName || 'Unknown devil fruit'
})
</script>

<template>
  <div class="clues">
    <div class="clue">
      <button class="clue-btn" :disabled="!firstUnlocked" @click="showFirst = !showFirst">
        <Icon class="clue-ico" name="scroll" :size="30" />
        <span class="clue-label">First Appearance Clue</span>
        <span v-if="!firstUnlocked" class="clue-lock">in {{ firstLeft }} {{ firstLeft === 1 ? 'try' : 'tries' }}</span>
      </button>
      <p v-if="showFirst && firstUnlocked" class="clue-value">
        {{ answer.firstArc ?? 'Unknown arc' }} / Episode {{ answer.firstEpisode ?? '—' }}
      </p>
    </div>
    <div class="clue">
      <button class="clue-btn" :disabled="!fruitUnlocked" @click="showFruit = !showFruit">
        <Icon class="clue-ico" name="fruit" :size="30" />
        <span class="clue-label">Devil Fruit Clue</span>
        <span v-if="!fruitUnlocked" class="clue-lock">in {{ fruitLeft }} {{ fruitLeft === 1 ? 'try' : 'tries' }}</span>
      </button>
      <p v-if="showFruit && fruitUnlocked" class="clue-value">{{ fruitText }}</p>
    </div>
  </div>
</template>

<style scoped>
.clues {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}
.clue {
  flex: 1;
  min-width: 160px;
  max-width: 220px;
}
.clue-btn {
  width: 100%;
  min-height: 108px;
  border: 2px solid var(--tan);
  border-radius: 8px;
  background: var(--parchment);
  color: var(--brown);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
}
.clue-btn:not(:disabled):hover {
  background: var(--parchment-dark);
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(0, 0, 0, .18);
}
.clue-value { animation: clue-in .25s ease both; }
@keyframes clue-in {
  from { transform: translateY(-4px); opacity: 0; }
  to { transform: none; opacity: 1; }
}
.clue-btn:disabled { opacity: .6; cursor: default; }
.clue-ico { color: var(--brown); }
.clue-label {
  font-weight: 700;
  text-transform: uppercase;
  font-size: 13px;
  letter-spacing: .5px;
}
.clue-lock { font-size: 12px; font-style: italic; }
.clue-value {
  margin: 8px 0 0;
  font-weight: 700;
  color: var(--brown-dark);
}
</style>
