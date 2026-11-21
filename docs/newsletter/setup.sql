-- Killed by AI newsletter: subscriber list. Paste this whole file into the Supabase SQL editor and press Run.
-- Running it twice is safe.
--
-- How it is locked down: row level security is on and the table has no policies, so the public (publishable) key
-- cannot read or write it. The website can only call the two functions at the bottom, which add or remove one
-- address at a time and never return anything about who is on the list. You read the list in the dashboard
-- (Table Editor > subscribers), which is your admin view.

create table if not exists public.subscribers (
  id uuid primary key default gen_random_uuid(),
  email text not null unique check (email = lower(email) and char_length(email) between 6 and 254),
  status text not null default 'subscribed' check (status in ('subscribed', 'unsubscribed')),
  source text,                                     -- the page the form was on, e.g. /layoffs/
  consent text not null,                           -- the wording shown next to the form at signup
  token uuid not null default gen_random_uuid(),   -- for one-click unsubscribe and confirmation links later
  confirmed_at timestamptz,                        -- filled once confirmation emails exist
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unsubscribed_at timestamptz
);
create index if not exists subscribers_created_at_idx on public.subscribers (created_at desc);
alter table public.subscribers enable row level security;
revoke all on table public.subscribers from anon, authenticated;

-- Admin view: signups per day.
create or replace view public.subscriber_stats with (security_invoker = true) as
select created_at::date as day,
       count(*) as signups,
       count(*) filter (where status = 'subscribed') as still_subscribed,
       count(*) filter (where status = 'unsubscribed') as unsubscribed
from public.subscribers
group by 1
order by 1 desc;
revoke all on table public.subscriber_stats from anon, authenticated;

-- Called by the signup form. p_website is a hidden field people never see; bots fill it in and are ignored.
create or replace function public.newsletter_subscribe(p_email text, p_source text default null, p_website text default null)
returns json
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_email text := lower(btrim(coalesce(p_email, '')));
  v_recent integer;
begin
  if btrim(coalesce(p_website, '')) <> '' then
    return json_build_object('ok', true);
  end if;
  if char_length(v_email) not between 6 and 254 or v_email !~ '^[^[:space:]@]+@[a-z0-9-]+(\.[a-z0-9-]+)+$' then
    return json_build_object('ok', false, 'error', 'email');
  end if;
  -- flood guard that stores no IP addresses: refuse when signups arrive faster than a real audience sends them
  select count(*) into v_recent from public.subscribers where created_at > now() - interval '1 minute';
  if v_recent > 40 then
    return json_build_object('ok', false, 'error', 'busy');
  end if;
  insert into public.subscribers (email, source, consent)
  values (v_email, left(p_source, 120), 'One email a week. Unsubscribe any time.')
  on conflict (email) do update
    set status = 'subscribed', unsubscribed_at = null, updated_at = now(), source = excluded.source
    where public.subscribers.status <> 'subscribed';
  return json_build_object('ok', true);
end;
$$;

-- Called by the "leave the list" form. Answers ok whether or not the address was on the list.
create or replace function public.newsletter_unsubscribe(p_email text)
returns json
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.subscribers
     set status = 'unsubscribed', unsubscribed_at = now(), updated_at = now()
   where email = lower(btrim(coalesce(p_email, ''))) and status = 'subscribed';
  return json_build_object('ok', true);
end;
$$;

revoke all on function public.newsletter_subscribe(text, text, text) from public;
revoke all on function public.newsletter_unsubscribe(text) from public;
grant execute on function public.newsletter_subscribe(text, text, text) to anon, authenticated;
grant execute on function public.newsletter_unsubscribe(text) to anon, authenticated;
