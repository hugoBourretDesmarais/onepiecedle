<script setup>
// Drawn as SVG rather than styled HTML: the wordmark needs three stacked
// strokes, a per-letter gradient, a gloss sweep and a grain wash, which
// text-shadow stacking can't express cleanly.
const WORD = 'NEPIECEDLE'
const LETTERS = [...WORD]

// Alternating warm/cool, matching the original's red-and-blue wordmark.
const fillFor = i => (i % 2 === 0 ? 'url(#gRed)' : 'url(#gBlue)')
</script>

<template>
  <h1 class="logo" aria-label="OnePieceDle">
    <span class="mark" aria-hidden="true">
      <svg viewBox="0 0 100 100">
        <defs>
          <radialGradient id="markDisc" cx="38%" cy="30%" r="78%">
            <stop offset="0%" stop-color="#4a4a52" />
            <stop offset="55%" stop-color="#1d1d24" />
            <stop offset="100%" stop-color="#0b0b10" />
          </radialGradient>
          <linearGradient id="hatG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#ffe08a" />
            <stop offset="55%" stop-color="#f0bf4c" />
            <stop offset="100%" stop-color="#cf9526" />
          </linearGradient>
          <linearGradient id="ringG" x1="0" y1="0" x2="0.4" y2="1">
            <stop offset="0%" stop-color="#fffdf4" />
            <stop offset="100%" stop-color="#d9c69a" />
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="48" fill="url(#ringG)" />
        <circle cx="50" cy="50" r="43" fill="url(#markDisc)" />
        <ellipse cx="37" cy="27" rx="23" ry="13" fill="#fff" opacity=".09" />

        <!-- crossed bones sit behind the skull -->
        <g fill="#fdfaf0" transform="rotate(-24 50 62)">
          <rect x="12" y="58.4" width="76" height="7.4" rx="3.7" />
          <circle cx="12" cy="56.6" r="4.9" /><circle cx="12" cy="67.6" r="4.9" />
          <circle cx="88" cy="56.6" r="4.9" /><circle cx="88" cy="67.6" r="4.9" />
        </g>
        <g fill="#fdfaf0" transform="rotate(24 50 62)">
          <rect x="12" y="58.4" width="76" height="7.4" rx="3.7" />
          <circle cx="12" cy="56.6" r="4.9" /><circle cx="12" cy="67.6" r="4.9" />
          <circle cx="88" cy="56.6" r="4.9" /><circle cx="88" cy="67.6" r="4.9" />
        </g>

        <!-- skull: cranium plus a narrower jaw -->
        <path
          d="M50 30c-13.5 0-22.5 9.2-22.5 20.8 0 6.4 3 11 6.6 13.8 1.3 1 2 2.4 2 4v3.1c0 2 1.7 3.6 3.9 3.6h20c2.2 0 3.9-1.6 3.9-3.6v-3.1c0-1.6.7-3 2-4 3.6-2.8 6.6-7.4 6.6-13.8C72.5 39.2 63.5 30 50 30z"
          fill="#fdfaf0" />
        <ellipse cx="41.4" cy="50.6" rx="6" ry="6.9" fill="#12121a" />
        <ellipse cx="58.6" cy="50.6" rx="6" ry="6.9" fill="#12121a" />
        <path d="M50 57.6l-3 5.6h6z" fill="#12121a" />
        <g fill="#12121a">
          <rect x="43.4" y="66.4" width="2.6" height="5.6" rx="1.1" />
          <rect x="48.7" y="66.4" width="2.6" height="5.6" rx="1.1" />
          <rect x="54" y="66.4" width="2.6" height="5.6" rx="1.1" />
        </g>

        <!-- straw hat: wide brim resting on the cranium, red band across it -->
        <path d="M31.5 33.5c0-8.6 8.2-14.8 18.5-14.8s18.5 6.2 18.5 14.8z" fill="url(#hatG)" />
        <path d="M31.5 33.5c0-8.6 8.2-14.8 18.5-14.8" fill="none" stroke="#fff" stroke-width="1.6" opacity=".35" />
        <path d="M31.2 31.2h37.6v6.2H31.2z" fill="#d4423f" />
        <path d="M31.2 31.2h37.6v1.8H31.2z" fill="#fff" opacity=".3" />
        <ellipse cx="50" cy="37.4" rx="34" ry="7.6" fill="url(#hatG)" />
        <ellipse cx="50" cy="36.2" rx="34" ry="7.6" fill="#ffe9a6" opacity=".45" />
        <path d="M16 37.4a34 7.6 0 0 0 68 0" fill="none" stroke="#b9812a" stroke-width="1.4" opacity=".55" />
      </svg>
    </span>

    <svg class="word" viewBox="0 0 760 150" aria-hidden="true">
      <defs>
        <linearGradient id="gRed" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#ff8b6b" />
          <stop offset="34%" stop-color="#ef4235" />
          <stop offset="72%" stop-color="#c8202a" />
          <stop offset="100%" stop-color="#95101f" />
        </linearGradient>
        <linearGradient id="gBlue" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#8fc4ff" />
          <stop offset="34%" stop-color="#3f7ee0" />
          <stop offset="72%" stop-color="#2352b4" />
          <stop offset="100%" stop-color="#13317a" />
        </linearGradient>
        <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#fff" stop-opacity=".85" />
          <stop offset="42%" stop-color="#fff" stop-opacity=".22" />
          <stop offset="46%" stop-color="#fff" stop-opacity="0" />
        </linearGradient>

        <!-- speckled grain, masked to the letters, so the fill isn't flat -->
        <filter id="speck" x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="4" seed="11" />
          <feColorMatrix type="saturate" values="0" />
          <feComponentTransfer><feFuncA type="linear" slope=".55" /></feComponentTransfer>
        </filter>

        <filter id="cast" x="-15%" y="-25%" width="130%" height="160%">
          <feDropShadow dx="0" dy="6" stdDeviation="5" flood-color="#000" flood-opacity=".45" />
          <feDropShadow dx="0" dy="2" stdDeviation="1" flood-color="#000" flood-opacity=".35" />
        </filter>

        <mask id="wordMask">
          <text class="t" x="380" y="112" text-anchor="middle" fill="#fff">{{ WORD }}</text>
        </mask>
      </defs>

      <g :filter="'url(#cast)'">
        <!-- 1. dark outer keyline -->
        <text class="t" x="380" y="112" text-anchor="middle"
          fill="none" stroke="#141c33" stroke-width="21" stroke-linejoin="round">{{ WORD }}</text>
        <!-- 2. cream band -->
        <text class="t" x="380" y="112" text-anchor="middle"
          fill="none" stroke="#fff6e2" stroke-width="12" stroke-linejoin="round">{{ WORD }}</text>
        <!-- 3. per-letter gradient fill -->
        <text class="t" x="380" y="112" text-anchor="middle">
          <tspan v-for="(ch, i) in LETTERS" :key="i" :fill="fillFor(i)">{{ ch }}</tspan>
        </text>
      </g>

      <!-- grain + gloss, both clipped to the glyphs -->
      <g mask="url(#wordMask)">
        <rect x="0" y="0" width="760" height="150" filter="url(#speck)" opacity=".16"
          style="mix-blend-mode: multiply" />
        <rect x="0" y="0" width="760" height="150" fill="url(#gloss)" />
      </g>
    </svg>

    <span class="sr">OnePieceDle</span>
  </h1>
