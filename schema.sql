-- Run this once in the Supabase SQL Editor (Project → SQL Editor → New query)
-- to set up the table this tracker uses.

create table if not exists shows (
  id uuid primary key,
  title text not null,
  episodes integer,
  channel text,
  end_date timestamptz,
  first_seen date not null default current_date,
  last_seen date not null default current_date
);

alter table shows enable row level security;

-- Anyone with the public "anon" key can read (the tracker page needs this).
-- No insert/update/delete policy is defined for anon, so only the secret
-- service_role key (used by the GitHub Action, never exposed publicly)
-- can write to this table.
create policy "public read access" on shows
  for select
  using (true);
