import os

import psycopg
from psycopg.rows import dict_row
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is missing. Add it in your hosting environment variables."
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


@app.route("/")
def home():
    with get_db() as connection:
        snippets = connection.execute("""
            SELECT id, title, language, code, description, created_at
            FROM snippets
            ORDER BY id DESC
        """).fetchall()

        edit_id = request.args.get("edit", type=int)
        editing = None

        if edit_id:
            editing = connection.execute(
                """
                SELECT id, title, language, code, description
                FROM snippets
                WHERE id = %s
                """,
                (edit_id,)
            ).fetchone()

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

    with get_db() as connection:
        connection.execute(
            """
            INSERT INTO snippets (title, language, code, description)
            VALUES (%s, %s, %s, %s)
            """,
            (title, language, code, description)
        )

    return redirect(url_for("home"))


@app.route("/edit/<int:snippet_id>", methods=["POST"])
def edit_snippet(snippet_id):
    title = request.form.get("title", "").strip()
    language = request.form.get("language", "").strip()
    code = request.form.get("code", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not language or not code:
        return redirect(url_for("home", edit=snippet_id))

    with get_db() as connection:
        connection.execute(
            """
            UPDATE snippets
            SET title = %s,
                language = %s,
                code = %s,
                description = %s
            WHERE id = %s
            """,
            (title, language, code, description, snippet_id)
        )

    return redirect(url_for("home"))


@app.route("/delete/<int:snippet_id>", methods=["POST"])
def delete_snippet(snippet_id):
    with get_db() as connection:
        connection.execute(
            "DELETE FROM snippets WHERE id = %s",
            (snippet_id,)
        )

    return redirect(url_for("home"))


@app.route("/health")
def health():
    try:
        with get_db() as connection:
            connection.execute("SELECT 1")

        return {"status": "ok", "database": "connected"}, 200

    except Exception:
        return {"status": "error", "database": "unavailable"}, 500
