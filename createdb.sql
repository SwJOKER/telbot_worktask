CREATE TABLE users(
	user_id integer PRIMARY KEY
);

CREATE TABLE unions(
	union_id integer PRIMARY KEY AUTOINCREMENT,
	name varchar(255),
	rebate decimal,
	user_id integer,
	FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE clubs(
	club_id integer PRIMARY KEY AUTOINCREMENT,
	name varchar(255),
	comission decimal,
	participate bool,
	union_id integer,
	FOREIGN KEY(union_id) REFERENCES unions(union_id)
);

	