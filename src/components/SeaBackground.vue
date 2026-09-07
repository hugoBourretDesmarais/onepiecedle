<script setup>
import { computed } from 'vue'

const props = defineProps({
  // 0..n — pick a palette; the caller ties this to the date so it changes daily
  seed: { type: Number, default: 0 },
})

// Hand-tuned so each reads as a different time of day rather than a hue shift.
const THEMES = [
  { // clear morning
    sky: ['#a8dcf0', '#7cc4e4', '#4f9fd0'],
    sun: '#fff6d8', glow: 'rgba(255,244,200,.55)', sunY: 22,
    sea: ['#2f7fb5', '#1d5f92', '#164b76'], cloud: 'rgba(255,255,255,.85)',
    island: '#2b5f7a', haze: 'rgba(255,250,225,.25)',
  },
  { // bright noon
    sky: ['#bfe9fb', '#8ed2ee', '#59a9d6'],
    sun: '#ffffff', glow: 'rgba(255,255,255,.5)', sunY: 14,
    sea: ['#3d92c4', '#256c9e', '#17527e'], cloud: 'rgba(255,255,255,.92)',
    island: '#31687f', haze: 'rgba(255,255,255,.22)',
  },
  { // golden hour
    sky: ['#ffd9a0', '#f7a86b', '#d9705c'],
    sun: '#fff1c0', glow: 'rgba(255,196,120,.6)', sunY: 34,
    sea: ['#b56a5c', '#7d4a5e', '#4a3358'], cloud: 'rgba(255,226,196,.8)',
    island: '#5b3a52', haze: 'rgba(255,190,130,.28)',
  },
  { // dusk
    sky: ['#8f7fc0', '#6a5f9e', '#3f3a6e'],
    sun: '#ffe9b8', glow: 'rgba(255,220,160,.45)', sunY: 40,
    sea: ['#3c4a86', '#2c3565', '#1e2447'], cloud: 'rgba(226,220,255,.7)',
    island: '#2b2f57', haze: 'rgba(200,190,255,.2)',
  },
  { // night
    sky: ['#1b2a52', '#152040', '#0d162c'],
    sun: '#eef3ff', glow: 'rgba(200,220,255,.35)', sunY: 18,
    sea: ['#16305a', '#102243', '#0a1730'], cloud: 'rgba(190,205,240,.45)',
    island: '#0d1930', haze: 'rgba(150,180,255,.14)',
  },
]

const t = computed(() => THEMES[((props.seed % THEMES.length) + THEMES.length) % THEMES.length])
const isNight = computed(() => (props.seed % THEMES.length) === 4)

// Deterministic star field so it doesn't reshuffle on every render.
const stars = computed(() => {
  let s = 1337
  const rnd = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff)
  return Array.from({ length: 60 }, () => ({
    x: +(rnd() * 100).toFixed(2),
    y: +(rnd() * 45).toFixed(2),
    r: +(0.6 + rnd() * 1.1).toFixed(2),
    d: +(rnd() * 4).toFixed(2),
  }))
})
</script>

