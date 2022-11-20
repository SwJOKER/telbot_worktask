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

	