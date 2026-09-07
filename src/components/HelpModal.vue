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
        <li><span class="swatch partial"></span><b>Orange</b> — partial match (some overlap)</li>
        <li><span class="swatch wrong"></span><b>Red</b> — no match</li>
      </ul>
      <p>On <b>Last Bounty</b>, <b>Height</b> and <b>First Arc</b>, an arrow shows whether the hidden character's value is <b>▲ higher/later</b> or <b>▼ lower/earlier</b> than your guess.</p>

      <h3>Properties</h3>
      <table class="props">
        <tbody>
          <tr><td>Gender</td><td>Male, Female, Other or Unknown</td></tr>
          <tr><td>Affiliation</td><td>Main crew or organization (e.g. Straw Hat Pirates, Marines)</td></tr>
          <tr><td>Devil Fruit</td><td>Fruit type: Paramecia, Zoan, Ancient Zoan, Mythical Zoan, Logia, Special Paramecia, None or Unknown</td></tr>
          <tr><td>Haki</td><td>Confirmed haki: 👑 Conqueror, 💪 Armament, 👀 Observation — ✖ none, ? unknown</td></tr>
          <tr><td>Last Bounty</td><td>Latest known bounty (0 if none)</td></tr>
          <tr><td>Height</td><td>Latest known height</td></tr>
          <tr><td>Origin</td><td>Sea of origin (East Blue, Grand Line, …)</td></tr>
          <tr><td>First Arc</td><td>Story arc of first appearance, arrows follow story order</td></tr>
        </tbody>
      </table>

      <h3>Clues</h3>
      <p>Stuck? After several guesses you unlock the <b>First Appearance</b> clue (chapter/episode) and the <b>Devil Fruit</b> clue (fruit name).</p>
      <p class="note">A new character every day at midnight (your local time). Data from the One Piece Wiki — current story spoilers included!</p>
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
