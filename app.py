from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3, hashlib, os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "mess-tracker-secret-2024"   # change this in production
DB = "mess.db"

# ── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name     TEXT DEFAULT '',
                role          TEXT DEFAULT 'Student',
                joined_date   TEXT DEFAULT (date('now'))
            );

            CREATE TABLE IF NOT EXISTS daily_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date    TEXT    NOT NULL UNIQUE,
                plates_used INTEGER DEFAULT 0,
                food_served REAL    DEFAULT 0,
                food_wasted REAL    DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS dish_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date    TEXT NOT NULL,
                dish_name   TEXT NOT NULL,
                served_kg   REAL DEFAULT 0,
                wasted_kg   REAL DEFAULT 0
            );
        """)

init_db()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

# ── Auth pages ────────────────────────────────────────────────────────────────
@app.route("/login")
def login_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/register")
def register_page():
    if "user_id" in session:
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

# ── Auth API ──────────────────────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def api_register():
    d = request.json
    username  = d.get("username", "").strip().lower()
    password  = d.get("password", "")
    full_name = d.get("full_name", "").strip()
    role      = d.get("role", "Student")
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters."}), 400
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?,?,?,?)",
                (username, hash_password(password), full_name, role)
            )
        return jsonify({"status": "ok"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already taken."}), 409

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    username = d.get("username", "").strip().lower()
    password = d.get("password", "")
    with get_db() as db:
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=?",
            (username, hash_password(password))
        ).fetchone()
    if not user:
        return jsonify({"error": "Invalid username or password."}), 401
    session["user_id"]   = user["id"]
    session["username"]  = user["username"]
    session["full_name"] = user["full_name"]
    session["role"]      = user["role"]
    return jsonify({"status": "ok"})

@app.route("/api/profile", methods=["GET"])
@login_required
def api_profile():
    with get_db() as db:
        user         = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        total_logs   = db.execute("SELECT COUNT(*) as c FROM daily_log").fetchone()["c"]
        total_dishes = db.execute("SELECT COUNT(*) as c FROM dish_log").fetchone()["c"]
        total_wasted = db.execute("SELECT COALESCE(SUM(food_wasted),0) as w FROM daily_log").fetchone()["w"]
    return jsonify({
        "username":     user["username"],
        "full_name":    user["full_name"],
        "role":         user["role"],
        "joined_date":  user["joined_date"],
        "total_logs":   total_logs,
        "total_dishes": total_dishes,
        "total_wasted": round(total_wasted, 1),
    })

@app.route("/api/profile", methods=["POST"])
@login_required
def api_update_profile():
    d = request.json
    full_name = d.get("full_name", "").strip()
    role      = d.get("role", "Student")
    with get_db() as db:
        db.execute("UPDATE users SET full_name=?, role=? WHERE id=?",
                   (full_name, role, session["user_id"]))
    session["full_name"] = full_name
    session["role"]      = role
    return jsonify({"status": "ok"})

# ── Protected pages ───────────────────────────────────────────────────────────
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/log")
@login_required
def log_page():
    return render_template("log.html")

@app.route("/report")
@login_required
def report_page():
    return render_template("report.html")

# ── API: daily log ────────────────────────────────────────────────────────────
@app.route("/api/daily", methods=["POST"])
@login_required
def save_daily():
    d    = request.json
    date = d.get("date", str(datetime.today().date()))
    with get_db() as db:
        db.execute("""
            INSERT INTO daily_log (log_date, plates_used, food_served, food_wasted)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(log_date) DO UPDATE SET
                plates_used = excluded.plates_used,
                food_served = excluded.food_served,
                food_wasted = excluded.food_wasted
        """, (date, d["plates_used"], d["food_served"], d["food_wasted"]))
    return jsonify({"status": "ok"})

@app.route("/api/daily", methods=["GET"])
@login_required
def get_daily():
    days  = request.args.get("days", 7)
    since = str((datetime.today() - timedelta(days=int(days))).date())
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM daily_log WHERE log_date >= ? ORDER BY log_date", (since,)
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/dish", methods=["POST"])
@login_required
def save_dish():
    d    = request.json
    date = d.get("date", str(datetime.today().date()))
    with get_db() as db:
        db.execute(
            "INSERT INTO dish_log (log_date, dish_name, served_kg, wasted_kg) VALUES (?,?,?,?)",
            (date, d["dish_name"], d["served_kg"], d["wasted_kg"])
        )
    return jsonify({"status": "ok"})

@app.route("/api/dish/summary", methods=["GET"])
@login_required
def dish_summary():
    with get_db() as db:
        rows = db.execute("""
            SELECT dish_name,
                   SUM(served_kg) AS total_served,
                   SUM(wasted_kg) AS total_wasted,
                   ROUND(SUM(wasted_kg)*100.0/NULLIF(SUM(served_kg),0), 1) AS waste_pct
            FROM dish_log
            GROUP BY dish_name
            ORDER BY waste_pct ASC
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/weekly", methods=["GET"])
@login_required
def weekly():
    with get_db() as db:
        rows = db.execute("""
            SELECT strftime('%W-%Y', log_date) AS week,
                   SUM(food_wasted) AS total_wasted,
                   SUM(food_served) AS total_served,
                   SUM(plates_used) AS total_plates
            FROM daily_log
            GROUP BY week
            ORDER BY week DESC
            LIMIT 8
        """).fetchall()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True)
