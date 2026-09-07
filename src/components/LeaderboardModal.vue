<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { fetchLeaderboard, fetchMe, loginPlayer, registerPlayer } from '../game/api.js'

const props = defineProps({
  account: { type: Object, default: null },
  day: { type: String, required: true },
})
const emit = defineEmits(['close', 'account'])

const sort = ref('streak')
const entries = ref([])
const loading = ref(true)
const me = ref(null)

const mode = ref('join') // 'join' | 'restore'
const nameInput = ref('')
const codeInput = ref('')
const busy = ref(false)
const error = ref('')
const freshCode = ref(null) // shown once, right after registering

const SORTS = [
  { key: 'streak', label: 'Streak' },
  { key: 'wins', label: 'Wins' },
  { key: 'avg', label: 'Avg guesses' },
]

async function load() {
  loading.value = true
  const r = await fetchLeaderboard(sort.value, props.day)
  entries.value = r?.entries ?? []
  loading.value = false
  if (props.account) me.value = await fetchMe(props.account)
}

watch(sort, load)
onMounted(load)

const myRank = computed(() => {
  if (!props.account) return null
  const hit = entries.value.find(e => e.name === props.account.name)
  return hit?.rank ?? null
})

async function join() {
  error.value = ''
  busy.value = true
  const r = await registerPlayer(nameInput.value)
  busy.value = false
  if (r?.error) {
    error.value = r.error
    return
  }
  freshCode.value = r.code
  emit('account', { id: r.id, name: r.name, code: r.code })
  load()
}

async function restore() {
  error.value = ''
  busy.value = true
  const r = await loginPlayer(nameInput.value, codeInput.value)
  busy.value = false
  if (r?.error) {
    error.value = r.error
    return
  }
  emit('account', { id: r.id, name: r.name, code: codeInput.value.trim().toUpperCase() })
  load()
}

function signOut() {
  emit('account', null)
  me.value = null
  freshCode.value = null
}

