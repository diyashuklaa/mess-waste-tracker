# 🌿 MessTrack — College Mess Food Waste Tracker

A beginner-friendly full-stack app built with **Flask + SQLite + Vanilla JS**.

---

## 📁 Project Structure

```
mess-waste-tracker/
├── app.py                   ← Flask backend (all routes + DB logic)
├── mess.db                  ← SQLite database (auto-created on first run)
├── requirements.txt
├── templates/
│   ├── base.html            ← Shared nav + layout
│   ├── index.html           ← Dashboard (KPIs + charts + dish table)
│   ├── log.html             ← Form to add daily/dish entries
│   └── report.html          ← Weekly comparison + dish ranking
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## 🗄️ Database Schema (2 tables only)

```sql
-- One row per day
CREATE TABLE daily_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date    TEXT    NOT NULL UNIQUE,   -- e.g. "2024-06-10"
    plates_used INTEGER DEFAULT 0,
    food_served REAL    DEFAULT 0,         -- kg
    food_wasted REAL    DEFAULT 0          -- kg
);

-- One row per dish per day (can have many)
CREATE TABLE dish_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date    TEXT NOT NULL,
    dish_name   TEXT NOT NULL,
    served_kg   REAL DEFAULT 0,
    wasted_kg   REAL DEFAULT 0
);
```

---

## 🔌 API Routes

| Method | Route              | Purpose                        |
|--------|--------------------|--------------------------------|
| POST   | `/api/daily`       | Save / update daily log        |
| GET    | `/api/daily`       | Get last N days (default: 7)   |
| POST   | `/api/dish`        | Add dish waste entry           |
| GET    | `/api/dish/summary`| Dish waste % ranking           |
| GET    | `/api/weekly`      | Weekly aggregated comparison   |

---

## 🚀 Setup & Run

```bash
# 1. Install Flask
pip install flask

# 2. Run the app
python app.py

# 3. Open in browser
http://127.0.0.1:5000
```

That's it! SQLite database (`mess.db`) is created automatically.

---

## 📖 How to Use

1. **Log Entry** (`/log`) — Fill in daily totals (plates, kg served/wasted) and individual dish entries.
2. **Dashboard** (`/`) — See 7-day KPIs, a daily waste bar chart, and which dishes waste least.
3. **Reports** (`/report`) — Compare waste across weeks and rank all dishes by waste percentage.

---

## 💡 Beginner Tips

- No ORM needed — plain `sqlite3` module is used throughout.
- No JavaScript framework — everything is plain `fetch()` + DOM manipulation.
- No build step — just run `python app.py` and go.
- To reset all data: delete `mess.db` and restart the server.
