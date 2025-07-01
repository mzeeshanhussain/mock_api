from flask import Flask, request, jsonify, render_template_string
import sqlite3
import uuid
import os

app = Flask(__name__)
DB_FILE = 'data.db'

# Create the SQLite table if it doesn't exist
if not os.path.exists(DB_FILE):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                data TEXT
            )
        ''')

# UI to insert and view data
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

# Insert data (POST endpoint)
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

# View data by ID (GET endpoint)
@app.route("/<int:record_id>", methods=["GET"])
def get_by_id(record_id):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, token, data FROM records WHERE id = ?", (record_id,))
        row = cur.fetchone()
    if row:
        return jsonify({"id": row[0], "token": row[1], "data": row[2]})
    return jsonify({"error": "Not found"}), 404

# View using /view?id=<id>
@app.route("/view")
def view():
    record_id = request.args.get("id")
    return get_by_id(int(record_id)) if record_id and record_id.isdigit() else jsonify({"error": "Invalid ID"})

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