const copied = ref(false)
async function copyCode() {
  const code = freshCode.value || props.account?.code
  if (!code) return
  try {
    await navigator.clipboard.writeText(code)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch { /* clipboard unavailable */ }
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal panel">
      <button class="modal-close" @click="emit('close')">×</button>
      <h2>Leaderboard</h2>

      <!-- Recovery code, shown once on registration -->
      <div v-if="freshCode" class="code-box">
        <p class="code-label">Save your recovery code</p>
        <p class="code">{{ freshCode }}</p>
        <p class="code-warn">
          This is the only way back into <b>{{ account?.name }}</b> on another device or after
          clearing your browser. It cannot be recovered — write it down now.
        </p>
        <div class="code-actions">
          <button @click="copyCode">{{ copied ? 'Copied!' : 'Copy code 📋' }}</button>
          <button @click="freshCode = null">I've saved it</button>
        </div>
      </div>

      <!-- Signed out: join or restore -->
      <div v-else-if="!account" class="join">
        <div class="tabs">
          <button :class="{ on: mode === 'join' }" @click="mode = 'join'; error = ''">New player</button>
          <button :class="{ on: mode === 'restore' }" @click="mode = 'restore'; error = ''">I have a code</button>
        </div>
        <p class="join-note">
          Pick a pseudonym to appear on the board. No email needed — you'll get a recovery code
          that carries your record to any device.
        </p>
        <input v-model="nameInput" placeholder="Pseudonym" maxlength="20" autocomplete="off" />
        <input
          v-if="mode === 'restore'" v-model="codeInput" placeholder="XXXX-XXXX-XXXX"
          autocomplete="off" spellcheck="false" />
        <p v-if="error" class="error">{{ error }}</p>
        <button
          class="primary" :disabled="busy || !nameInput.trim()"
          @click="mode === 'join' ? join() : restore()">
          {{ busy ? 'Working…' : mode === 'join' ? 'Join the leaderboard' : 'Restore my record' }}
        </button>
      </div>

      <!-- Signed in -->
      <div v-else class="signed-in">
        <span class="who">Playing as <b>{{ account.name }}</b></span>
        <span class="who-actions">
          <button @click="copyCode">{{ copied ? 'Copied!' : 'Copy code' }}</button>
          <button @click="signOut">Sign out</button>
        </span>
      </div>
      <p v-if="account && me" class="my-line">
        {{ me.wins }} ranked {{ me.wins === 1 ? 'win' : 'wins' }} ·
        streak {{ me.streak }} (best {{ me.maxStreak }}) ·
        avg {{ me.avg ?? '—' }}
        <template v-if="myRank"> · rank #{{ myRank }}</template>
      </p>

      <div class="tabs sort-tabs">
        <button
          v-for="s in SORTS" :key="s.key" :class="{ on: sort === s.key }"
          @click="sort = s.key">{{ s.label }}</button>
      </div>

      <p v-if="loading" class="empty">Loading…</p>
      <table v-else-if="entries.length" class="board">
        <thead>
          <tr><th>#</th><th>Player</th><th>Streak</th><th>Wins</th><th>Avg</th></tr>
        </thead>
        <tbody>
          <tr v-for="e in entries" :key="e.name" :class="{ mine: account && e.name === account.name }">
            <td>{{ e.rank }}</td>
            <td class="p-name">{{ e.name }}</td>
            <td>{{ e.streak }}<span class="best"> / {{ e.maxStreak }}</span></td>
            <td>{{ e.wins }}</td>
            <td>{{ e.avg ?? '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">
        Nobody's on the board yet — win today's character to be first.
      </p>

      <p class="fine">
        Only classic games with <b>no spoiler limit</b> count, since a limited roster is far easier.
        Streak shows current / best. Average needs 3+ wins to rank.
      </p>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 12px; }
.tabs { display: flex; gap: 8px; margin-bottom: 10px; }
.tabs button {
  flex: 1;
  font-family: inherit;
  font-weight: 700;
  font-size: 13px;
  padding: 7px;
  border-radius: 8px;
  border: 2px solid var(--tan);
  background: var(--parchment);
  color: var(--brown);
}
.tabs button.on {
  background: var(--parchment-dark);
  color: var(--brown-dark);
  border-color: var(--brown);
}
.sort-tabs { margin-top: 14px; }

.join { display: flex; flex-direction: column; gap: 8px; }
.join-note { margin: 0; font-size: 13px; color: var(--brown); }
.join input {
  font-family: inherit;
  font-size: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 2px solid var(--tan);
  background: #fffdf5;
  color: var(--ink);
  outline: none;
}
.primary {
  font-family: inherit;
  font-weight: 700;
  font-size: 15px;
  padding: 11px;
  border-radius: 8px;
  border: 2px solid var(--brown);
  background: var(--parchment-dark);
  color: var(--brown-dark);
}
.primary:disabled { opacity: .55; cursor: default; }
.error { margin: 0; color: var(--red); font-size: 13px; font-weight: 700; }

.code-box {
  border: 2px solid var(--yellow);
  background: var(--parchment-dark);
  border-radius: 8px;
  padding: 14px;
  text-align: center;
}
.code-label { margin: 0 0 6px; font-weight: 700; color: var(--brown-dark); }
.code {
  margin: 0 0 8px;
  font-family: ui-monospace, monospace;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--brown-dark);
}
.code-warn { margin: 0 0 10px; font-size: 13px; color: var(--brown); line-height: 1.4; }
.code-actions { display: flex; gap: 8px; justify-content: center; }
.code-actions button, .who-actions button {
  font-family: inherit;
  font-weight: 700;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 2px solid var(--tan);
  background: var(--parchment);
  color: var(--brown-dark);
}

.signed-in {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 14px;
  color: var(--brown);
}
.who-actions { display: flex; gap: 6px; }
.my-line {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--brown-dark);
  font-weight: 700;
}

.board { width: 100%; border-collapse: collapse; font-size: 14px; }
.board th {
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  color: var(--brown);
  border-bottom: 2px solid var(--tan);
  padding: 4px 6px;
}
.board td { padding: 6px; border-top: 1px solid var(--tan); }
.board tr.mine { background: var(--parchment-dark); }
.p-name { font-weight: 700; color: var(--brown-dark); overflow-wrap: anywhere; }
.best { color: var(--brown); font-size: 12px; }

.empty { text-align: center; font-style: italic; color: var(--brown); margin: 18px 0; }
.fine {
  margin: 14px 0 0;
  font-size: 12px;
  color: var(--brown);
  font-style: italic;
  line-height: 1.4;
}
</style>
