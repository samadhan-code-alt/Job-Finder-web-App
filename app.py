from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "jobfinder_secret_key"

# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        description TEXT
    )
    """)

    # ✅ JOB APPLICATIONS TABLE
    conn.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        name TEXT,
        email TEXT,
        phone TEXT,
        resume TEXT
    )
    """)
    # user Profile
    conn.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    full_name TEXT,
    age INTEGER,
    birth_date TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tables()

# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- USER REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            
            session["user"]=username
            return redirect("/profile")

        except:
            return render_template(
                "user_register.html",
                error="User already exists"
            )

    return render_template("user_register.html")

# ---------------- USER LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session.clear()
            session["user"] = username
            return redirect("/")
        else:
            return render_template(
                "login.html",
                error="Invalid username or password"
            )

    return render_template("login.html")

# ---------------- USER PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        full_name = request.form["full_name"]
        age = request.form["age"]
        birth_date = request.form["birth_date"]

        conn = get_db()

        conn.execute("""
        INSERT INTO user_profiles
        (username, full_name, age, birth_date)
        VALUES (?, ?, ?, ?)
        """, (
            session["user"],
            full_name,
            age,
            birth_date
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("profile.html")

# ---------------- ADMIN REGISTER ----------------
@app.route("/admin-register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = get_db()
            conn.execute(
                "INSERT INTO admins (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()

            return redirect("/admin-login")

        except:
            return render_template(
                "admin_register.html",
                error="Admin already exists"
            )

    return render_template("admin_register.html")

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admins WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if admin:
            session.clear()
            session["admin"] = username
            return redirect("/admin")
        else:
            return render_template(
                "admin_login.html",
                error="Invalid admin credentials"
            )

    return render_template("admin_login.html")

# ---------------- ADMIN PROCESS ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "admin" not in session:
        return redirect("/admin-login")

    if request.method == "POST":
        conn = get_db()
        conn.execute("""
            INSERT INTO jobs (job_title, company, location, salary, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["job_title"],
            request.form["company"],
            request.form["location"],
            request.form["salary"],
            request.form["description"]
        ))
        conn.commit()
        conn.close()

        return redirect("/admin")

    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    conn.close()

    return render_template("admin.html", jobs=jobs)

# ---------------- VIEW APPLICATIONS (ADMIN) ----------------
@app.route("/admin/applications")
def view_applications():
    if "admin" not in session:
        return redirect("/admin-login")

    conn = get_db()
    applications = conn.execute("""
        SELECT applications.*, jobs.job_title, jobs.company
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
    """).fetchall()
    conn.close()

    return render_template("admin_applications.html", applications=applications)

# ---------------- JOB SEARCH ----------------
@app.route("/search", methods=["POST"])
def search():
    location = request.form["location"]
    job = request.form["job"]

    conn = get_db()
    jobs = conn.execute("""
        SELECT * FROM jobs
        WHERE location LIKE ? AND job_title LIKE ?
    """, (
        f"%{location}%",
        f"%{job}%"
    )).fetchall()
    conn.close()

    return render_template("results.html", jobs=jobs)

# ---------------- APPLY JOB ----------------
@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply_job(job_id):
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        resume = request.form["resume"]

        conn = get_db()
        conn.execute("""
            INSERT INTO applications (job_id, name, email, phone, resume)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, name, email, phone, resume))
        conn.commit()
        conn.close()

        return render_template("apply_success.html")

    conn = get_db()
    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()
    conn.close()

    return render_template("apply.html", job=job)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
