from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import sqlite3, os, re, time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# On Vercel, static files are served from the root
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, static_folder=_root, static_url_path="")
CORS(app, origins=["*"])

# ── Config ────────────────────────────────────────────────────────────────────
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-me-in-production"),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.environ.get("MAIL_USERNAME"),
)

OWNER_EMAIL       = os.environ.get("OWNER_EMAIL", "dassrijan76@gmail.com")
RESUME_URL        = os.environ.get("RESUME_URL", "")
BASE_URL          = os.environ.get("BASE_URL", "http://localhost:5000")
LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "dassrijan76")

# Verified company domains — instant resume access, no approval needed
VERIFIED_DOMAINS = {
    # Tech giants
    "google.com", "microsoft.com", "amazon.com", "apple.com", "meta.com",
    "netflix.com", "adobe.com", "salesforce.com", "oracle.com", "ibm.com",
    "intel.com", "nvidia.com", "qualcomm.com", "cisco.com", "vmware.com",
    # Indian IT & product companies
    "tcs.com", "infosys.com", "wipro.com", "hcltech.com", "techmahindra.com",
    "capgemini.com", "accenture.com", "cognizant.com", "mphasis.com",
    "ltimindtree.com", "hexaware.com", "persistent.com", "kpit.com",
    "mindtree.com", "niit.com", "zensar.com", "birlasoft.com",
    # Indian startups & product
    "flipkart.com", "paytm.com", "razorpay.com", "zomato.com", "swiggy.in",
    "ola.com", "byjus.com", "freshworks.com", "zoho.com", "browserstack.com",
    "meesho.com", "cred.club", "phonepe.com", "groww.in", "zerodha.com",
    # Global consulting & finance
    "deloitte.com", "pwc.com", "ey.com", "kpmg.com", "mckinsey.com",
    "bcg.com", "bain.com", "jpmorgan.com", "goldmansachs.com",
    # Recruiting platforms
    "linkedin.com", "naukri.com", "instahyre.com", "hirist.com",
}

def is_verified_recruiter(email):
    domain = email.split("@")[-1].lower()
    return domain in VERIFIED_DOMAINS

mail = Mail(app)
s    = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# ── Database ──────────────────────────────────────────────────────────────────
# On Vercel /tmp is the only writable directory
DB = "/tmp/requests.db" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "requests.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS resume_requests (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                email   TEXT NOT NULL,
                reason  TEXT,
                status  TEXT DEFAULT 'pending',
                created TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS page_views (
                id    INTEGER PRIMARY KEY CHECK (id = 1),
                total INTEGER DEFAULT 0
            )
        """)
        conn.execute("INSERT OR IGNORE INTO page_views (id, total) VALUES (1, 0)")
        conn.commit()

init_db()

# ── Serve portfolio ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return app.send_static_file("index.html")

# ── Helpers ───────────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def valid_email(e):
    return bool(EMAIL_RE.match(e))

# ── Resume request ────────────────────────────────────────────────────────────
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

    # ── Verified recruiter: instant access ───────────────────────────────────
    if is_verified_recruiter(email):
        try:
            _send_download_email(name, email)
            return jsonify({
                "message": "Verified organization detected! A download link has been sent directly to your email.",
                "verified": True
            })
        except Exception as e:
            return jsonify({"error": f"Mail failed: {str(e)}"}), 500

    # ── Everyone else: needs approval ────────────────────────────────────────

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, status FROM resume_requests WHERE email = ? ORDER BY id DESC LIMIT 1",
            (email,)
        ).fetchone()

        if existing:
            if existing["status"] == "approved":
                _send_download_email(name, email)
                return jsonify({"message": "You are already approved. A download link has been resent to your email."})
            if existing["status"] == "pending":
                return jsonify({"message": "Your request is already pending. You'll be notified once approved."})

        row = conn.execute(
            "INSERT INTO resume_requests (name, email, reason) VALUES (?, ?, ?)",
            (name, email, reason)
        ).lastrowid
        conn.commit()

    approve_token = s.dumps({"id": row, "email": email, "name": name}, salt="approve")
    approve_url   = f"{BASE_URL}/api/approve/{approve_token}"

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
            <a href="{approve_url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Approve Request</a>
            <p style="color:#888;font-size:12px;margin-top:16px;">This approval link is valid for 7 days.</p>
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
        data = s.loads(token, salt="approve", max_age=604800)
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

    try:
        _send_download_email(data.get("name", "there"), email)
    except Exception as e:
        import traceback
        app.logger.error(f"Failed to send download email: {e}\n{traceback.format_exc()}")
        return """
        <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#0a0f1e;color:#e2e8f0;">
            <h2 style="color:#f87171;">Approved but email failed!</h2>
            <p>Could not send email to <b>{}</b>.</p>
            <p style="color:#94a3b8;">Error: {}</p>
        </body></html>
        """.format(email, str(e))

    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#0a0f1e;color:#e2e8f0;">
        <h2 style="color:#6366f1;">Approved!</h2>
        <p>A download link has been sent to <b>{}</b>.</p>
    </body></html>
    """.format(email)

