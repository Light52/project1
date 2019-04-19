import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	if db.execute("SELECT * FROM books").rowcount == 0:
		f = open("books.csv")
		reader = csv.reader(f)
		#skip first row of headers
		next(reader)
		for isbn, title, author, year in reader:
			db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
					{"isbn": isbn, "title": title, "author": author, "year": year})
			print(f"Added book {title} written by {author} in {year}, isbn {isbn}.")
		db.commit()

if __name__ == "__main__":
	main()
