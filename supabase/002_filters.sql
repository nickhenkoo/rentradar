create table if not exists filters (
  id         uuid primary key default gen_random_uuid(),
  user_id    bigint not null references users(id) on delete cascade,
  label      text,
  city       text not null,
  district   text,
  price_min  integer,
  price_max  integer,
  rooms_min  integer,
  rooms_max  integer,
  area_min   integer,
  is_active  boolean not null default true,
  created_at timestamptz not null default now()
);

create index if not exists filters_user_id_idx on filters(user_id);
create index if not exists filters_active_idx on filters(is_active) where is_active = true;
