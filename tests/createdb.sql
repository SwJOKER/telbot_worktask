CREATE TABLE users(
	id integer PRIMARY KEY
);

CREATE TABLE unions(
	id integer PRIMARY KEY AUTOINCREMENT,
	name varchar(255),
	rebate decimal,
	user_id integer,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE clubs(
	id integer PRIMARY KEY AUTOINCREMENT,
	name varchar(255),
	comission decimal,
	participate bool,
	union_id integer,
	FOREIGN KEY(union_id) REFERENCES unions(id) ON DELETE CASCADE
);


-- users
insert into "users" ("id") values
(123),
(133191215);


-- unions
insert into "unions" ("id", "name", "rebate", "user_id") values
(2, 'Коммунисты', 2, 133191215),
(3, 'Демократы', 2, 133191215),
(4, 'Бездельники', 228, 133191215),
(5, 'Технократы', 2, 133191215),
(6, 'Либералы', 1, 133191215);


insert into "clubs" ("id", "name", "comission", "participate", "union_id") values
(5, 'Крокодил', 6, 1, 2),
(6, 'Антилопа', 3, 1, 3),
(7, 'Лев', 3, 0, 3),
(8, 'Слон', 5, 1, 4),
(9, 'Мышь', 3, 1, 5),
(10, 'Собака', 6, 1, 6),
(12, 'Бигемот', 45, 1, 2),
(13, 'Кошка', 5, 1, 2),
(14, 'Крыса', 34, 1, 2),
(15, 'Ленивец', 54, 1, 6),
(16, 'Крыса', 7, 1, 5);





	