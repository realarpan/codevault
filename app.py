
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path

app = Flask(__name__)

DATABASE = Path(__file__).parent / "codevault.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            code TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


@app.route("/")
def home():
    connection = get_db()

    snippets = connection.execute("""
        SELECT * FROM snippets
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    edit_id = request.args.get("edit", type=int)
    editing = None

    if edit_id:
        connection = get_db()
        editing = connection.execute(
            "SELECT * FROM snippets WHERE id = ?",
            (edit_id,)
        ).fetchone()
        connection.close()

    return render_template(
        "index.html",
        snippets=snippets,
        editing=editing
    )


@app.route("/add", methods=["POST"])
def add_snippet():
    title = request.form.get("title", "").strip()
    language = request.form.get("language", "").strip()
    code = request.form.get("code", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not language or not code:
        return redirect(url_for("home"))

    connection = get_db()

    connection.execute("""
        INSERT INTO snippets (title, language, code, description)
        VALUES (?, ?, ?, ?)
    """, (title, language, code, description))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


@app.route("/edit/<int:snippet_id>", methods=["POST"])
def edit_snippet(snippet_id):
    title = request.form.get("title", "").strip()
    language = request.form.get("language", "").strip()
    code = request.form.get("code", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not language or not code:
        return redirect(url_for("home", edit=snippet_id))

    connection = get_db()

    connection.execute("""
        UPDATE snippets
        SET title = ?, language = ?, code = ?, description = ?
        WHERE id = ?
    """, (title, language, code, description, snippet_id))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


@app.route("/delete/<int:snippet_id>", methods=["POST"])
def delete_snippet(snippet_id):
    connection = get_db()

    connection.execute(
        "DELETE FROM snippets WHERE id = ?",
        (snippet_id,)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
