from flask import Flask, request, jsonify, send_file, abort, Response, stream_with_context
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import sqlite3, os, re, shutil, time, queue, threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__, static_folder="../", static_url_path="")
CORS(app, origins=["*"])

# ── Config ────────────────────────────────────────────────────────────────────
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-me-in-production"),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),   # your Gmail
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),   # Gmail app password
    MAIL_DEFAULT_SENDER=os.environ.get("MAIL_USERNAME"),
)

OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "dassrijan76@gmail.com")
RESUME_PATH = os.environ.get("RESUME_PATH", "../resume.pdf")
BASE_URL     = os.environ.get("BASE_URL", "http://localhost:5000")
LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "dassrijan76")

mail = Mail(app)
s    = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ── Database ──────────────────────────────────────────────────────────────────
DB = os.path.join(os.path.dirname(__file__), "requests.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS resume_requests (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT NOT NULL,
                email     TEXT NOT NULL,
                reason    TEXT,
                status    TEXT DEFAULT 'pending',
                created   TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_views (
                id      INTEGER PRIMARY KEY CHECK (id = 1),
                total   INTEGER DEFAULT 0
            )
        """)
        conn.execute("INSERT OR IGNORE INTO page_views (id, total) VALUES (1, 0)")
        conn.commit()

init_db()

# ── View counter (SSE) ────────────────────────────────────────────────────────
_sse_clients = []
_sse_lock    = threading.Lock()

def _get_views():
    with get_db() as conn:
        row = conn.execute("SELECT total FROM page_views WHERE id = 1").fetchone()
        return row["total"] if row else 0

def _increment_views():
    with get_db() as conn:
        conn.execute("UPDATE page_views SET total = total + 1 WHERE id = 1")
        conn.commit()
        row = conn.execute("SELECT total FROM page_views WHERE id = 1").fetchone()
        return row["total"]

def _broadcast(count):
    """Push new count to all SSE subscribers."""
    dead = []
    with _sse_lock:
        for q in _sse_clients:
            try:
                q.put_nowait(count)
            except Exception:
                dead.append(q)
        for q in dead:
            _sse_clients.remove(q)

@app.route("/api/views/track", methods=["POST"])
def track_view():
    count = _increment_views()
    _broadcast(count)
    return jsonify({"total": count})

@app.route("/api/views/stream")
def views_stream():
    """SSE endpoint — pushes view count to all connected clients in real time."""
    q = queue.Queue()
    with _sse_lock:
        _sse_clients.append(q)

    def generate():
        # Send current count immediately on connect
        try:
            yield f"data: {_get_views()}\n\n"
            while True:
                try:
                    count = q.get(timeout=25)
                    yield f"data: {count}\n\n"
                except queue.Empty:
                    yield ": keep-alive\n\n"  # prevent proxy timeouts
        finally:
            with _sse_lock:
                if q in _sse_clients:
                    _sse_clients.remove(q)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

# ── Serve portfolio ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("index.html")

# ── Helpers ───────────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def valid_email(e):
    return bool(EMAIL_RE.match(e))

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/api/request-resume", methods=["POST"])
def request_resume():
    data   = request.get_json(silent=True) or {}
    name   = (data.get("name") or "").strip()
    email  = (data.get("email") or "").strip().lower()
    reason = (data.get("reason") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400
    if not valid_email(email):
        return jsonify({"error": "Invalid email address."}), 400

    with get_db() as conn:
        # Prevent duplicate pending requests
        existing = conn.execute(
            "SELECT id, status FROM resume_requests WHERE email = ? ORDER BY id DESC LIMIT 1",
            (email,)
        ).fetchone()

        if existing:
            if existing["status"] == "approved":
                # Re-send download link
                _send_download_email(name, email)
                return jsonify({"message": "You are already approved. A download link has been resent to your email."})
            if existing["status"] == "pending":
                return jsonify({"message": "Your request is already pending. You'll be notified once approved."})

        row = conn.execute(
            "INSERT INTO resume_requests (name, email, reason) VALUES (?, ?, ?)",
            (name, email, reason)
        ).lastrowid
        conn.commit()

    approve_token = s.dumps({"id": row, "email": email}, salt="approve")
    approve_url   = f"{BASE_URL}/api/approve/{approve_token}"

    # Email to owner
    try:
        msg = Message(
            subject=f"Resume Access Request from {name}",
            recipients=[OWNER_EMAIL],
            html=f"""
            <h2>New Resume Download Request</h2>
            <p><b>Name:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Reason:</b> {reason or 'Not provided'}</p>
            <p><b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
            <br>
            <a href="{approve_url}" style="
                background:#6366f1;color:#fff;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:600;
            ">Approve Request</a>
            <p style="color:#888;font-size:12px;margin-top:16px;">
                This approval link is valid for 7 days.
            </p>
            """
        )
        mail.send(msg)
        app.logger.info(f"Approval email sent to {OWNER_EMAIL} for {email}")
    except Exception as e:
        import traceback
        app.logger.error(f"Mail error: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        return jsonify({"error": f"Mail failed: {str(e)}"}), 500

    return jsonify({"message": "Request submitted! You'll receive an email once approved."})


@app.route("/api/approve/<token>")
def approve(token):
    try:
        data = s.loads(token, salt="approve", max_age=604800)  # 7 days
    except SignatureExpired:
        return "<h2>This approval link has expired.</h2>", 400
    except BadSignature:
        return "<h2>Invalid approval link.</h2>", 400

    req_id = data["id"]
    email  = data["email"]

    with get_db() as conn:
        row = conn.execute("SELECT * FROM resume_requests WHERE id = ?", (req_id,)).fetchone()
        if not row:
            return "<h2>Request not found.</h2>", 404
        if row["status"] == "approved":
            return "<h2>Already approved.</h2>"

        conn.execute("UPDATE resume_requests SET status = 'approved' WHERE id = ?", (req_id,))
        conn.commit()

    _send_download_email(row["name"], email)
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#0a0f1e;color:#e2e8f0;">
        <h2 style="color:#6366f1;">✅ Approved!</h2>
        <p>A download link has been sent to <b>{}</b>.</p>
    </body></html>
    """.format(email)


@app.route("/api/download/<token>")
def download_resume(token):
    try:
        data = s.loads(token, salt="download", max_age=86400)  # 24 hours
    except SignatureExpired:
        return jsonify({"error": "Download link has expired."}), 400
    except BadSignature:
        return jsonify({"error": "Invalid download link."}), 400

    email = data.get("email")
    with get_db() as conn:
        row = conn.execute(
            "SELECT status FROM resume_requests WHERE email = ? ORDER BY id DESC LIMIT 1",
            (email,)
        ).fetchone()

    if not row or row["status"] != "approved":
        abort(403)

    resume = os.path.abspath(RESUME_PATH)
    if not os.path.exists(resume):
        return jsonify({"error": "Resume file not found on server."}), 404

    return send_file(resume, as_attachment=True, download_name="Srijan_Das_Resume.pdf")


# ── Internal helper ───────────────────────────────────────────────────────────
def _send_download_email(name, email):
    token        = s.dumps({"email": email}, salt="download")
    download_url = f"{BASE_URL}/api/download/{token}"

    msg = Message(
        subject="Your Resume Download Link – Srijan Das",
        recipients=[email],
        html=f"""
        <h2>Hi {name},</h2>
        <p>Your request to download Srijan Das's resume has been <b>approved</b>.</p>
        <p>Click the button below to download. The link is valid for <b>24 hours</b>.</p>
        <br>
        <a href="{download_url}" style="
            background:#6366f1;color:#fff;padding:12px 24px;
            border-radius:8px;text-decoration:none;font-weight:600;
        ">📄 Download Resume</a>
        <p style="color:#888;font-size:12px;margin-top:16px;">
            If you did not request this, please ignore this email.
        </p>
        """
    )
    mail.send(msg)


# ── LeetCode Stats ────────────────────────────────────────────────────────────
_lc_cache = {"data": None, "ts": 0}
LC_CACHE_TTL = 300  # seconds (5 min)

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      reputation
      starRating
    }
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    badges {
      id
      displayName
      icon
    }
    userCalendar {
      streak
      totalActiveDays
    }
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
}
"""

@app.route("/api/leetcode")
def leetcode_stats():
    global _lc_cache
    now = time.time()

    if _lc_cache["data"] and (now - _lc_cache["ts"]) < LC_CACHE_TTL:
        return jsonify(_lc_cache["data"])

    try:
        import urllib.request, json as _json
        payload = _json.dumps({
            "query": LEETCODE_QUERY,
            "variables": {"username": LEETCODE_USERNAME}
        }).encode()
        req = urllib.request.Request(
            "https://leetcode.com/graphql",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = _json.loads(resp.read())

        user = raw["data"]["matchedUser"]
        contest = raw["data"].get("userContestRanking") or {}

        # Parse solved counts
        solved = {s["difficulty"]: s["count"] for s in user["submitStats"]["acSubmissionNum"]}

        result = {
            "username": user["username"],
            "ranking": user["profile"]["ranking"],
            "totalSolved": solved.get("All", 0),
            "easySolved": solved.get("Easy", 0),
            "mediumSolved": solved.get("Medium", 0),
            "hardSolved": solved.get("Hard", 0),
            "streak": user["userCalendar"]["streak"] if user.get("userCalendar") else 0,
            "totalActiveDays": user["userCalendar"]["totalActiveDays"] if user.get("userCalendar") else 0,
            "badges": [{"name": b["displayName"], "icon": b["icon"]} for b in (user.get("badges") or [])],
            "contestsAttended": contest.get("attendedContestsCount", 0),
            "contestRating": round(contest.get("rating", 0)),
            "contestGlobalRanking": contest.get("globalRanking", "N/A"),
            "contestTopPercentage": round(contest.get("topPercentage", 0), 1) if contest.get("topPercentage") else "N/A",
        }

        _lc_cache = {"data": result, "ts": now}
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"LeetCode fetch error: {e}")
        if _lc_cache["data"]:
            return jsonify(_lc_cache["data"])  # serve stale cache on error
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)