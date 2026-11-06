#!/usr/bin/env python3
"""One-off: fill episodes_at_first_seen from the old tracker's daily history."""
import json, os, sys, urllib.error, urllib.request

url = os.environ["SUPABASE_URL"].rstrip("/")
key = os.environ["SUPABASE_SERVICE_KEY"]
rows = json.load(open("backfill_episodes.json"))
req = urllib.request.Request(
    f"{url}/rest/v1/shows?on_conflict=id",
    data=json.dumps(rows).encode(), method="POST",
    headers={"apikey": key, "Authorization": f"Bearer {key}",
             "Content-Type": "application/json",
             "Prefer": "resolution=merge-duplicates,return=minimal"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"OK (HTTP {r.status}), {len(rows)} rows")
except urllib.error.HTTPError as e:
    print("FAILED:", e.code, e.read().decode()); sys.exit(1)
