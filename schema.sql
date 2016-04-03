drop table if exists articles;
create table articles (
  id integer primary key autoincrement,
  url text not null,
  title text not null,
  description text,
  image text,
  text text
);

create table translations (
  id integer primary key autoincrement,
  term text not null,
  translation text not null
);
