create table if not exists users (
  id            bigint primary key,
  username      text,
  first_name    text,
  language      text not null default 'en',
  is_subscribed boolean not null default false,
  subscribed_at timestamptz,
  expires_at    timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_updated_at
  before update on users
  for each row execute function update_updated_at();