<template>
  <div class="sea-bg" aria-hidden="true">
    <svg class="scene" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
      <defs>
        <linearGradient id="skyG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="t.sky[0]" />
          <stop offset="55%" :stop-color="t.sky[1]" />
          <stop offset="100%" :stop-color="t.sky[2]" />
        </linearGradient>
        <linearGradient id="seaG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="t.sea[0]" />
          <stop offset="50%" :stop-color="t.sea[1]" />
          <stop offset="100%" :stop-color="t.sea[2]" />
        </linearGradient>
        <radialGradient id="sunG">
          <stop offset="0%" :stop-color="t.sun" stop-opacity="1" />
          <stop offset="45%" :stop-color="t.glow" stop-opacity=".8" />
          <stop offset="100%" :stop-color="t.glow" stop-opacity="0" />
        </radialGradient>
        <!-- Paper-grain noise reused as a subtle atmospheric texture -->
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="7" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </defs>

      <rect width="1200" height="800" fill="url(#skyG)" />

      <g v-if="isNight" class="stars">
        <circle
          v-for="(s, i) in stars" :key="i"
          :cx="s.x * 12" :cy="s.y * 12" :r="s.r"
          fill="#fff" :style="{ animationDelay: s.d + 's' }" />
      </g>

      <circle :cx="880" :cy="t.sunY * 6" r="150" fill="url(#sunG)" class="sun-glow" />
      <circle :cx="880" :cy="t.sunY * 6" r="46" :fill="t.sun" class="sun-disc" />

      <!-- distant islands -->
      <g :fill="t.island" opacity=".45">
        <path class="isle isle-a" d="M-40 566 q70-58 140-30 q46-46 104-6 q56-30 96 36 z" />
        <path class="isle isle-b" d="M980 572 q54-46 110-20 q40-40 92 2 q40 20 58 18 l0 20 z" />
      </g>

      <!-- cloud bands, each drifting at its own pace -->
      <g :fill="t.cloud">
        <g class="cloud-layer cloud-slow" opacity=".55">
          <ellipse cx="180" cy="150" rx="120" ry="30" />
          <ellipse cx="260" cy="136" rx="80" ry="26" />
          <ellipse cx="760" cy="110" rx="140" ry="32" />
          <ellipse cx="860" cy="126" rx="90" ry="24" />
        </g>
        <g class="cloud-layer cloud-mid" opacity=".7">
          <ellipse cx="480" cy="210" rx="150" ry="34" />
          <ellipse cx="580" cy="192" rx="96" ry="28" />
          <ellipse cx="1080" cy="230" rx="130" ry="30" />
        </g>
        <g class="cloud-layer cloud-fast" opacity=".45">
          <ellipse cx="120" cy="300" rx="170" ry="26" />
          <ellipse cx="900" cy="320" rx="150" ry="22" />
        </g>
      </g>

      <!-- horizon haze softens the sky/sea seam -->
      <rect y="536" width="1200" height="70" :fill="t.haze" />

      <rect y="576" width="1200" height="224" fill="url(#seaG)" />

      <!-- wave crests: three bands sliding at different speeds -->
      <g class="waves" fill="#ffffff">
        <path class="wave wave-1" opacity=".14"
          d="M0 608 q60-16 120 0 t120 0 t120 0 t120 0 t120 0 t120 0 t120 0 t120 0 t120 0 t120 0 v40 H0 z" />
        <path class="wave wave-2" opacity=".10"
          d="M0 652 q80-20 160 0 t160 0 t160 0 t160 0 t160 0 t160 0 t160 0 v46 H0 z" />
        <path class="wave wave-3" opacity=".07"
          d="M0 706 q100-24 200 0 t200 0 t200 0 t200 0 t200 0 t200 0 v60 H0 z" />
      </g>

      <!-- a ship on the horizon and a few birds, for scale and life -->
      <g class="ship" :fill="t.island" opacity=".7">
        <path d="M556 574h44l-6 12h-32z" />
        <path d="M578 574V536l26 14-26 8z" />
        <path d="M578 552l-22 8 22 10z" opacity=".85" />
      </g>
      <g class="birds" :stroke="t.island" fill="none" stroke-width="2.4" opacity=".5">
        <path class="bird bird-1" d="M300 250q7-7 14 0q7-7 14 0" />
        <path class="bird bird-2" d="M348 232q6-6 12 0q6-6 12 0" />
        <path class="bird bird-3" d="M262 274q5-5 10 0q5-5 10 0" />
      </g>

      <rect width="1200" height="800" filter="url(#grain)" opacity=".05" style="mix-blend-mode:overlay" />
    </svg>
    <div class="vignette"></div>
    <div class="scrim"></div>
  </div>
</template>

<style scoped>
.sea-bg {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
}
.scene { width: 100%; height: 100%; display: block; }

.vignette {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% 36%, rgba(0,0,0,.10) 0%, transparent 42%),
    radial-gradient(ellipse at 50% 45%, transparent 38%, rgba(0, 0, 0, .42) 100%);
  pointer-events: none;
}

/* Darkens the column the UI sits in so parchment always has contrast,
   without flattening the scene at the edges. */
.scrim {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg,
    rgba(20, 14, 40, .34) 0%,
    rgba(20, 14, 40, .26) 45%,
    rgba(20, 14, 40, .10) 70%,
    transparent 100%);
}

.ship { animation: sail 26s ease-in-out infinite; }
@keyframes sail {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  50% { transform: translate(26px, -3px) rotate(1.2deg); }
}
.bird { animation: flap 3.2s ease-in-out infinite; transform-origin: center; }
.bird-2 { animation-delay: .5s; }
.bird-3 { animation-delay: 1.1s; }
@keyframes flap {
  0%, 100% { transform: translateY(0) scaleY(1); }
  50% { transform: translateY(-5px) scaleY(.65); }
}

.sun-glow { animation: pulse 9s ease-in-out infinite; transform-origin: 880px center; }
@keyframes pulse {
  0%, 100% { opacity: .85; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.07); }
}

.cloud-layer { will-change: transform; }
.cloud-slow { animation: drift 90s linear infinite; }
.cloud-mid { animation: drift 62s linear infinite; }
.cloud-fast { animation: drift 40s linear infinite; }
@keyframes drift {
  from { transform: translateX(-320px); }
  to { transform: translateX(1320px); }
}

.wave { will-change: transform; }
.wave-1 { animation: swell 11s ease-in-out infinite; }
.wave-2 { animation: swell 15s ease-in-out infinite reverse; }
.wave-3 { animation: swell 19s ease-in-out infinite; }
@keyframes swell {
  0%, 100% { transform: translateX(0) translateY(0); }
  50% { transform: translateX(-60px) translateY(5px); }
}

.isle { animation: bob 14s ease-in-out infinite; }
.isle-b { animation-duration: 18s; animation-direction: reverse; }
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(3px); }
}

.stars circle { animation: twinkle 3.4s ease-in-out infinite; }
@keyframes twinkle {
  0%, 100% { opacity: .25; }
  50% { opacity: .95; }
}

@media (prefers-reduced-motion: reduce) {
  .sun-glow, .cloud-layer, .wave, .isle, .stars circle, .ship, .bird { animation: none; }
}
</style>
