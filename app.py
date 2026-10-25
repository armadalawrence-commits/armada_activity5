
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


# Initialize the database and sample records.
init_db()


def validate_student_data(data):
    """Validate incoming JSON for creating or updating a student."""
    if not isinstance(data, dict):
        return None, "A valid JSON object is required."

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        if field not in data or data[field] is None:
            return None, f"Missing required field: {field}"

        if not str(data[field]).strip():
            return None, f"{field} cannot be empty."

    try:
        raw_year = data["year"]

        if isinstance(raw_year, bool):
            raise ValueError

        year = int(raw_year)

        if isinstance(raw_year, float) and not raw_year.is_integer():
            raise ValueError

        if isinstance(raw_year, str) and raw_year.strip() != str(year):
            raise ValueError

        if year not in (1, 2, 3, 4):
            return None, "Year must be between 1 and 4."

    except (ValueError, TypeError):
        return None, "Year must be a whole number from 1 to 4."

    student = {
        "student_id": str(data["student_id"]).strip(),
        "name": str(data["name"]).strip(),
        "program": str(data["program"]).strip(),
        "year": year,
        "section": str(data["section"]).strip()
    }

    return student, None


# --------------------------------------------------
# HOME PAGE: Search, filter, and view student records
# --------------------------------------------------
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
    try:
        students = conn.execute(query, params).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]
    finally:
        conn.close()

    return render_template(
        "index.html",
        students=students,
        search=search,
        selected_program=program,
        selected_year=year,
        total=total
    )


# --------------------------------------------------
# EXISTING JSON ROUTE
# GET /students
# --------------------------------------------------
@app.route("/students")
def all_students():
    conn = get_db_connection()
    try:
        students = conn.execute(
            "SELECT * FROM students ORDER BY id ASC"
        ).fetchall()

        return jsonify([dict(student) for student in students])
    finally:
        conn.close()


# --------------------------------------------------
# HTML STUDENT DETAILS PAGE
# GET /students/<student_id>
# --------------------------------------------------
@app.route("/students/<int:student_id>")
def student_detail(student_id):
    conn = get_db_connection()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()
    finally:
        conn.close()

    if student is None:
        abort(404)

    return render_template(
        "student_detail.html",
        student=student
    )


# --------------------------------------------------
# READ ALL + CREATE
# GET  /api/students
# POST /api/students
# --------------------------------------------------
@app.route("/api/students", methods=["GET", "POST"])
def api_students():

    # READ ALL STUDENTS
    if request.method == "GET":
        program = request.args.get("program", "").strip()
        year = request.args.get("year", "").strip()

        query = "SELECT * FROM students WHERE 1=1"
        params = []

        if program:
            query += " AND program = ?"
            params.append(program)

        if year:
            if year not in ("1", "2", "3", "4"):
                return jsonify({
                    "error": "Year must be between 1 and 4."
                }), 400

            query += " AND year = ?"
            params.append(int(year))

        query += " ORDER BY id ASC"

        conn = get_db_connection()
        try:
            students = conn.execute(query, params).fetchall()
            return jsonify([dict(student) for student in students])
        finally:
            conn.close()

    # CREATE A STUDENT
    data = request.get_json(silent=True)
    student, error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            student["year"],
            student["section"]
        ))

        conn.commit()
        new_id = cursor.lastrowid

        return jsonify({
            "message": "Student added successfully.",
            "id": new_id
        }), 201
    finally:
        conn.close()


# --------------------------------------------------
# READ ONE STUDENT
# GET /api/students/<id>
# --------------------------------------------------
@app.route("/api/students/<int:id>", methods=["GET"])
def api_get_student(id):
    conn = get_db_connection()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (id,)
        ).fetchone()
    finally:
        conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found."
        }), 404

    return jsonify(dict(student))


# --------------------------------------------------
# UPDATE A STUDENT
# PUT /api/students/<id>
# --------------------------------------------------
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json(silent=True)
    student, error = validate_student_data(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            student["student_id"],
            student["name"],
            student["program"],
            student["year"],
            student["section"],
            id
        ))

        conn.commit()

        return jsonify({
            "message": "Student updated successfully.",
            "id": id
        })
    finally:
        conn.close()


# --------------------------------------------------
# DELETE A STUDENT
# DELETE /api/students/<id>
# --------------------------------------------------
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?",
            (id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found."
            }), 404

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully.",
            "id": id
        })
    finally:
        conn.close()


# --------------------------------------------------
# HELLO API
# --------------------------------------------------
@app.route("/hello")
def hello():
    name = request.args.get("name", "Student")
    return jsonify({
        "message": f"Hello, {name}!"
    })


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------
@app.errorhandler(404)
def page_not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({
            "error": "Resource not found."
        }), 404

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>404 - Student Not Found</title>
    </head>
    <body style="font-family:Arial;text-align:center;padding:60px">
        <h1>404 - Not Found</h1>
        <p>Hindi makita ang hinahanap mong student o page.</p>
        <a href="/">Back to Homepage</a>
    </body>
    </html>
    """, 404


if __name__ == "__main__":
    app.run(debug=True)
