from flask import Flask, render_template, request, redirect, jsonify
import json
import os

app = Flask(__name__)

# List of candidates
CANDIDATES = ["Alice", "Bob", "Charlie"]

# Ensure votes.json file exists with all values set to 0
if not os.path.exists("data/votes.json"):
    os.makedirs("data", exist_ok=True)
    with open("data/votes.json", "w") as f:
        json.dump({name: 0 for name in CANDIDATES}, f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/vote")
def vote():
    return render_template("vote.html", candidates=CANDIDATES)

@app.route("/submit_vote", methods=["POST"])
def submit_vote():
    name = request.form["candidate"]

    # Validate candidate name
    if name not in CANDIDATES:
        return "Invalid candidate!", 400

    with open("data/votes.json", "r+") as f:
        data = json.load(f)
        data[name] += 1
        f.seek(0)
        json.dump(data, f)
        f.truncate()

    return redirect("/results")

@app.route("/results")
def results():
    with open("data/votes.json", "r") as f:
        data = json.load(f)
    return render_template("results.html", votes=data)

@app.route("/api/results")
def api_results():
    with open("data/votes.json", "r") as f:
        data = json.load(f)
    return jsonify(data)

# Optional: prevent browser from caching /api/results
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

if __name__ == "__main__":
    app.run(debug=True)
