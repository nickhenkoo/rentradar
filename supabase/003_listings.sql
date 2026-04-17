create table if not exists listings (
  id          text primary key,
  source      text not null,
  url         text not null unique,
  title       text,
  price       integer,
  rooms       integer,
  area        integer,
  district    text,
  city        text,
  image_url   text,
  first_seen  timestamptz not null default now()
);

create index if not exists listings_city_idx on listings(city);
create index if not exists listings_first_seen_idx on listings(first_seen desc);

create table if not exists sent_alerts (
  user_id    bigint not null references users(id) on delete cascade,
  listing_id text not null references listings(id) on delete cascade,
  sent_at    timestamptz not null default now(),
  primary key (user_id, listing_id)
);
