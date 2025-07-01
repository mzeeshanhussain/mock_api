from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import json

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

    # Ensure data is valid JSON
    try:
        parsed_data = json.loads(data) if isinstance(data, str) else data
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("INSERT INTO records (token, data) VALUES (?, ?)", (token, json.dumps(parsed_data)))
        new_id = cur.lastrowid
    return jsonify({"id": new_id})

# View data by ID (API-only, token required via header, returns raw JSON)
@app.route("/<int:record_id>", methods=["GET"])
def get_by_id(record_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Missing token"}), 401

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT token, data FROM records WHERE id = ?", (record_id,))
        row = cur.fetchone()

    if row and row[0] == token:
        return jsonify(json.loads(row[1]))
    return jsonify({"error": "Not found or invalid token"}), 403

# View via UI (no auth, shows full record: id, token, data)
@app.route("/view")
def view():
    record_id = request.args.get("id")
    if not record_id or not record_id.isdigit():
        return jsonify({"error": "Invalid ID"})

    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT id, token, data FROM records WHERE id = ?", (int(record_id),))
        row = cur.fetchone()

    if row:
        try:
            parsed = json.loads(row[2])
        except:
            parsed = row[2]
        return jsonify({
            "id": row[0],
            "token": row[1],
            "data": parsed
        })
    return jsonify({"error": "Not found"}), 404

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
