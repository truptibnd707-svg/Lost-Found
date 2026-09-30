import os
import sqlite3
import webbrowser
from threading import Timer
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OWNER_FOLDER = os.path.join(UPLOAD_FOLDER, "owner")
ITEM_FOLDER = os.path.join(UPLOAD_FOLDER, "item")

os.makedirs(OWNER_FOLDER, exist_ok=True)
os.makedirs(ITEM_FOLDER, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "database.db")


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            name TEXT,
            location TEXT,
            contact TEXT,
            email TEXT,
            description TEXT,
            owner_photo TEXT,
            item_photo TEXT
        )
    """
    )
    db.commit()


init_db()


# ---------- HOME (FRONTEND) ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- IMAGE SERVING ----------
@app.route("/uploads/<folder>/<filename>")
def serve_image(folder, filename):
    return send_from_directory(os.path.join(UPLOAD_FOLDER, folder), filename)


# ---------- REPORT ITEM ----------
@app.route("/report", methods=["POST"])
def report_item():
    form = request.form
    owner_photo = request.files.get("ownerPhoto")
    item_photo = request.files.get("itemPhoto")

    owner_path = ""
    item_path = ""

    if owner_photo:
        filename = secure_filename(owner_photo.filename)
        owner_photo.save(os.path.join(OWNER_FOLDER, filename))
        owner_path = f"uploads/owner/{filename}"

    if item_photo:
        filename = secure_filename(item_photo.filename)
        item_photo.save(os.path.join(ITEM_FOLDER, filename))
        item_path = f"uploads/item/{filename}"

    db = get_db()
    db.execute(
        """
        INSERT INTO items
        (type, name, location, contact, email, description, owner_photo, item_photo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            form.get("type"),
            form.get("item"),
            form.get("location"),
            form.get("contact"),
            form.get("email"),
            form.get("desc"),
            owner_path,
            item_path,
        ),
    )
    db.commit()

    return jsonify({"status": "success"})


# ---------- GET ITEMS ----------
@app.route("/items")
def get_items():
    search = request.args.get("search", "")
    item_type = request.args.get("type", "All")

    query = "SELECT * FROM items WHERE name LIKE ?"
    params = [f"%{search}%"]

    if item_type != "All":
        query += " AND type = ?"
        params.append(item_type)

    db = get_db()
    items = db.execute(query, params).fetchall()

    return jsonify([dict(item) for item in items])


# ---------- AUTO OPEN BROWSER ----------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)
