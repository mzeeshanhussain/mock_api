# Step 1: Create a folder for your project, e.g., `mock-api`
# Inside it, create this file: app.py

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import uuid
import os

app = Flask(__name__)
DB_FILE = 'data.db'

# Step 2: Create the SQLite table on first run
if not os.path.exists(DB_FILE):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            data TEXT
        )''')

# Step 3: Home UI to insert/view data
@app.route("/ui")
def ui():
    return render_template_string('''
        <h2>Insert JSON</h2>
        <form method="post" action="/insert">
            Token: <input name="token"><br><br>
            JSON:<br>
            <textarea name="json" rows=10 cols=50>{}</textarea><br>
            <button type="submit">Submit</button>
        </form>
        <hr>
        <h2>Fetch by ID</h2>
        <form method="get" action="/view">
            ID: <input name="id"><br>
            <button type="submit">View</button>
        </form>
    ''')

# Step 4: Insert endpoint (POST from UI or API)
@app.route("/insert", methods=["POST"])
def insert():
    data = request.form.get("json") or request.json
    token = request.form.get("token") or request.headers.get("Authorization")
    if not data or not token:
        return jsonify({"error": "Missing token or JSON"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("INSERT INTO records (token, data) VALUES (?, ?)", (token, str(data)))
        new_id = cur.lastrowid
    return jsonify({"id": new_id})

# Step 5: View by ID
@app.route("/<int:record_id>", methods=["GET"])
def get_by_id(record_id):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, token, data FROM records WHERE id = ?", (record_id,))
        row = cur.fetchone()
    if row:
        return jsonify({"id": row[0], "token": row[1], "data": row[2]})
    return jsonify({"error": "Not found"}), 404

# Optional: Clean view UI
@app.route("/view")
def view():
    record_id = request.args.get("id")
    return get_by_id(int(record_id)) if record_id and record_id.isdigit() else jsonify({"error": "Invalid ID"})

# Step 6: Run locally
if __name__ == "__main__":
    app.run(debug=True)
