--create table for Books
CREATE TABLE IF NOT EXISTS books(
	id SERIAL PRIMARY KEY,
	isbn VARCHAR NOT NULL,
	title VARCHAR NOT NULL,
	author VARCHAR NOT NULL,
	year INTEGER NOT NULL
);

--create table for users
CREATE TABLE IF NOT EXISTS users(
	user_id SERIAL PRIMARY KEY,
	username VARCHAR NOT NULL,
	password VARCHAR NOT NULL
);

--create table for Reviews
CREATE TABLE IF NOT EXISTS reviews(
	review_id SERIAL PRIMARY KEY,
	review VARCHAR NOT NULL,
	rating INTEGER NOT NULL,
	book_id INTEGER REFERENCES books(id),
	user_id INTEGER REFERENCES users(user_id)
);
