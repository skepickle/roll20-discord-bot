Table players {
  id      int [pk]
  discord varchar [not null]
  roll20  varchar [not null]
}

Table campaigns {
  guild int [ref: > guilds.pkey]
  gm    int [ref: > players.pkey]
  url   varchar [not null]
  key   varchar [not null]
  id    int [pk]
}

Table guilds {
  id       int [pk]
  guild    varchar [not null]
  campaign int [ref: > campaigns.pkey]
}

Table channels {
  id       int [pk]
  channel  varchar [not null]
  guild    int [ref: > guilds.pkey]
  campaign int [ref: > campaigns.pkey]
}
