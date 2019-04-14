Table players {
  id      bigint [pk]
  discord varchar [not null]
  roll20  varchar [not null]
}

Table campaigns {
  guild bigint [ref: > guilds.pkey]
  gm    bigint [ref: > players.pkey]
  url   varchar [not null]
  key   varchar [not null]
  id    bigint [pk]
}

Table guilds {
  id       bigint [pk]
  guild    varchar [not null]
  campaign bigint [ref: > campaigns.pkey]
}

Table channels {
  id       bigint [pk]
  channel  varchar [not null]
  guild    bigint [ref: > guilds.pkey]
  campaign bigint [ref: > campaigns.pkey]
}
