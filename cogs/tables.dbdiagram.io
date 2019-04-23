Table players {
  id      bigint [pk]
  roll20  bigint
}

Table guilds {
  id      bigint [pk]
  gm      bigint [ref: > players.id]
  url     varchar [not null]
  key     varchar [not null]
}

Table channels {
  id       bigint [pk]
  gm       bigint [ref: > player.id]
}
