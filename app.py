from flask import Flask, render_template, request, redirect, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_123"  # Change this for security

CANDIDATES = ["Alice", "Bob", "Charlie"]

# Ensure necessary files/directories
os.makedirs("data", exist_ok=True)
if not os.path.exists("data/votes.json"):
    with open("data/votes.json", "w") as f:
        json.dump({name: 0 for name in CANDIDATES}, f)

if not os.path.exists("users.json"):
    with open("users.json", "w") as f:
        json.dump({}, f)

# ----------- UTILITIES -----------
def is_admin():
    return session.get("username") == "admin"

# ----------- HOME -----------
@app.route("/")
def index():
    return render_template("index.html")

# ----------- REGISTER -----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open("users.json", "r+") as f:
            users = json.load(f)

            if username in users:
                flash("Username already exists!", "error")
                return redirect("/register")

            users[username] = {
                "password": generate_password_hash(password),
                "voted": False
            }

            f.seek(0)
            json.dump(users, f)
            f.truncate()

        flash("Registered successfully. Please log in.", "success")
        return redirect("/login")

    return render_template("register.html")

# ----------- LOGIN -----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with open("users.json", "r") as f:
            users = json.load(f)

        if username in users and check_password_hash(users[username]["password"], password):
            session["username"] = username
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid username or password", "error")
            return redirect("/login")

    return render_template("login.html")

# ----------- LOGOUT -----------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect("/")

# ----------- VOTE -----------
@app.route("/vote")
def vote():
    if "username" not in session:
        flash("You must log in to vote.", "error")
        return redirect("/login")

    username = session["username"]

    with open("users.json", "r") as f:
        users = json.load(f)

    if users[username]["voted"]:
        flash("You have already voted. Thank you!", "info")
        return redirect("/results")

    return render_template("vote.html", candidates=CANDIDATES)

# ----------- SUBMIT VOTE -----------
@app.route("/submit_vote", methods=["POST"])
def submit_vote():
    if "username" not in session:
        flash("You must be logged in to vote.", "error")
        return redirect("/login")

    username = session["username"]
    name = request.form["candidate"]

    if name not in CANDIDATES:
        return "Invalid candidate!", 400

    with open("users.json", "r+") as user_file:
        users = json.load(user_file)

        if users[username]["voted"]:
            flash("You have already voted!", "info")
            return redirect("/results")

        users[username]["voted"] = True

        user_file.seek(0)
        json.dump(users, user_file)
        user_file.truncate()

    with open("data/votes.json", "r+") as f:
        data = json.load(f)
        data[name] += 1
        f.seek(0)
        json.dump(data, f)
        f.truncate()

    flash("Vote submitted successfully!", "success")
    return redirect("/results")

# ----------- PUBLIC RESULTS -----------
@app.route("/results")
def results():
    try:
        with open("data/votes.json", "r") as f:
            data = json.load(f)
    except:
        data = {}

    return render_template("results.html", votes=data)

# ----------- API FOR CHART -----------
@app.route("/api/results")
def api_results():
    try:
        with open("data/votes.json", "r") as f:
            data = json.load(f)
        return jsonify(data)
    except:
        return jsonify({})

# ----------- ADMIN PANEL -----------
@app.route("/admin")
def admin_panel():
    if not is_admin():
        flash("Access denied. Admins only.", "error")
        return redirect("/")

    with open("data/votes.json", "r") as f:
        vote_data = json.load(f)

    return render_template("admin.html", votes=vote_data, candidates=CANDIDATES)

@app.route("/admin/reset_votes")
def reset_votes():
    if not is_admin():
        return "Unauthorized", 403

    with open("data/votes.json", "w") as f:
        json.dump({name: 0 for name in CANDIDATES}, f)

    with open("users.json", "r+") as f:
        users = json.load(f)
        for user in users:
            users[user]["voted"] = False
        f.seek(0)
        json.dump(users, f)
        f.truncate()

    flash("Votes and user status reset.", "info")
    return redirect("/admin")

@app.route("/admin/add_candidate", methods=["POST"])
def add_candidate():
    if not is_admin():
        return "Unauthorized", 403

    new_name = request.form["name"].strip()

    if new_name and new_name not in CANDIDATES:
        CANDIDATES.append(new_name)

        with open("data/votes.json", "r+") as f:
            data = json.load(f)
            data[new_name] = 0
            f.seek(0)
            json.dump(data, f)
            f.truncate()

        flash(f"Candidate '{new_name}' added.", "success")
    else:
        flash("Invalid or duplicate candidate name.", "error")

    return redirect("/admin")

# ----------- DISABLE CACHE -----------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# ----------- RUN -----------
if __name__ == "__main__":
    app.run(debug=True)
