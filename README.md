# BBC First Arrivals Tracker

Daily-scraped record of what's on BBC First's "New Dramas" page, with the date
each title was first spotted. Runs entirely on GitHub Actions + Supabase —
no laptop, no Claude session, no permission prompts required after setup.

## How it works

- `.github/workflows/scrape.yml` first fires at 10am UK time (09:00 UTC,
  shifts to 9am UK once GMT starts in late October), then every 30 minutes
  for the rest of the day as retries, on GitHub's own servers. GitHub's
  `cron` trigger is "best effort" and occasionally skips a firing entirely,
  so rather than rely on one exact time, today's scrape gets ~30 chances to
  land.
- `scripts/scrape.py` checks first whether today's data is already recorded
  and exits immediately if so — so once one firing succeeds, every later one
  that day is a no-op costing under a second. If the actual scrape fails
  (BBC unreachable, bad response), the workflow retries it 5 times, 60
  seconds apart, before giving up for that firing (the next firing 30
  minutes later tries again from scratch).
- The script fetches BBC's public catalogue API and upserts it into a
  Supabase table called `shows`. Existing shows get their `last_seen` date
  bumped; new shows get `first_seen` set to today automatically.
- `index.html` (served by GitHub Pages) reads that table with the public
  `anon` key and renders the tracker page — no server needed.

## One-time setup (only two steps left)

1. **Create the table.** Open your Supabase project → SQL Editor → New query,
   paste the contents of [`schema.sql`](schema.sql), and run it.

2. **Add the write secret.** In this repo: Settings → Secrets and variables →
   Actions → New repository secret.
   - Name: `SUPABASE_SERVICE_KEY`
   - Value: your Supabase project's `service_role` key (Project Settings →
     API → `service_role` — the *secret* one, not `anon`).

   This key is only used by the GitHub Action to write data; it's never
   included in the public page.

That's it. The workflow also has a "Run workflow" button (Actions tab) if you
want to trigger the first scrape manually instead of waiting for the schedule.

## Viewing it

Enable GitHub Pages for this repo (Settings → Pages → Source: `main` branch,
`/ (root)`), then the tracker is live at:

`https://bilalshujazaidi-ai.github.io/bbc-first-tracker/`
