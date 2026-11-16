# app.py - TUMA Login System kwa Python
from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = "tuma-secret-key-2026"  # Badilisha hii kwa siri yako

# --- 1. TENGENEZA DATABASE ---
def init_db():
    conn = sqlite3.connect("tuma.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'voter'
        )
    """)
    # Tengeneza Admin na Mwanafunzi wa kujaribu kama hawapo
    # Password ya Admin ni: admin123
    # Password ya Mwanafunzi ni: 12345
    admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
    student_pass = hashlib.sha256("12345".encode()).hexdigest()
    
    cur.execute("INSERT OR IGNORE INTO users (full_name, student_id, password, role) VALUES (?,?,?,?)",
                ("Admin TUMA", "ADMIN001", admin_pass, "admin"))
    cur.execute("INSERT OR IGNORE INTO users (full_name, student_id, password, role) VALUES (?,?,?,?)",
                ("Neema Joseph", "TUMA001", student_pass, "voter"))
    conn.commit()
    conn.close()

init_db()

# --- 2. UKURASA WA LOGIN ---
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head><title>TUMA Login</title>
<style>
body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;padding:40px}
.card{background:white;padding:30px;border-radius:12px;width:350px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box}
button{background:#1a3a5c;color:white;padding:12px;border:none;border-radius:8px;width:100%;font-weight:bold;cursor:pointer}
.error{color:red;background:#ffe6e6;padding:10px;border-radius:8px}
.success{color:green;background:#e6ffe6;padding:10px;border-radius:8px}
</style>
</head>
<body>
<div class="card">
<h2 style="text-align:center">TUMA - Ingia</h2>
<p style="text-align:center;color:#666">Mfumo wa Uchaguzi wa Wanafunzi</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
{% if success %}<p class="success">{{ success }}</p>{% endif %}
<form method="POST">
<input name="student_id" placeholder="Student ID - mfano TUMA001" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">INGIA</button>
</form>
<p style="text-align:center">Hauna account? <a href="/register">Jisajili</a></p>
<hr>
<p style="font-size:13px;background:#f8f9fa;padding:10px;border-radius:8px">
<b>Kujaribu:</b><br>
Admin: ADMIN001 / admin123<br>
Mwanafunzi: TUMA001 / 12345
</p>
</div>
</body>
</html>
"""

# --- 3. UKURASA BAADA YA KUINGIA ---
DASHBOARD_PAGE = """
<!DOCTYPE html>
<html><head><title>Karibu</title>
<style>body{font-family:Arial;background:#f0f2f5;padding:40px;text-align:center}.card{background:white;padding:30px;border-radius:12px;max-width:500px;margin:auto}</style>
</head><body><div class="card">
<h2>Karibu, {{ name }}! 🎉</h2>
<p>Umefanikiwa kuingia!</p>
<p><b>Student ID:</b> {{ student_id }}<br><b>Role:</b> {{ role }}</p>
{% if role == 'admin' %}
<p style="background:#e6f0ff;padding:10px;border-radius:8px">Wewe ni <b>Admin</b> - Unaweza kusimamia uchaguzi.</p>
{% else %}
<p style="background:#e6ffe6;padding:10px;border-radius:8px">Wewe ni <b>Mpiga Kura</b> - Unaweza kupiga kura sasa.</p>
{% endif %}
<a href="/logout"><button style="background:red;color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer">TOKA (Logout)</button></a>
</div></body></html>
"""

# --- 4. UKURASA WA KUJISAJILI ---
REGISTER_PAGE = """
<!DOCTYPE html>
<html><head><title>Jisajili</title>
<style>body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;padding:40px}.card{background:white;padding:30px;border-radius:12px;width:350px}input{width:100%;padding:12px;margin:8px 0;border-radius:8px;border:1px solid #ddd;box-sizing:border-box}button{background:#2a7a3b;color:white;padding:12px;border:none;border-radius:8px;width:100%;font-weight:bold}</style>
</head><body><div class="card">
<h2>Jisajili</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
<input name="full_name" placeholder="Jina Kamili" required>
<input name="student_id" placeholder="Student ID" required>
<input type="password" name="password" placeholder="Password" required>
<button>JISAJILI</button></form>
<p><a href="/">Rudi kwenye Login</a></p></div></body></html>
"""

# --- 5. ROUTES - HII NDIO LOGIC YA LOGIN ---

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        student_id = request.form["student_id"]
        password = request.form["password"]
        # Badilisha password kuwa hash ili kulinganisha na iliyohifadhiwa
        hashed = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect("tuma.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE student_id=? AND password=?", (student_id, hashed))
        user = cur.fetchone()
        conn.close()

        if user:
            # HIFADHI KWENYE SESSION - HII NDIO "AMEINGIA"
            session["user_id"] = user[0]
            session["name"] = user[1]
            session["student_id"] = user[2]
            session["role"] = user[4]
            return redirect("/dashboard")
        else:
            return render_template_string(LOGIN_PAGE, error="Student ID au Password sio sahihi!")
    return render_template_string(LOGIN_PAGE)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["full_name"]
        sid = request.form["student_id"]
        hashed = hashlib.sha256(request.form["password"].encode()).hexdigest()
        try:
            conn = sqlite3.connect("tuma.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO users (full_name, student_id, password) VALUES (?,?,?)", (name, sid, hashed))
            conn.commit()
            conn.close()
            return render_template_string(LOGIN_PAGE, success="Umejisajili! Sasa ingia.")
        except:
            return render_template_string(REGISTER_PAGE, error="Student ID hii imeshatumika!")
    return render_template_string(REGISTER_PAGE)

@app.route("/dashboard")
def dashboard():
    # Kama hakuingia, mrudishe kwenye login
    if "user_id" not in session:
        return redirect("/")
    return render_template_string(DASHBOARD_PAGE, name=session["name"], student_id=session["student_id"], role=session["role"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
