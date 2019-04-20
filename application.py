import os
import requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = 'testapp'
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

@app.route("/register", methods = ["GET"])
def register():
	if session.get("logged_in") is not None:
		return render_template('error.html', message="Already logged in. Proceed to search, or log out then register.")
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
	if request.method == "POST":
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

		#set sessions to logged in and Username
		session["username"] = username
		session["logged_in"] = True
		session["user_id"] = user[0]["user_id"]
		return render_template("search.html")
	else:
		#if already logged in
		if session.get("logged_in") is not None:
			if session['logged_in'] == True:
				return render_template("search.html")
		else:
			return render_template("error.html", message="Not logged in. Please login to continue.")



@app.route("/books", methods=["POST"])
def books():
	"""Lists books from search."""

	#info from form
	isbn = request.form.get("isbn")
	title = request.form.get("title")
	author = request.form.get("author")
	book_query = db.execute("SELECT * FROM books \
				WHERE LOWER(title) LIKE LOWER(CONCAT('%', :title, '%')) AND \
				LOWER(isbn) LIKE LOWER(CONCAT('%', :isbn, '%')) AND \
				LOWER(author) LIKE LOWER(CONCAT('%', :author, '%'))",
				{"title": title, "isbn": isbn, "author": author})

	#if search returns no results
	if book_query.rowcount == 0:
		return render_template("error.html", message = "No book matches the search criteria. Please try again.")
	books = book_query.fetchall()

	return render_template("books.html", books=books)


@app.route("/books/<int:book_id>")
def book(book_id):
	"""Lists details about a single book."""

	#Ensure book exists.
	book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
	if book is None:
		return render_template("error.html", message="No such book.")

	#return results from Good Reads API
	res = requests.get("https://www.goodreads.com/book/review_counts.json",
	params = {"key": "vcnuyAAHLVhYg4R2pNJjw", "isbns": book["isbn"]})
	data = res.json()
	num_ratings = data["books"][0]["work_ratings_count"]
	avg_rating = data["books"][0]["average_rating"]

	#query for existing reviews:
	reviews = db.execute("SELECT * FROM reviews \
							WHERE book_id = :id",
							{"id":book_id}).fetchall()


	#Return book details
	return render_template("book.html", book=book, num_ratings=num_ratings, avg_rating=avg_rating, reviews=reviews)

@app.route("/<int:book_id>/review", methods=["POST"])
def review(book_id):
	"""Allow user to submit a review out of 5 and text if they so desire."""
	#ensure rating user submitted is an integer
	try:
		rating = int(request.form.get("num_review"))
	except ValueError:
		return render_template("error.html", message="Submit a number rating.")

	review = request.form.get("text_review")

	if rating < 1 or rating > 5:
		return render_template("error.html",message="Your rating must be between 1 and 5")
	user_id = session.get("user_id")
	#select all reviews from user for current book
	query = db.execute("SELECT * FROM reviews \
				WHERE reviews.book_id = :id AND reviews.user_id = :uid",
				{"id": book_id, "uid": user_id})

	#check if user already submitted a review for this book
	if query.rowcount != 0:
		return render_template("error.html", message="You can only submit one review per book.")

	db.execute("INSERT INTO reviews (review, rating, book_id, user_id)\
				VALUES (:review, :rating, :book_id, :user_id)",
				{"review":review, "rating":rating, "book_id":book_id, "user_id":user_id})
	db.commit()
	return render_template("review.html")

@app.route('/logout')
def logout():
	#remove user from session if exists
	session.pop('username', None)
	session.pop('logged_in', None)
	session.pop('user_id', None)
	return render_template('logout.html')

@app.route("/api/<string:isbn>")
def isbn_api(isbn):
	#make sure book exists
	query = db.execute("SELECT * FROM books \
						WHERE isbn = :isbn",
						{"isbn": isbn})
	if query.rowcount == 0:
		return jsonify({"error": "Invalid isbn"}), 404

	book = query.fetchone()

	#get data from goodreads API
	res = requests.get("https://www.goodreads.com/book/review_counts.json",
	params = {"key": "vcnuyAAHLVhYg4R2pNJjw", "isbns": book.isbn})
	data = res.json()
	num_ratings = data["books"][0]["work_ratings_count"]
	avg_rating = data["books"][0]["average_rating"]

	return jsonify({
		"title": book.title,
	    "author": book.author,
	    "year": book.year,
	    "isbn": book.isbn,
	    "review_count": num_ratings,
	    "average_score": avg_rating
	})
