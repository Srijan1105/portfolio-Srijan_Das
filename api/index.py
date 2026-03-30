from flask import Flask, request, jsonify, abort, redirect
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import sqlite3, os, re, time
from datetime import datetime

# Static files live one level up (repo root)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, static_folder=_root, static_url_path="")
CORS(app, origins=["*"])

app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "srijan-portfolio-secret-2026"),
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.environ.get("MAIL_USERNAME"),
)

OWNER_EMAIL       = os.environ.get("OWNER_EMAIL", "dassrijan76@gmail.com")
RESUME_URL        = os.environ.get("RESUME_URL", "")
BASE_URL          = os.environ.get("BASE_URL", "https://portfolio-srijan-das.vercel.app")
LEETCODE_USERNAME = os.environ.get("LEETCODE_USERNAME", "dassrijan76")

VERIFIED_DOMAINS = {
    "google.com","microsoft.com","amazon.com","apple.com","meta.com",
    "netflix.com","adobe.com","salesforce.com","oracle.com","ibm.com",
    "intel.com","nvidia.com","qualcomm.com","cisco.com","vmware.com",
    "tcs.com","infosys.com","wipro.com","hcltech.com","techmahindra.com",
    "capgemini.com","accenture.com","cognizant.com","mphasis.com",
    "ltimindtree.com","hexaware.com","persistent.com","kpit.com",
    "mindtree.com","niit.com","zensar.com","birlasoft.com",
    "flipkart.com","paytm.com","razorpay.com","zomato.com","swiggy.in",
    "ola.com","byjus.com","freshworks.com","zoho.com","browserstack.com",
    "meesho.com","cred.club","phonepe.com","groww.in","zerodha.com",
    "deloitte.com","pwc.com","ey.com","kpmg.com","mckinsey.com",
    "bcg.com","bain.com","jpmorgan.com","goldmansachs.com",
    "linkedin.com","naukri.com","instahyre.com","hirist.com",
}

def is_verified_recruiter(email):
    return email.split("@")[-1].lower() in VERIFIED_DOMAINS

mail = Mail(app)
s    = URLSafeTimedSerializer(app.config["SECRET_KEY"])

