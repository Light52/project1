import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("home.html")

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/register/success", methods = ["POST"])
def first_register():
	"""First time register - insert into table."""
	username = request.form.get("username")
	password = request.form.get("password")
	query = db.execute("SELECT * FROM users \
					WHERE username = :username",
					{"username": username})

	#if user already exists, do not insert into table.
	if query.rowcount != 0:
		return render_template("error.html", message="Username already exists, please go to login page and login instead.")

	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
		{"username": username, "password": password})
	db.commit()
	return render_template("success.html")

@app.route("/search", methods=["POST", "GET"])
def search():
	"""return the search page, after validating user login info."""
	# TODO: add search function linking to /books
	#user should be coming after the login page - check if user has logged in successfully.
	username = request.form.get("username")
	password = request.form.get("password")
	query = db.execute("SELECT * FROM users \
					WHERE username = :username AND \
					password = :password",
					{"username": username, "password": password})
	#if username and password do not match, return error.
	if query.rowcount == 0:
		return render_template("error.html", message="Invalid username or password. Please register a new account if necessary.")
	user = query.fetchall()
	return render_template("search.html", user = user)

@app.route("/books", methods=["POST"])
def books():
	"""Lists books from search."""

	#info from form
	isbn = request.form.get("isbn")
	title = request.form.get("title")
	author = request.form.get("author")
	query = db.execute("SELECT * FROM books \
				WHERE LOWER(title) LIKE LOWER(CONCAT('%', :title, '%')) AND \
				LOWER(isbn) LIKE LOWER(CONCAT('%', :isbn, '%')) AND \
				LOWER(author) LIKE LOWER(CONCAT('%', :author, '%'))",
				{"title": title, "isbn": isbn, "author": author})

	#if search returns no results
	if query.rowcount == 0:
		return render_template("error.html", message = "No book matches the search criteria. Please try again.")
	books = query.fetchall()
	return render_template("books.html", books=books)

@app.route("/books/<string:book_id>")
def book(book_id):
	"""Lists details about a single book."""

	#Ensure book exists.
	book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
	if book is None:
		return render_template("error.html", message="No such book.")

	#return results from Good Reads API
	res = requests.get("https://www.goodreads.com/book/review_counts.json",
	params = {"key": "vcnuyAAHLVhYg4R2pNJjw", "isbns":"9781632168146"})
	data = res.json()
	num_ratings = data["books"][0]["work_ratings_count"]
	avg_rating = data["books"][0]["average_rating"]
	#Return book details
	return render_template("book.html", book=book, num_ratings=num_ratings, avg_rating=avg_rating)
	# TODO: add in section returning results from API.
	# TODO: add in section to incorporate if any reviews/ratings from my site