</template>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin: 4px 0 0;
  width: min(600px, calc(100% - 14px));
  max-width: 100%;
  user-select: none;
}

.mark {
  width: clamp(48px, 14%, 100px);
  flex: none;
  margin: 0 -1.5% 0 0;
  filter: drop-shadow(0 5px 6px rgba(0, 0, 0, .45));
  animation: mark-in .6s cubic-bezier(.2, .9, .3, 1.5) both, sway 6s ease-in-out 1.1s infinite;
}
.mark svg { width: 100%; height: auto; display: block; }

.word {
  flex: 1;
  height: auto;
  overflow: visible;
  animation: word-in .55s cubic-bezier(.2, .85, .3, 1.35) both .1s;
}
.t {
  font-family: 'Lilita One', cursive;
  font-size: 118px;
  letter-spacing: 1px;
  paint-order: stroke fill;
}

.sr {
  position: absolute;
  width: 1px; height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
}

@keyframes mark-in {
  from { transform: scale(.35) rotate(-45deg); opacity: 0; }
  to { transform: none; opacity: 1; }
}
@keyframes word-in {
  from { transform: translateY(-14px) scale(.94); opacity: 0; }
  to { transform: none; opacity: 1; }
}
@keyframes sway {
  0%, 100% { transform: rotate(-3deg); }
  50% { transform: rotate(3deg); }
}

@media (prefers-reduced-motion: reduce) {
  .mark, .word { animation: none; }
}
</style>
