-- schema.sql is all CREATE TABLE IF NOT EXISTS, so it cannot alter a database
-- that already exists. Changes to a live schema go here instead, one numbered
-- file per change, applied in order:
--   npx wrangler d1 execute onepiecedle --remote --file=./migrations/<file>.sql

ALTER TABLE standings ADD COLUMN last_arc_limit TEXT NOT NULL DEFAULT '';

UPDATE standings SET last_arc_limit = COALESCE(
  (SELECT arc_limit FROM results r WHERE r.player_id = standings.player_id
   ORDER BY day DESC LIMIT 1), '');
