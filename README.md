
# CodeVault

A personal coding snippet manager built using Flask, SQLite,
HTML, CSS, and JavaScript.

## Features

- Save and organize code snippets
- Filter by programming language
- Search titles, descriptions, and code
- Copy snippets to clipboard
- Edit and delete saved snippets
- Persistent SQLite database
- Responsive dark-themed interface

## Tech Stack

- Python and Flask
- SQLite
- HTML5
- CSS3
- JavaScript

## Run Locally

1. Clone the repository.
2. Open the project folder in a terminal.
3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate it on Windows:

   ```bash
   venv\Scripts\activate
   ```

5. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the application:

   ```bash
   python app.py
   ```

7. Open http://127.0.0.1:5000 in your browser.

The SQLite database is created automatically when the application starts.
