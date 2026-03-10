from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect
from database import cursor, db

app = Flask(__name__)


# Home Dashboard
@app.route("/")
def home():

    # Books list
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
    issued_books = cursor.fetchone()[0]

    # Issued books with status
    cursor.execute("""
        SELECT id, book_id, student_name, issue_date, return_date,
        CASE
            WHEN return_date IS NOT NULL THEN 'Returned'
            WHEN return_date IS NULL AND due_date < CURDATE() THEN 'Overdue'
            ELSE 'Issued'
        END AS status
        FROM issued_books
    """)
    issued = cursor.fetchall()

    # Overdue books
    cursor.execute("""
    SELECT id, book_id, student_name, issue_date, due_date,
    DATEDIFF(CURDATE(), due_date) AS late_days,
    DATEDIFF(CURDATE(), due_date) * 5 AS fine
    FROM issued_books
    WHERE return_date IS NULL
    AND due_date < CURDATE()
    """)

    overdue = cursor.fetchall()

    return render_template(
        "index.html",
        books=books,
        issued=issued,
        overdue=overdue,
        total_books=total_books,
        issued_books=issued_books
    )


# Add Book
@app.route("/add", methods=["POST"])
def add_book():

    title = request.form["title"]
    author = request.form["author"]
    copies = request.form["copies"]

    cursor.execute(
        "INSERT INTO books(title, author, copies) VALUES (%s,%s,%s)",
        (title, author, copies)
    )

    db.commit()

    return redirect("/")


# Issue Book
@app.route("/issue", methods=["POST"])
def issue_book():

    book_id = request.form["book_id"]
    student_name = request.form["student_name"]
    issue_date = request.form["issue_date"]

    issue_date_obj = datetime.strptime(issue_date, "%Y-%m-%d")
    due_date = issue_date_obj + timedelta(days=10)

    cursor.execute("SELECT copies FROM books WHERE id=%s", (book_id,))
    copies = cursor.fetchone()[0]

    if copies > 0:

        cursor.execute("""
            INSERT INTO issued_books(book_id, student_name, issue_date, due_date)
            VALUES (%s,%s,%s,%s)
        """, (book_id, student_name, issue_date, due_date))

        cursor.execute(
            "UPDATE books SET copies=copies-1 WHERE id=%s",
            (book_id,)
        )

        db.commit()

    return redirect("/")


# Return Book
@app.route("/return", methods=["POST"])
def return_book():

    issue_id = request.form["issue_id"]
    return_date = datetime.today().strftime("%Y-%m-%d")

    cursor.execute(
        "UPDATE issued_books SET return_date=%s WHERE id=%s",
        (return_date, issue_id)
    )

    cursor.execute(
        "SELECT book_id FROM issued_books WHERE id=%s",
        (issue_id,)
    )

    book_id = cursor.fetchone()[0]

    cursor.execute(
        "UPDATE books SET copies=copies+1 WHERE id=%s",
        (book_id,)
    )

    db.commit()

    return redirect("/")


# Search Books
@app.route("/search", methods=["POST"])
def search():

    keyword = request.form["keyword"]

    cursor.execute(
        "SELECT * FROM books WHERE title LIKE %s",
        ("%" + keyword + "%",)
    )

    books = cursor.fetchall()

    return render_template("index.html", books=books)


# Delete Book
@app.route("/delete/<int:id>")
def delete_book(id):

    cursor.execute("DELETE FROM books WHERE id=%s", (id,))
    db.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)