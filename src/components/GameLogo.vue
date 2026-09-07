<script setup>
// The original swaps the leading O for the crew's Jolly Roger; the rest of the
// wordmark alternates red/blue with a heavy white outline.
const LETTERS = [...'NEPIECEDLE']
</script>

<template>
  <h1 class="logo" aria-label="OnePieceDle">
    <span class="mark" aria-hidden="true">
      <svg viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="47" fill="#fff" />
        <circle cx="50" cy="50" r="42" fill="#111" />
        <!-- skull -->
        <path
          d="M50 34c-11 0-18.5 7-18.5 16.6 0 5 2.3 8.6 5 10.8 1.2 1 1.9 2.2 1.9 3.7v2.1c0 1.7 1.5 3 3.3 3h16.6c1.8 0 3.3-1.3 3.3-3v-2.1c0-1.5.7-2.7 1.9-3.7 2.7-2.2 5-5.8 5-10.8C68.5 41 61 34 50 34z"
          fill="#fff" />
        <ellipse cx="42.6" cy="51" rx="4.6" ry="5.2" fill="#111" />
        <ellipse cx="57.4" cy="51" rx="4.6" ry="5.2" fill="#111" />
        <path d="M46.4 61.6h7.2v2.6h-7.2z" fill="#111" />
        <!-- straw hat -->
        <path d="M22 36c0-3 12.6-8 28-8s28 5 28 8-12.6 5.4-28 5.4S22 39 22 36z" fill="#f2c14a" />
        <path d="M35 33c0-6.4 6.7-11.4 15-11.4S65 26.6 65 33z" fill="#f2c14a" />
        <path d="M33.5 33.4c0-6.6 7.4-11.8 16.5-11.8s16.5 5.2 16.5 11.8" fill="none" stroke="#c9922c" stroke-width="1.6" />
        <path d="M34 31.4h32v4.2H34z" fill="#d33a3a" />
        <!-- crossbones -->
        <g fill="#fff">
          <path d="M18 66.5l64 12 1.4-7.4-64-12z" />
          <path d="M82 66.5l-64 12L16.6 71l64-12z" />
          <circle cx="16" cy="63" r="5.4" /><circle cx="20" cy="70" r="5.4" />
          <circle cx="84" cy="63" r="5.4" /><circle cx="80" cy="70" r="5.4" />
          <circle cx="16" cy="76" r="5.4" /><circle cx="20" cy="83" r="5.4" />
          <circle cx="84" cy="76" r="5.4" /><circle cx="80" cy="83" r="5.4" />
        </g>
      </svg>
    </span>
    <span
      v-for="(ch, i) in LETTERS" :key="i"
      class="ltr" :class="i % 2 ? 'lb' : 'lr'"
      :style="{ animationDelay: 120 + i * 45 + 'ms' }">{{ ch }}</span>
  </h1>
</template>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
  margin: 2px 0 0;
  font-family: 'Lilita One', cursive;
  font-size: clamp(34px, 7.4vw, 60px);
  letter-spacing: 1px;
  user-select: none;
  line-height: 1;
}

.mark {
  width: 1.28em;
  height: 1.28em;
  margin-right: .04em;
  filter: drop-shadow(2px 3px 0 rgba(0, 0, 0, .4));
  animation: mark-in .55s cubic-bezier(.2, .9, .3, 1.5) both, sway 5.5s ease-in-out 1s infinite;
}
.mark svg { width: 100%; height: 100%; display: block; }

.ltr {
  display: inline-block;
  -webkit-text-stroke: 3px #fff;
  paint-order: stroke fill;
  text-shadow: 2px 3px 0 rgba(0, 0, 0, .4);
  animation: drop .5s cubic-bezier(.2, .8, .3, 1.5) both;
}
.lr { color: #e23b3b; }
.lb { color: #3f6fd2; }

@keyframes drop {
  from { transform: translateY(-20px) rotate(-7deg); opacity: 0; }
  to { transform: none; opacity: 1; }
}
@keyframes mark-in {
  from { transform: scale(.4) rotate(-40deg); opacity: 0; }
  to { transform: none; opacity: 1; }
}
@keyframes sway {
  0%, 100% { transform: rotate(-3.5deg); }
  50% { transform: rotate(3.5deg); }
}

@media (prefers-reduced-motion: reduce) {
  .mark, .ltr { animation: none; }
}
</style>