@app.route("/api/download/<token>")
def download_resume(token):
    try:
        data = s.loads(token, salt="download", max_age=86400)
    except SignatureExpired:
        return "<h2 style='font-family:sans-serif'>Download link has expired.</h2>", 400
    except BadSignature:
        return "<h2 style='font-family:sans-serif'>Invalid download link.</h2>", 400

    if not RESUME_URL:
        return "<h2 style='font-family:sans-serif'>Resume not available. Contact dassrijan76@gmail.com</h2>", 404

    from flask import redirect
    return redirect(RESUME_URL)


def _send_download_email(name, email):
    token        = s.dumps({"email": email}, salt="download")
    download_url = f"{BASE_URL}/api/download/{token}"
    try:
        msg = Message(
            subject="Your Resume Download Link - Srijan Das",
            recipients=[email],
            html=f"""
            <h2>Hi {name},</h2>
            <p>Your request to download Srijan Das's resume has been <b>approved</b>.</p>
            <p>Click the button below to download. The link is valid for <b>24 hours</b>.</p>
            <br>
            <a href="{download_url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Download Resume</a>
            <p style="color:#888;font-size:12px;margin-top:16px;">If you did not request this, please ignore this email.</p>
            """
        )
        mail.send(msg)
        app.logger.info(f"Download email sent to {email}")
    except Exception as e:
        import traceback
        app.logger.error(f"Failed to send download email to {email}: {e}\n{traceback.format_exc()}")
        raise


# ── View counter (polling-friendly, no SSE) ───────────────────────────────────
@app.route("/api/views/track", methods=["POST"])
def track_view():
    with get_db() as conn:
        conn.execute("UPDATE page_views SET total = total + 1 WHERE id = 1")
        conn.commit()
        row = conn.execute("SELECT total FROM page_views WHERE id = 1").fetchone()
        return jsonify({"total": row["total"]})

@app.route("/api/views")
def get_views():
    with get_db() as conn:
        row = conn.execute("SELECT total FROM page_views WHERE id = 1").fetchone()
        return jsonify({"total": row["total"] if row else 0})


# ── LeetCode Stats ────────────────────────────────────────────────────────────
_lc_cache = {"data": None, "ts": 0}
LC_CACHE_TTL = 300

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile { ranking }
    submitStats {
      acSubmissionNum { difficulty count }
    }
    badges { id displayName icon }
    userCalendar { streak totalActiveDays }
  }
  userContestRanking(username: $username) {
    attendedContestsCount rating globalRanking topPercentage
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
            headers={"Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = _json.loads(resp.read())

        user    = raw["data"]["matchedUser"]
        contest = raw["data"].get("userContestRanking") or {}
        solved  = {s["difficulty"]: s["count"] for s in user["submitStats"]["acSubmissionNum"]}

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
            return jsonify(_lc_cache["data"])
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
