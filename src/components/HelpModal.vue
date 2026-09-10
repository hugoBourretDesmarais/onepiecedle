<script setup>
const emit = defineEmits(['close'])
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal panel">
      <button class="modal-close" @click="emit('close')">×</button>
      <h2>How to play</h2>
      <p>Guess today's One Piece character. Each guess reveals its properties and how they compare to the hidden character.</p>
      <ul class="colors">
        <li><span class="swatch exact"></span><b>Green</b> — exact match</li>
        <li><span class="swatch partial"></span><b>Yellow</b> — partial match (some overlap)</li>
        <li><span class="swatch wrong"></span><b>Red</b> — no match</li>
      </ul>
      <p>On <b>Last Bounty</b>, <b>Height</b> and <b>First Arc</b>, an arrow shows whether the hidden character's value is <b>▲ higher/later</b> or <b>▼ lower/earlier</b> than your guess.</p>

      <h3>Properties</h3>
      <table class="props">
        <tbody>
          <tr><td>Gender</td><td>Male, Female, Other or Unknown</td></tr>
          <tr><td>Affiliation</td><td>Main crew or organization (e.g. Straw Hat Pirates, Marines)</td></tr>
          <tr><td>Devil Fruit</td><td>Fruit type: Paramecia, Zoan, Ancient Zoan, Mythical Zoan, Logia, Special Paramecia, None or Unknown</td></tr>
          <tr><td>Haki</td><td>Confirmed haki: 👑 Conqueror, 💪 Armament, 👀 Observation — ✖ none, ? unknown. Yellow when you share at least one type but not all of them</td></tr>
          <tr><td>Last Bounty</td><td>Latest known bounty (0 if none). With a spoiler limit set, the latest one revealed by the end of that arc</td></tr>
          <tr><td>Height</td><td>Latest known height. With a spoiler limit set, the height as of that arc — the Straw Hats are shorter before the timeskip</td></tr>
          <tr><td>Origin</td><td>Sea of origin (East Blue, Grand Line, …)</td></tr>
          <tr><td>First Arc</td><td>Story arc of first appearance, arrows follow story order</td></tr>
        </tbody>
      </table>

      <h3>Clues</h3>
      <p>Stuck? After several guesses you unlock the <b>First Appearance</b> clue (arc/episode), the <b>Devil Fruit</b> clue (fruit name) and, after 10 guesses, the <b>Affiliation</b> clue (crew or group).</p>
      <h3>Modes</h3>
      <table class="props">
        <tbody>
          <tr><td>☠️ Classic</td><td>One character per day, shared by everyone. Resets at your local midnight.</td></tr>
          <tr><td>🎲 Practice</td><td>Unlimited random characters — hit <b>New character</b> any time to reroll.</td></tr>
          <tr><td>📖 Gallery</td><td>Browse all characters and search by name, crew, devil fruit, haki or origin. Tap a card for full details, or untick it to keep it out of practice mode.</td></tr>
        </tbody>
      </table>

      <h3>🏆 Leaderboard</h3>
      <p>
        Pick a pseudonym and a password to join — no email required. Sign in with the same two on
        any device and your ranked record follows you. There's no password reset yet, so don't reuse
        an important password.
        Only classic games with <b>no spoiler limit</b> are ranked, since a limited roster is much
        easier. Your local 📊 stats stay on this device and are separate from your ranked record.
      </p>

      <h3>Avoiding spoilers</h3>
      <p>
        Not caught up? Open <b>⚙️ Settings</b> and set how far you've read. Only characters who have
        appeared by the end of that arc show up as the answer, in the guess suggestions or in the
        gallery — and each card <b>rewinds</b> to what was known by then. Bounty, crew, haki, devil
        fruit, height and even the portrait all follow the story: in Alabasta, Luffy is a ฿100M
        Straw Hat with no haki and a plain Gum-Gum Fruit, and Robin is still Baroque Works.
      </p>

      <h3>Also play AvatarDle</h3>
      <p>
        The same account works on <a href="https://hugobourretdesmarais.github.io/avatardle/">AvatarDle</a>:
        sign in on one game and you're signed in on the other. Rankings stay separate per game.
      </p>

      <p class="note">Data from the One Piece Wiki — with no spoiler limit set, current story spoilers are included!</p>
    </div>
  </div>
</template>

<style scoped>
p, li { font-size: 15px; }
h3 {
  font-family: 'Lilita One', cursive;
  color: var(--brown-dark);
  margin-bottom: 4px;
}
.colors {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.props {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.props td {
  border-top: 1px solid var(--tan);
  padding: 5px 8px 5px 0;
  vertical-align: top;
}
.props td:first-child {
  font-weight: 700;
  white-space: nowrap;
  color: var(--brown-dark);
}
.note { font-style: italic; color: var(--brown); }
</style>
