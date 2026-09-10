# OnePieceDle (fan recreation)

A recreation of the [onepiecedle.net](https://onepiecedle.net) **classic** mode: guess the daily One Piece
character, one guess at a time, using colour-coded property comparisons.

Built with Vue 3 + Vite. Fully responsive — all nine columns fit on a phone screen.

## Differences from the original

- **268 characters** instead of 193 — the original roster plus the characters it is missing
  (Egghead / Elbaf arcs, the Five Elders, the Knights of God, Vegapunk's satellites, the Blackbeard
  and Red Hair crews, and more).
- All property data is re-derived from the [One Piece Wiki](https://onepiece.fandom.com), so bounties
  and story facts are current rather than frozen at the original app's last update.
- **Practice mode** (🎲) in addition to the daily character — replay as often as you like.
- **Character gallery** (📖) — browse the whole roster, search across name, aliases, crew, devil fruit,
  haki, origin and debut arc, and open any card for full details plus a link to its wiki page.
  Each card has a tickbox that adds or removes it from the practice pool, so you can drill a
  single crew or arc. The daily is deliberately unaffected, so it stays the same for everyone.
- Baroque Works agents show their codename alongside their real name (`Zala (Miss Doublefinger)`),
  since the codename is how readers know them.
- Unknown/unconfirmed Devil Fruit, Haki and Origin values are shown as `Unknown` / `?` rather than guessed.

- **Spoiler limit** (⚙️) — tell it how far you've read and the roster is capped to characters who have
  debuted by the end of that arc, across the daily answer, the guess suggestions and the gallery.
  Bounties rewind with it: at a Loguetown limit Luffy is worth ฿30,000,000, not ฿3,000,000,000.

⚠️ With no spoiler limit set, the data includes **current manga spoilers**.

## Play

```bash
npm install
npm run dev
```

Then open http://localhost:5173.

## How the game works

Type a character name and submit. Each guess reveals a row of tiles:

| Colour | Meaning |
| --- | --- |
| 🟩 Green | exact match |
| 🟨 Yellow | partial match (some overlap — e.g. one shared Haki type, or a related Devil Fruit family) |
| 🟥 Red | no overlap |

`Last Bounty`, `Height` and `First Arc` also show ▲/▼ arrows pointing toward the hidden character's value.

On a win the row flips one tile at a time before the result panel appears, followed by confetti;
both are skipped under `prefers-reduced-motion`.

Clues unlock as you guess: **First Appearance** (arc/episode) after 5 tries, **Devil Fruit** (fruit name)
after 8. The daily character resets at local midnight; stats live in `localStorage`.

📊 tracks classic and practice separately — games played, wins, win rate, total guesses, average
guesses per win, best game, the guesses-per-win distribution and your five most-guessed characters.
Classic additionally tracks streaks; a streak counts **consecutive days** won, so missing a day resets
it to zero, and winning a second daily on the same day (by changing the spoiler limit) doesn't inflate it.

## Look and feel

- **Backdrop** — six hand-picked landscape pieces from the wiki (Oda colour spreads and anime
  stills) rotate by date, each slowly panning. Fetched and encoded by
  `tools/download_backgrounds.py`: centre-cropped to 16:9, resized to 1920px, written as WebP
  with a JPEG fallback via CSS `image-set()`. A tint and vignette keep the UI readable over
  busy art. Append `?bg=0`–`?bg=5` to preview a specific one.
- **Wordmark** — `GameLogo.vue` is drawn entirely in SVG: the crew's Jolly Roger (gold-rimmed
  disc, skull, crossed bones, straw hat with its red band) stands in for the leading O, and the
  letters stack a dark keyline, a cream band and a per-letter gradient, then a generated wear map
  (`tools/make_textures.py` — fractal grain, speckle and directional scratches, baked to RGBA)
  tiled inside the glyphs so the fill looks weathered rather than moulded. The overlay uses plain
  alpha, not `mix-blend-mode`: the masked group is isolated, so `overlay`/`soft-light` blend
  against nothing and grey the letters out.
- **Streak flame** — `StreakFlame.vue` animates three nested tongues on offset cycles; it is
  greyed out at zero and lights up once a streak is running.
- **Paper** — panels use an inline SVG `feTurbulence` grain plus warm gradients and an inset
  shadow, so parchment scales cleanly instead of tiling like a bitmap, at no extra request.
- **Icons** — the toolbar uses a drawn SVG set (`Icon.vue`), which can be recoloured and sized;
  the three mode buttons keep their emoji (☠️ 🎲 📖) as in the original.

The backdrop pans via `background-position` rather than a transform: a transformed layer can sit
un-rasterised in a throttled tab, leaving the artwork invisible. All motion is suppressed under
`prefers-reduced-motion`.

## Data pipeline

Character data is generated from the wiki, not hand-written. The scripts live in `tools/`:

```bash
python3 tools/fetch_wiki.py         # pull infoboxes + haki categories -> tools/out/characters.draft.json
python3 tools/fetch_bounties.py     # full bounty history + reveal chapters -> tools/out/bounties.json
python3 tools/fetch_history.py      # height/haki/fruit timelines -> tools/out/history.raw.json
python3 tools/merge_history.py      # + reviewed research -> tools/out/history.json
python3 tools/dump_dossiers.py      # per-character source excerpts for review
python3 tools/download_portraits.py # portraits -> public/portraits/
python3 tools/download_pre_timeskip.py # pre-timeskip portraits -> public/portraits/*-pre.png
python3 tools/download_backgrounds.py # backdrops -> public/backgrounds/
python3 tools/make_textures.py      # wear map -> public/textures/
python3 tools/build_dataset.py      # merge + validate -> src/data/characters.json
```

`tools/roster.json` is the character list. `tools/out/corrections.json` holds the reviewed field
overrides that `build_dataset.py` merges over the raw parse; `tools/out/final_report.txt` reports the
resulting value vocabularies and anything that needed attention.

### Dating bounties

The spoiler limit needs to know *when the reader learned* each figure, not when the raise happened
in-story, so every bounty carries the chapter its wiki citation points at. Three wrinkles:

- The wiki lists bounties newest-first, and the app picks a value by scanning that list top-down for
  the first entry the reader has reached. Taking the highest chapter instead would break on
  retroactive reveals — Kaidou's rookie ฿70,000,000 surfaces in chapter 1049, long after his current
  one, and Shanks's former ฿1,040,000,000 comes from a 2022 film.
- Citations are often `{{Qref|name=...}}` back-references. Those are page-scoped, so they resolve
  against the character's own page only; a bare name like `bounty` or `infobox` means something
  different on every page.
- Most bounties past the Straw Hats' were never printed in a chapter at all — they come from the
  Vivre Card databook, an exhibition, a film or a novel. Those are dated to the chapter that was
  being serialised when that thing was published (`SOURCE_CHAPTER` in `build_dataset.py`), so the
  limit hides them until the player has read that far. `tools/out/bounty_dates.json` holds the
  handful of hand-reviewed dates for citations with no machine-readable source at all.

With no limit set, the card shows the latest bounty as before — the history only comes into play
once you cap the story.

### Dating everything else

Each character also carries a `history` block covering affiliation, haki, devil fruit, height and
portrait, resolved the same way: newest-first lists, scanned top-down for the first entry the
reader has reached. How much of it the wiki will tell you varies enormously.

- **Height** is easy — the Char Box tags its values `(debut)` / `(after timeskip)`, and the
  timeskip is chapter 598. Only eight characters actually grow.
- **Portraits** are a naming convention: `<Name> Anime Pre Timeskip Infobox.png` exists for 71 of
  the 164 characters who debut before the timeskip. The rest never changed enough for the wiki to
  bother and keep the one portrait.
- **Haki** comes from the per-type sections on the `/Abilities and Powers` pages, whose chapter
  citations give a usable first-display date — but only as a starting point, since the earliest
  citation in a section is often not the earliest display.
- **Devil fruit** defaults to the character's debut: taking the earliest citation in the Devil
  Fruit section instead would date Robin's power to chapter 629, hundreds after readers saw it.
  Review only has to catch the genuinely late reveals, like Blackbeard's in 440.
- **Affiliation is not datable at all.** The Char Box lists crews in no particular order and mostly
  without refs — Robin's own list puts Baroque Works third and undated, and Jinbe's only dated
  entry points at a chapter that has nothing to do with him. This one is researched per character.

So `fetch_history.py` scrapes what it can and everything else is reviewed, with the results merged
by `merge_history.py`. `tools/out/history_review.json` holds hand overrides for the cases neither
can express — Luffy's fruit is a plain Paramecia until the Five Elders name it in chapter 1044.

One consequence worth knowing: the affiliation vocabulary contains crews nobody currently belongs
to (`CP9`, `Buggy Pirates`, `Drake Pirates`, `Drum Kingdom`, …). Without them the early-story cards
have to reach for a successor organisation, and that leaks — labelling X Drake's debut "Marines"
gives away the cover he keeps for another 300 chapters.

Where a value can't be dated it stays hidden under a limit rather than being shown early, so a
handful of databook-only haki types read as "none" on a limited board. That matches how an
unrevealed bounty already reads as ฿0.

## Backend (solve counter + leaderboard)

`api/` is a Cloudflare Worker backed by a D1 database. It powers the
“N people already found out!” counter and the 🏆 leaderboard.

Accounts are shared with [AvatarDle](https://github.com/hugoBourretDesmarais/avatardle): its worker binds this
same D1 database, using the common `players` and `sessions` tables and its own `av_`-prefixed game
tables, and both sites keep the session under the same `dle:account` localStorage key on their
shared origin. A landing page linking the two lives at https://hugobourretdesmarais.github.io/.

Accounts are a pseudonym plus a password — no email, no third-party auth. Workers Free allows
only 10ms CPU per request, far too little for a real KDF, so the 600k-iteration PBKDF2 runs in
the browser and the server stores a salted SHA-256 of the derived key. The password therefore
never leaves the device, and a database dump isn't directly replayable. The browser holds a
session token, never the password. There is no password reset yet.

Every verified classic win is ranked, whatever the spoiler limit, and the board shows the
limit each player last won under — a capped roster is a much smaller pool, so the column is
there to make that visible rather than to exclude anyone. Streaks are derived from the
stored result days rather than incremented, so a result arriving out of order still lands
correctly, and the shown limit follows the newest day rather than the last write. Ranked
averages need 3+ wins. Local 📊 stats are per-device and deliberately separate from the ranked record —
they can't be verified, so they're never backfilled into it.

The worker recomputes the day's answer itself from a generated copy of the dataset, and only
counts a solve whose submitted name matches — so the tally can't be inflated by anyone who
hasn't actually solved it. One count per address per `(day, spoiler limit)` bucket; the address
is salted with a Worker secret and hashed, never stored.

```bash
node api/tools/gen_data.mjs                          # after changing characters.json / arcs.json
cd api && npx wrangler d1 execute onepiecedle --remote --file=./schema.sql
cd api && npx wrangler deploy
```

`schema.sql` is all `CREATE TABLE IF NOT EXISTS`, so it only ever builds a database from
empty — running it against a live one changes nothing. Changes to an existing schema go in
`api/migrations/` as numbered files, applied in order and before the deploy that needs them:

```bash
cd api && npx wrangler d1 execute onepiecedle --remote --file=./migrations/001_standings_arc_limit.sql
```

`VITE_API_URL` in `.env.production` points the site at the worker. It's a public endpoint, so
it isn't a secret. Every API call fails soft: with no `VITE_API_URL` the counter simply hides
and the game is unaffected.

## Deploying

Pushing to `main` builds and publishes to GitHub Pages via `.github/workflows/deploy.yml`.
Enable it once under **Settings → Pages → Source: GitHub Actions**.

## Credits

One Piece © Eiichiro Oda / Shueisha. Character data and portraits from the
[One Piece Wiki](https://onepiece.fandom.com) (CC BY-SA). Original game concept by
[onepiecedle.net](https://onepiecedle.net). This is a non-commercial fan project.
