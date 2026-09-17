#!/usr/bin/env python3
"""Fetch BBC First's 'New Dramas' catalogue and upsert it into Supabase.

Reads SUPABASE_URL and SUPABASE_SERVICE_KEY from the environment (set as
GitHub Actions secrets). Writes nothing if the fetch fails or looks empty,
so a bad run can never overwrite good data with junk.

Runs every 30 minutes via GitHub Actions (see scrape.yml) but is a no-op
once a run has succeeded for today — this is what makes the schedule
self-healing: GitHub's cron trigger is only "best effort" and occasionally
skips a firing entirely, so instead of relying on one scheduled time,
today's data gets ~48 chances to land, and every run after the first
successful one exits in under a second.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

BBC_API_URL = (
    "https://player.bbc.com/api/client/v1/content/page"
    "?id=2907dff2-f7ec-4f0c-ab64-54807e084c83"
    "&path=2907dff2-f7ec-4f0c-ab64-54807e084c83"
    "&viewAll=2907dff2-f7ec-4f0c-ab64-54807e084c83"
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_nodes():
    req = urllib.request.Request(BBC_API_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["page"]["sections"][0]["collection"]["nodes"]


def already_scraped_today(supabase_url, service_key, today):
    """True if any row already has last_seen = today, meaning an earlier
    firing today (this workflow runs every 30 minutes as a safety net
    against GitHub's scheduler occasionally skipping a trigger) already
    succeeded. Lets every run stay a cheap no-op once one has landed."""
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/shows?select=id&last_seen=eq.{today}&limit=1",
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return len(json.load(resp)) > 0


def main():
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    service_key = os.environ["SUPABASE_SERVICE_KEY"]
    today = datetime.date.today().isoformat()

    if already_scraped_today(supabase_url, service_key, today):
        print(f"Already recorded for {today} — nothing to do.")
        return

    nodes = fetch_nodes()
    if not nodes:
        print("No shows found in the BBC response — aborting without writing.")
        sys.exit(1)

    rows = [
        {
            "id": n["id"],
            "title": n["name"],
            "episodes": n.get("episodeCount"),
            "channel": n.get("channel"),
            "end_date": n.get("end"),
            "last_seen": today,
        }
        for n in nodes
    ]

    body = json.dumps(rows).encode()
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/shows?on_conflict=id",
        data=body,
        method="POST",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
    except urllib.error.HTTPError as e:
        print(f"Supabase upsert failed: {e.code} {e.read().decode()}")
        sys.exit(1)

    print(f"Upsert OK (HTTP {status}). Recorded {len(rows)} shows for {today}.")


if __name__ == "__main__":
    main()