DB = "/tmp/requests.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS resume_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT NOT NULL, reason TEXT, status TEXT DEFAULT 'pending',
            created TEXT DEFAULT (datetime('now')))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY CHECK (id=1), total INTEGER DEFAULT 0)""")
        conn.execute("INSERT OR IGNORE INTO page_views (id,total) VALUES (1,0)")
        conn.commit()

init_db()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/request-resume", methods=["POST"])
def request_resume():
    data   = request.get_json(silent=True) or {}
    name   = (data.get("name") or "").strip()
    email  = (data.get("email") or "").strip().lower()
    reason = (data.get("reason") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email address."}), 400

    if is_verified_recruiter(email):
        try:
            _send_download_email(name, email)
            return jsonify({"message": "Verified organization detected! A download link has been sent directly to your email.", "verified": True})
        except Exception as e:
            return jsonify({"error": f"Mail failed: {str(e)}"}), 500

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, status FROM resume_requests WHERE email=? ORDER BY id DESC LIMIT 1", (email,)
        ).fetchone()
        if existing:
            if existing["status"] == "approved":
                _send_download_email(name, email)
                return jsonify({"message": "You are already approved. A download link has been resent."})
            if existing["status"] == "pending":
                return jsonify({"message": "Your request is already pending. You'll be notified once approved."})
        row = conn.execute(
            "INSERT INTO resume_requests (name,email,reason) VALUES (?,?,?)", (name, email, reason)
        ).lastrowid
        conn.commit()

    approve_token = s.dumps({"id": row, "email": email, "name": name}, salt="approve")
    approve_url   = f"{BASE_URL}/api/approve/{approve_token}"

    try:
        msg = Message(
            subject=f"Resume Access Request from {name}",
            recipients=[OWNER_EMAIL],
            html=f"""<h2>New Resume Download Request</h2>
            <p><b>Name:</b> {name}</p><p><b>Email:</b> {email}</p>
            <p><b>Reason:</b> {reason or 'Not provided'}</p>
            <p><b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p><br>
            <a href="{approve_url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Approve Request</a>
            <p style="color:#888;font-size:12px;margin-top:16px;">Valid for 7 days.</p>"""
        )
        mail.send(msg)
    except Exception as e:
        return jsonify({"error": f"Mail failed: {str(e)}"}), 500

    return jsonify({"message": "Request submitted! You'll receive an email once approved."})


@app.route("/api/approve/<token>")
def approve(token):
    try:
        data = s.loads(token, salt="approve", max_age=604800)
    except SignatureExpired:
        return "<h2>Approval link expired.</h2>", 400
    except BadSignature:
        return "<h2>Invalid link.</h2>", 400

    email = data["email"]
    name  = data.get("name", "there")

    with get_db() as conn:
        existing = conn.execute(
            "SELECT status FROM resume_requests WHERE email=? ORDER BY id DESC LIMIT 1", (email,)
        ).fetchone()
        if existing and existing["status"] == "approved":
            pass  # already approved, just resend
        else:
            conn.execute(
                "INSERT OR IGNORE INTO resume_requests (name,email,reason,status) VALUES (?,?,?,?)",
                (name, email, "approved via token", "approved")
            )
            conn.execute(
                "UPDATE resume_requests SET status='approved' WHERE email=?", (email,)
            )
            conn.commit()

    try:
        _send_download_email(name, email)
    except Exception as e:
        return f"""<html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#0a0f1e;color:#e2e8f0;">
            <h2 style="color:#f87171;">Approved but email failed!</h2>
            <p>Error: {str(e)}</p></body></html>"""

    return f"""<html><body style="font-family:sans-serif;text-align:center;padding:60px;background:#0a0f1e;color:#e2e8f0;">
        <h2 style="color:#6366f1;">Approved!</h2>
        <p>Download link sent to <b>{email}</b>.</p></body></html>"""


@app.route("/api/download/<token>")
def download_resume(token):
    try:
        s.loads(token, salt="download", max_age=86400)
    except SignatureExpired:
        return "<h2>Download link expired.</h2>", 400
    except BadSignature:
        return "<h2>Invalid link.</h2>", 400

    if not RESUME_URL:
        return "<h2>Resume unavailable. Contact dassrijan76@gmail.com</h2>", 404
    return redirect(RESUME_URL)


def _send_download_email(name, email):
    token        = s.dumps({"email": email}, salt="download")
    download_url = f"{BASE_URL}/api/download/{token}"
    msg = Message(
        subject="Your Resume Download Link - Srijan Das",
        recipients=[email],
        html=f"""<h2>Hi {name},</h2>
        <p>Your request to download Srijan Das's resume has been <b>approved</b>.</p>
        <p>The link is valid for <b>24 hours</b>.</p><br>
        <a href="{download_url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Download Resume</a>
        <p style="color:#888;font-size:12px;margin-top:16px;">If you did not request this, ignore this email.</p>"""
    )
    mail.send(msg)


@app.route("/api/views/track", methods=["POST"])
def track_view():
    with get_db() as conn:
        conn.execute("UPDATE page_views SET total=total+1 WHERE id=1")
        conn.commit()
        row = conn.execute("SELECT total FROM page_views WHERE id=1").fetchone()
        return jsonify({"total": row["total"]})

@app.route("/api/views")
def get_views():
    with get_db() as conn:
        row = conn.execute("SELECT total FROM page_views WHERE id=1").fetchone()
        return jsonify({"total": row["total"] if row else 0})


# ── GitHub Repos ──────────────────────────────────────────────────────────────
# v2 - featured filter support
_gh_cache = {"data": None, "ts": 0}

# Map keywords in repo name/description/topics to filter categories
CATEGORY_KEYWORDS = {
    "AI":  ["ai", "artificial-intelligence", "nlp", "deep-learning", "neural", "gpt", "llm", "computer-vision", "agriculture"],
    "ML":  ["ml", "machine-learning", "sklearn", "tensorflow", "keras", "pytorch", "prediction", "forecasting", "classification", "regression", "data-science", "pandas", "numpy"],
    "Web": ["web", "flask", "django", "fastapi", "html", "css", "javascript", "react", "node", "frontend", "backend", "api", "portfolio", "website"],
}

# Custom descriptions for repos that lack one on GitHub
REPO_DESCRIPTIONS = {
    "Airline-Management-System": "A Java-based system to streamline airline booking and scheduling operations with centralized data management using JDBC and MySQL.",
    "AI-Based-Smart-Inventory-Management-for-Small-Businesses": "AI-powered inventory management system for small businesses — predicts stock requirements and reduces wastage using machine learning.",
    "AI-Task-Management-": "An AI-driven task management application that prioritizes and organizes tasks intelligently based on deadlines and workload.",
    "BANK-MANAGEMENT-SYSTEM": "A complete bank management system built in Java supporting account creation, transactions, and balance management with a MySQL backend.",
    "Company_Profit_Prediction-": "Machine learning model to predict company profit based on R&D spend, administration, and marketing data using regression techniques.",
    "Deforestation-Monitoring": "A data-driven system to monitor and analyze deforestation patterns using satellite data and visualization tools.",
    "Empowering-Small-and-Marginal-Farmers-with-AI-Driven-Agricultural-Solutions": "AI platform providing personalized crop recommendations, weather insights, and market price predictions to empower small-scale farmers.",
    "FreelanceHub": "A web platform connecting freelancers with clients, featuring project listings, bidding, and profile management.",
    "Gas-Detection-System": "IoT-based gas detection system that monitors hazardous gas levels and triggers real-time alerts for safety.",
    "IPL-2025-Winner-Prediction": "Machine learning model predicting IPL 2025 match winners using historical match data, player stats, and team performance metrics.",
    "Mobile_Sales_Dashboard": "Interactive Power BI dashboard analyzing mobile sales trends, revenue, and customer demographics across regions.",
    "Movie-Recommender": "Content-based movie recommendation system using cosine similarity on TF-IDF vectors built with Python and Scikit-learn.",
    "MovieX": "A movie discovery web app with search, filtering, and detailed movie information powered by a public movie API.",
    "Retail_Sales_Forcasting": "Data analysis and forecasting model for retail sales using EDA, feature engineering, and evaluation with RMSE and R² metrics.",
    "Stock-Price-Prediction": "LSTM-based deep learning model to predict stock prices using historical market data and time-series analysis.",
    "Traffic-Flow-Prediction-System": "Machine learning system to predict urban traffic flow patterns and congestion using historical traffic data.",
    "Weather-App": "A responsive weather application that fetches real-time weather data and forecasts using a public weather API.",
    "portfolio-Srijan_Das": "Personal portfolio website built with Flask, HTML, CSS, and JavaScript — featuring live LeetCode stats, GitHub projects, and a resume request system.",
    "one-compiler": "An online code compiler interface supporting multiple programming languages with real-time execution.",
    "Hack4Bengal4.0---Team-NextGen": "Hackathon project from Hack4Bengal 4.0 — built by Team NextGen to solve a real-world problem using technology.",
}

FEATURED_REPOS = {
    "Mobile_Sales_Dashboard",
    "Airline-Management-System",
    "Retail_Sales_Forcasting",
    "Hack4Bengal4.0---Team-NextGen",  # Pathfinder
    "FreelanceHub",                    # FoodBridge if renamed
    "IPL-2025-Winner-Prediction",
}

# Override categories for specific repos
CATEGORY_OVERRIDES = {
    "Mobile_Sales_Dashboard": ["ML"],  # Power BI + MySQL, not Web
}

def get_description(repo):
    name = repo.get("name", "")
    return REPO_DESCRIPTIONS.get(name) or repo.get("description") or "No description provided."

CATEGORY_KEYWORDS = {
    "AI":  ["ai", "artificial-intelligence", "nlp", "deep-learning", "neural", "gpt", "llm", "computer-vision", "agriculture", "smart", "prediction", "recommender"],
    "ML":  ["ml", "machine-learning", "sklearn", "tensorflow", "keras", "pytorch", "forecasting", "classification", "regression", "data-science", "pandas", "numpy", "sales", "stock", "traffic", "profit"],
    "Web": ["web", "flask", "django", "fastapi", "html", "css", "javascript", "react", "node", "frontend", "backend", "api", "portfolio", "website", "app", "dashboard", "compiler"],
}

def categorize_repo(repo):
    name = repo.get("name", "")
    if name in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[name]
    cats = set()
    text = " ".join([
        (repo.get("name") or ""),
        (repo.get("description") or ""),
        (repo.get("language") or ""),
        " ".join(repo.get("topics") or [])
    ]).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            cats.add(cat)
    return list(cats) if cats else ["Other"]
    cats = set()
    text = " ".join([
        (repo.get("name") or ""),
        (repo.get("description") or ""),
        (repo.get("language") or ""),
        " ".join(repo.get("topics") or [])
    ]).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            cats.add(cat)
    return list(cats) if cats else ["Other"]

@app.route("/api/github-repos")
def github_repos():
    global _gh_cache
    now = time.time()
    if _gh_cache["data"] and (now - _gh_cache["ts"]) < 300:
        return jsonify(_gh_cache["data"])
    try:
        import urllib.request, json as _json
        req = urllib.request.Request(
            "https://api.github.com/users/Srijan1105/repos?per_page=100&sort=updated",
            headers={"User-Agent": "portfolio-app", "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos = _json.loads(resp.read())

        result = []
        for r in repos:
            if r.get("fork"):
                continue
            if r["name"] in ("portfolio-Srijan_Das", "Srijan1105"):
                continue
            result.append({
                "name":        r["name"],
                "description": get_description(r),
                "url":         r["html_url"],
                "homepage":    r.get("homepage") or "",
                "language":    r.get("language") or "",
                "topics":      r.get("topics") or [],
                "stars":       r.get("stargazers_count", 0),
                "updated":     r.get("updated_at", "")[:10],
                "categories":  categorize_repo(r),
                "featured":    r["name"] in FEATURED_REPOS,
            })
        # Sort: featured first, then by updated
        result.sort(key=lambda x: (not x["featured"], x["updated"]), reverse=False)
        result.sort(key=lambda x: not x["featured"])

        _gh_cache = {"data": result, "ts": now}
        return jsonify(result)
    except Exception as e:
        if _gh_cache["data"]:
            return jsonify(_gh_cache["data"])
        return jsonify({"error": str(e)}), 500


# ── LeetCode Stats ────────────────────────────────────────────────────────────
_lc_cache = {"data": None, "ts": 0}

@app.route("/api/leetcode")
def leetcode_stats():
    global _lc_cache
    now = time.time()
    if _lc_cache["data"] and (now - _lc_cache["ts"]) < 300:
        return jsonify(_lc_cache["data"])
    try:
        import urllib.request, json as _json
        query = """query getUserProfile($username: String!) {
          matchedUser(username: $username) {
            username profile { ranking }
            submitStats { acSubmissionNum { difficulty count } }
            badges { id displayName icon }
            userCalendar { streak totalActiveDays }
          }
          userContestRanking(username: $username) {
            attendedContestsCount rating globalRanking topPercentage
          }
        }"""
        payload = _json.dumps({"query": query, "variables": {"username": LEETCODE_USERNAME}}).encode()
        req = urllib.request.Request("https://leetcode.com/graphql", data=payload,
            headers={"Content-Type":"application/json","Referer":"https://leetcode.com","User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = _json.loads(resp.read())
        user    = raw["data"]["matchedUser"]
        contest = raw["data"].get("userContestRanking") or {}
        solved  = {x["difficulty"]: x["count"] for x in user["submitStats"]["acSubmissionNum"]}
        result  = {
            "username": user["username"], "ranking": user["profile"]["ranking"],
            "totalSolved": solved.get("All",0), "easySolved": solved.get("Easy",0),
            "mediumSolved": solved.get("Medium",0), "hardSolved": solved.get("Hard",0),
            "streak": (user["userCalendar"] or {}).get("streak", 0),
            "totalActiveDays": (user["userCalendar"] or {}).get("totalActiveDays", 0),
            "badges": [{"name": b["displayName"], "icon": b["icon"]} for b in (user.get("badges") or [])],
            "contestsAttended": contest.get("attendedContestsCount", 0),
            "contestRating": round(contest.get("rating", 0)),
            "contestGlobalRanking": contest.get("globalRanking", "N/A"),
            "contestTopPercentage": round(contest.get("topPercentage", 0), 1) if contest.get("topPercentage") else "N/A",
        }
        _lc_cache = {"data": result, "ts": now}
        return jsonify(result)
    except Exception as e:
        if _lc_cache["data"]:
            return jsonify(_lc_cache["data"])
        return jsonify({"error": str(e)}), 500
