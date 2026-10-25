
import os
import sqlite3
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "students.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    """)

    count = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if count == 0:
        students = [
            ("2026-00123", "Jade Casas", "BSIT", 1, "A"),
            ("2026-00124", "Mary Debaja", "BSIT", 1, "A"),
            ("2026-00125", "Hemar Abian", "BSIT", 2, "B"),
            ("2026-00126", "Raveen Celo", "BSCS", 2, "A"),
            ("2026-00127", "Lorenzo Colasisang", "BSIT", 3, "B")
        ]

        conn.executemany("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, students)

    conn.commit()
    conn.close()


# Create the database and sample records.
init_db()


@app.route("/")
def home():
    search = request.args.get("search", "").strip()
    program = request.args.get("program", "").strip()
    year = request.args.get("year", "").strip()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query += """
            AND (
                name LIKE ?
                OR student_id LIKE ?
                OR CAST(id AS TEXT) LIKE ?
            )
        """
        term = f"%{search}%"
        params.extend([term, term, term])

    if program:
        query += " AND program = ?"
        params.append(program)

    if year in ("1", "2", "3", "4"):
        query += " AND year = ?"
        params.append(int(year))

    query += " ORDER BY id ASC"

    conn = get_db_connection()
    students = conn.execute(query, params).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]
    conn.close()

    return render_template(
        "index.html",
        students=students,
        search=search,
        selected_program=program,
        selected_year=year,
        total=total
    )


@app.route("/students")
def all_students():
    conn = get_db_connection()
    students = conn.execute(
        "SELECT * FROM students ORDER BY id ASC"
    ).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


@app.route("/students/<int:student_id>")
def student_detail(student_id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    conn.close()

    if student is None:
        abort(404)

    return render_template("student_detail.html", student=student)


@app.route("/api/students")
def filter_students_api():
    program = request.args.get("program", "").strip()
    year = request.args.get("year", "").strip()

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if program:
        query += " AND program = ?"
        params.append(program)

    if year in ("1", "2", "3", "4"):
        query += " AND year = ?"
        params.append(int(year))

    query += " ORDER BY id ASC"

    conn = get_db_connection()
    students = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


@app.route("/hello")
def hello():
    name = request.args.get("name", "Student")
    return jsonify({"message": f"Hello, {name}!"})


@app.errorhandler(404)
def page_not_found(error):
    return """
    <html>
    <head><title>404 - Student Not Found</title></head>
    <body style="font-family:Arial;text-align:center;padding:60px">
        <h1>404 - Not Found</h1>
        <p>Hindi makita ang hinahanap mong student o page.</p>
        <a href="/">Back to Homepage</a>
    </body>
    </html>
    """, 404


if __name__ == "__main__":
    app.run(debug=True)
