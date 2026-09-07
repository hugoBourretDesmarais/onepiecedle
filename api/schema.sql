-- Solve counter: one row per (game day, spoiler limit), incremented on a
-- verified solve. Kept separate from players so the counter works for people
-- who never sign up.
CREATE TABLE IF NOT EXISTS solves (
  day         TEXT NOT NULL,
  arc_limit   TEXT NOT NULL DEFAULT '',
  count       INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, arc_limit)
);

-- One counted solve per address per day, so the tally reads as "people" and
-- the daily write count stays bounded. The address is salted and hashed; the
-- raw IP is never stored.
-- Keyed per bucket, not just per day: each (day, arc_limit) is its own tally,
-- so one address must be able to count once in each bucket it solves.
CREATE TABLE IF NOT EXISTS counted (
  day       TEXT NOT NULL,
  arc_limit TEXT NOT NULL DEFAULT '',
  ip_hash   TEXT NOT NULL,
  PRIMARY KEY (day, arc_limit, ip_hash)
);

-- Players claim a pseudonym and get a recovery code; the code's hash is what
-- we store, so a database leak cannot be replayed as a login.
CREATE TABLE IF NOT EXISTS players (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  name_key    TEXT NOT NULL UNIQUE,   -- lowercased, for case-insensitive uniqueness
  code_hash   TEXT NOT NULL,
  created_at  TEXT NOT NULL,
  last_seen   TEXT NOT NULL
);

-- One row per player per game day. Re-solving the same day (e.g. after
-- changing the spoiler limit) updates in place rather than inserting, which
-- keeps the daily write count bounded.
CREATE TABLE IF NOT EXISTS results (
  player_id   TEXT NOT NULL,
  day         TEXT NOT NULL,
  arc_limit   TEXT NOT NULL DEFAULT '',
  guesses     INTEGER NOT NULL,
  solved_at   TEXT NOT NULL,
  PRIMARY KEY (player_id, day),
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

-- Denormalised standings so the leaderboard is a single indexed scan rather
-- than an aggregate over every result row (D1 free tier bills row reads).
CREATE TABLE IF NOT EXISTS standings (
  player_id     TEXT PRIMARY KEY,
  wins          INTEGER NOT NULL DEFAULT 0,
  total_guesses INTEGER NOT NULL DEFAULT 0,
  streak        INTEGER NOT NULL DEFAULT 0,
  max_streak    INTEGER NOT NULL DEFAULT 0,
  last_win_day  TEXT,
  FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_standings_wins ON standings(wins DESC);
CREATE INDEX IF NOT EXISTS idx_standings_streak ON standings(max_streak DESC);
CREATE INDEX IF NOT EXISTS idx_results_day ON results(day, guesses);
