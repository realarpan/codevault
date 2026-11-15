# CodeVault

A private, multi-user code snippet library built with Flask, PostgreSQL, HTML, CSS and JavaScript. The existing dark CodeVault workspace is retained, with account-based access added.

## Features

- Private registration, sign-in and sign-out
- Passwords stored as secure hashes (never plaintext)
- Each account can only view, create, edit and delete its own snippets
- PostgreSQL persistence suitable for serverless hosting
- Automatic idempotent database schema creation and migration
- CSRF protection on all form submissions
- Search, language filtering and copy-to-clipboard
- Responsive dark-themed interface
- Health endpoint at /health

## Vercel deployment

### 1. Create a PostgreSQL database

Create a PostgreSQL database with a provider such as Neon or Supabase. Copy its connection string. Use the provider's pooled connection string if it recommends one for serverless applications.

### 2. Import the GitHub repository

1. Open the Vercel dashboard.
2. Select **Add New → Project**.
3. Import **realarpan/codevault**.
4. Keep the project root directory as the repository root. No build command is required for this Flask application.

### 3. Add environment variables

In **Project → Settings → Environment Variables**, add:

| Name | Value |
| --- | --- |
| DATABASE_URL | Your PostgreSQL connection string |
| SECRET_KEY | A long, random secret value |

Set both for Production and Preview as appropriate. Do not commit either value to GitHub. Generate a unique secret with a password manager; do not reuse a database password.

### 4. Deploy

Deploy the project. Vercel detects the root app.py Flask application and installs packages from requirements.txt. On the first request, CodeVault creates the required tables and indexes automatically.

Open https://YOUR-PROJECT.vercel.app/health. A successful response looks like:

```json
{"status":"ok","database":"connected"}
```

Then open the site and create your account.

## Database and existing snippets

The app creates a users table and adds a nullable user_id ownership column to the existing snippets table. If the database contains legacy snippets from the original single-user version, the first account registered claims those unowned rows. Later accounts cannot see them. New snippets are always assigned to the signed-in account.

Use a fresh database for a clean launch if you do not need to preserve any existing records. Back up an existing database before pointing this version at it.

## Security notes

- Set a strong SECRET_KEY in Vercel before deployment. The app deliberately refuses to start on Vercel without it.
- Keep DATABASE_URL private and restrict database network access where your provider supports it.
- All snippet routes require authentication and filter by the authenticated user's ID.
- CSRF tokens are required for POST forms.
- Passwords are hashed using Werkzeug's password hashing utilities.
- There is no password-reset email flow yet. Users who forget their password will need an administrator-assisted reset or a future reset feature.
- This is an account-based private library, not an end-to-end encrypted vault. The hosting platform and database operator can technically access stored snippet content.

## Project structure

```text
codevault/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── auth.html
│   └── index.html
└── static/
    ├── script.js
    └── style.css
```
