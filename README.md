# OnePieceDle (fan recreation)

A recreation of the [onepiecedle.net](https://onepiecedle.net) **classic** mode: guess the daily One Piece
character, one guess at a time, using colour-coded property comparisons.

Built with Vue 3 + Vite. Fully responsive — all nine columns fit on a phone screen.

## Differences from the original

- **266 characters** instead of 193 — the original roster plus the characters it is missing
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
| 🟧 Orange | partial match (some overlap — e.g. one shared Haki type, or a related Devil Fruit family) |
| 🟥 Red | no overlap |

`Last Bounty`, `Height` and `First Arc` also show ▲/▼ arrows pointing toward the hidden character's value.

Clues unlock as you guess: **First Appearance** (chapter/episode) after 5 tries, **Devil Fruit** (fruit name)
after 8. The daily character resets at local midnight; stats live in `localStorage`.

📊 tracks classic and practice separately — games played, wins, win rate, total guesses, average
guesses per win, best game, the guesses-per-win distribution and your five most-guessed characters.
Classic additionally tracks streaks; a streak counts **consecutive days** won, so missing a day resets
it to zero, and winning a second daily on the same day (by changing the spoiler limit) doesn't inflate it.

## Data pipeline

Character data is generated from the wiki, not hand-written. The scripts live in `tools/`:

```bash
python3 tools/fetch_wiki.py         # pull infoboxes + haki categories -> tools/out/characters.draft.json
python3 tools/dump_dossiers.py      # per-character source excerpts for review
python3 tools/download_portraits.py # portraits -> public/portraits/
python3 tools/build_dataset.py      # merge + validate -> src/data/characters.json
```

`tools/roster.json` is the character list. `tools/out/corrections.json` holds the reviewed field
overrides that `build_dataset.py` merges over the raw parse; `tools/out/final_report.txt` reports the
resulting value vocabularies and anything that needed attention.

## Backend (solve counter)

`api/` is a Cloudflare Worker backed by a D1 database. It powers the
“N people already found out!” counter under the daily puzzle.

The worker recomputes the day's answer itself from a generated copy of the dataset, and only
counts a solve whose submitted name matches — so the tally can't be inflated by anyone who
hasn't actually solved it. One count per address per `(day, spoiler limit)` bucket; the address
is salted with a Worker secret and hashed, never stored.

```bash
node api/tools/gen_data.mjs                          # after changing characters.json / arcs.json
cd api && npx wrangler d1 execute onepiecedle --remote --file=./schema.sql
cd api && npx wrangler deploy
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
