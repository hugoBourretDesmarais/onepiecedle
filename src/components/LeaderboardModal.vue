<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { MIN_PASSWORD, fetchLeaderboard, fetchMe, loginPlayer, logoutPlayer, registerPlayer } from '../game/api.js'

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
const passwordInput = ref('')
const busy = ref(false)
const error = ref('')

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

const canSubmit = computed(
  () => nameInput.value.trim().length >= 2 && passwordInput.value.length >= MIN_PASSWORD)

async function submit() {
  error.value = ''
  busy.value = true
  const fn = mode.value === 'join' ? registerPlayer : loginPlayer
  const r = await fn(nameInput.value, passwordInput.value)
  busy.value = false
  if (r?.error) {
    error.value = r.error
    return
  }
  passwordInput.value = ''
  emit('account', { id: r.id, name: r.name, token: r.token })
  load()
}

function signOut() {
  logoutPlayer(props.account)
  emit('account', null)
  me.value = null
}
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal panel">
      <button class="modal-close" @click="emit('close')">×</button>
      <h2>Leaderboard</h2>

      <!-- Signed out: create an account or sign in -->
      <div v-if="!account" class="join">
        <div class="tabs">
          <button :class="{ on: mode === 'join' }" @click="mode = 'join'; error = ''">Create account</button>
          <button :class="{ on: mode === 'restore' }" @click="mode = 'restore'; error = ''">Sign in</button>
        </div>
        <p class="join-note">
          A pseudonym and a password — no email needed. Sign in with the same two on any device
          and your record follows you.
        </p>
        <form @submit.prevent="canSubmit && submit()">
          <input
            v-model="nameInput" placeholder="Pseudonym" maxlength="20"
            autocomplete="username" autocapitalize="off" />
          <input
            v-model="passwordInput" type="password" :placeholder="`Password (${MIN_PASSWORD}+ characters)`"
            :autocomplete="mode === 'join' ? 'new-password' : 'current-password'" />
          <p v-if="error" class="error">{{ error }}</p>
          <button class="primary" type="submit" :disabled="busy || !canSubmit">
            {{ busy ? 'Working\u2026' : mode === 'join' ? 'Create account' : 'Sign in' }}
          </button>
        </form>
        <p v-if="mode === 'join'" class="warn">
          There is no password reset yet \u2014 if you forget it the account can't be recovered.
          Please don't reuse an important password.
        </p>
      </div>

      <!-- Signed in -->
      <div v-else class="signed-in">
        <span class="who">Playing as <b>{{ account.name }}</b></span>
        <span class="who-actions">
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

.who-actions button {
  font-family: inherit;
  font-weight: 700;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 2px solid var(--tan);
  background: var(--parchment);
  color: var(--brown-dark);
}

.join form { display: flex; flex-direction: column; gap: 8px; }
.warn {
  margin: 0;
  font-size: 12px;
  color: var(--brown);
  font-style: italic;
  line-height: 1.4;
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
