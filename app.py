import os
import re
import threading

import psycopg
from psycopg.rows import dict_row
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if os.environ.get("VERCEL") and not SECRET_KEY:
    raise RuntimeError("Set a strong SECRET_KEY in Vercel Project Settings > Environment Variables.")

app.config.update(
    SECRET_KEY=SECRET_KEY or "local-development-only-change-this-key",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("VERCEL")),
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,
    MAX_CONTENT_LENGTH=150 * 1024,
)

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access your private library."
login_manager.login_message_category = "info"

_schema_ready = False
_schema_lock = threading.Lock()


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing. Add your PostgreSQL connection string in Vercel.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)


def ensure_schema():
    """Create the schema and safely migrate the original shared snippets table."""
    global _schema_ready

    if _schema_ready:
        return

    with _schema_lock:
        if _schema_ready:
            return

        with get_db() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    email VARCHAR(254) NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id BIGSERIAL PRIMARY KEY,
                    title VARCHAR(160) NOT NULL,
                    language VARCHAR(60) NOT NULL,
                    code TEXT NOT NULL,
                    description VARCHAR(500) NOT NULL DEFAULT '',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            connection.execute("""
                ALTER TABLE snippets
                ADD COLUMN IF NOT EXISTS user_id BIGINT
                REFERENCES users(id) ON DELETE CASCADE
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS snippets_user_id_idx
                ON snippets(user_id)
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS users_email_lower_idx
                ON users(LOWER(email))
            """)

        _schema_ready = True


@app.before_request
def prepare_database():
    if request.endpoint != "static":
        ensure_schema()


class User(UserMixin):
    def __init__(self, user_id, email):
        self.id = str(user_id)
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    ensure_schema()
    with get_db() as connection:
        row = connection.execute(
            "SELECT id, email FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
    return User(row["id"], row["email"]) if row else None


def valid_email(email):
    return len(email) <= 254 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def validate_snippet_form():
    title = request.form.get("title", "").strip()
    language = request.form.get("language", "").strip()
    code = request.form.get("code", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not language or not code:
        flash("Please complete the title, language and code fields.", "error")
        return None

    if len(title) > 160 or len(language) > 60 or len(description) > 500:
        flash("Title, language or description is too long.", "error")
        return None

    if len(code) > 100000:
        flash("Code must be 100,000 characters or fewer.", "error")
        return None

    return title, language, code, description


@app.route("/")
@login_required
def home():
    with get_db() as connection:
        snippets = connection.execute("""
            SELECT id, title, language, code, description, created_at
            FROM snippets
            WHERE user_id = %s
            ORDER BY id DESC
        """, (current_user.id,)).fetchall()

        edit_id = request.args.get("edit", type=int)
        editing = None
        if edit_id:
            editing = connection.execute("""
                SELECT id, title, language, code, description
                FROM snippets
                WHERE id = %s AND user_id = %s
            """, (edit_id, current_user.id)).fetchone()

    if request.args.get("edit") and not editing:
        flash("That snippet was not found in your account.", "error")

    return render_template("index.html", snippets=snippets, editing=editing)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not valid_email(email):
            flash("Enter a valid email address.", "error")
            return render_template("auth.html", mode="register")

        if len(password) < 12:
            flash("Use a password with at least 12 characters.", "error")
            return render_template("auth.html", mode="register")

        try:
            with get_db() as connection:
                existing_users = connection.execute(
                    "SELECT COUNT(*) AS total FROM users"
                ).fetchone()["total"]

                user_row = connection.execute("""
                    INSERT INTO users (email, password_hash)
                    VALUES (%s, %s)
                    RETURNING id, email
                """, (email, generate_password_hash(password))).fetchone()

                # Preserve the old single-user library by assigning its legacy
                # rows to the first account only. Later accounts never see them.
                if existing_users == 0:
                    connection.execute(
                        "UPDATE snippets SET user_id = %s WHERE user_id IS NULL",
                        (user_row["id"],),
                    )

            login_user(User(user_row["id"], user_row["email"]))
            flash("Your private CodeVault account is ready.", "success")
            return redirect(url_for("home"))

        except psycopg.errors.UniqueViolation:
            flash("An account with that email already exists. Please sign in.", "error")

    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as connection:
            user_row = connection.execute("""
                SELECT id, email, password_hash
                FROM users
                WHERE LOWER(email) = LOWER(%s)
            """, (email,)).fetchone()

        if not user_row or not check_password_hash(user_row["password_hash"], password):
            flash("Email or password is incorrect.", "error")
            return render_template("auth.html", mode="login")

        login_user(User(user_row["id"], user_row["email"]))
        flash("Welcome back to CodeVault.", "success")
        return redirect(url_for("home"))

    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/add", methods=["POST"])
@login_required
def add_snippet():
    values = validate_snippet_form()
    if not values:
        return redirect(url_for("home"))

    with get_db() as connection:
        connection.execute("""
            INSERT INTO snippets (user_id, title, language, code, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_user.id, *values))

    flash("Snippet saved to your private library.", "success")
    return redirect(url_for("home"))


@app.route("/edit/<int:snippet_id>", methods=["POST"])
@login_required
def edit_snippet(snippet_id):
    values = validate_snippet_form()
    if not values:
        return redirect(url_for("home", edit=snippet_id))

    with get_db() as connection:
        result = connection.execute("""
            UPDATE snippets
            SET title = %s, language = %s, code = %s, description = %s
            WHERE id = %s AND user_id = %s
        """, (*values, snippet_id, current_user.id))

    if result.rowcount == 0:
        flash("That snippet was not found in your account.", "error")
    else:
        flash("Snippet updated.", "success")

    return redirect(url_for("home"))


@app.route("/delete/<int:snippet_id>", methods=["POST"])
@login_required
def delete_snippet(snippet_id):
    with get_db() as connection:
        result = connection.execute(
            "DELETE FROM snippets WHERE id = %s AND user_id = %s",
            (snippet_id, current_user.id),
        )

    if result.rowcount:
        flash("Snippet deleted.", "success")
    else:
        flash("That snippet was not found in your account.", "error")

    return redirect(url_for("home"))


@app.route("/health")
def health():
    try:
        ensure_schema()
        with get_db() as connection:
            connection.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}, 200
    except Exception:
        app.logger.exception("CodeVault health check failed")
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
