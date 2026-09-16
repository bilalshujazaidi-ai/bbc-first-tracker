#!/usr/bin/env python3
"""One-off: backfill first_seen/last_seen dates from the old tracker's history.

Reads backfill_corrections.json (existing shows, fix first_seen only) and
backfill_inserts.json (shows that had already left by the time this new
system took over, full rows) and applies them to Supabase. Meant to be run
once, then deleted along with its data files.
"""
import json
import os
import sys
import urllib.error
import urllib.request


def post(supabase_url, service_key, rows, extra_headers=None):
    if not rows:
        return
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/shows?on_conflict=id",
        data=json.dumps(rows).encode(),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"  OK (HTTP {resp.status}), {len(rows)} rows")
    except urllib.error.HTTPError as e:
        print(f"  FAILED: {e.code} {e.read().decode()}")
        sys.exit(1)


def main():
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    service_key = os.environ["SUPABASE_SERVICE_KEY"]

    with open("backfill_corrections.json") as f:
        corrections = json.load(f)
    with open("backfill_inserts.json") as f:
        inserts = json.load(f)

    print(f"Applying {len(corrections)} first_seen corrections...")
    post(supabase_url, service_key, corrections)

    print(f"Inserting {len(inserts)} departed shows from history...")
    post(supabase_url, service_key, inserts)

    print("Backfill complete.")


if __name__ == "__main__":
    main()
