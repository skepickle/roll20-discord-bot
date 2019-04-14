Table players {
  id      bigint [pk]
  roll20  bigint
}

Table campaigns {
  id    bigint [pk]
  gm    bigint [ref: > players.id]
  url   varchar [not null]
  key   varchar [not null]
}

Table guilds {
  id       bigint [pk]
  campaign bigint [ref: > campaigns.id]
}

Table channels {
  id       bigint [pk]
  campaign bigint [ref: > campaigns.id]
}
