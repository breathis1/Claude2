from flask import Flask, render_template, request, jsonify, send_file
import requests
import json
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data/saved.json"

def load_saved():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def search_reddit(keyword, min_members=0, activity="all"):
    results = []
    headers = {"User-Agent": "Nichify/1.0"}
    try:
        url = f"https://www.reddit.com/search.json?q={keyword}&type=sr&limit=25"
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        for item in data.get("data", {}).get("children", []):
            s = item["data"]
            members = s.get("subscribers") or 0
            if members < min_members:
                continue
            # Activity filter
            active_users = s.get("accounts_active") or 0
            if activity == "active" and active_users < 100:
                continue
            if activity == "dead" and active_users >= 100:
                continue
            results.append({
                "platform": "Reddit",
                "name": s.get("display_name_prefixed", ""),
                "title": s.get("title", ""),
                "description": (s.get("public_description") or "")[:200],
                "members": members,
                "active_users": active_users,
                "url": f"https://reddit.com{s.get('url', '')}",
                "type": classify_intent(s.get("public_description", "") + " " + s.get("title", "")),
                "saved": False
            })
    except Exception as e:
        print(f"Reddit error: {e}")
    return results

def search_forums(keyword):
    results = []
    headers = {"User-Agent": "Nichify/1.0"}
    try:
        # Search for forums via DuckDuckGo HTML (no API key needed)
        query = f"{keyword} forum site:reddit.com OR site:forum OR inurl:forum"
        url = f"https://html.duckduckgo.com/html/?q={keyword}+biohacking+forum+community"
        res = requests.get(url, headers=headers, timeout=10)
        # Parse basic links from DuckDuckGo HTML
        from html.parser import HTMLParser

        class LinkParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
                self.current_text = ""
                self.in_result = False

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and "uddg" in attrs_dict.get("href", ""):
                    href = attrs_dict["href"]
                    if any(x in href for x in ["forum", "community", "board", "discuss"]):
                        self.links.append(href)

        parser = LinkParser()
        parser.feed(res.text)

        seen = set()
        for link in parser.links[:8]:
            if link not in seen:
                seen.add(link)
                name = link.split("/")[2] if len(link.split("/")) > 2 else link
                results.append({
                    "platform": "Forum",
                    "name": name,
                    "title": name,
                    "description": f"Forum community related to {keyword}",
                    "members": 0,
                    "active_users": 0,
                    "url": link,
                    "type": "Mixed",
                    "saved": False
                })
    except Exception as e:
        print(f"Forum search error: {e}")

    # Also add known health/biohacking forums
    known_forums = [
        {"name": "longecity.org", "title": "Longecity - Immortality Institute", "url": "https://www.longecity.org/forum/", "description": "Leading forum for biohackers, nootropics, and life extension enthusiasts.", "type": "Buyers"},
        {"name": "biohack.me", "title": "Biohack.me Community", "url": "https://forum.biohack.me", "description": "Community for grinders and DIY biohackers."},
        {"name": "reddit.com/r/Biohackers", "title": "r/Biohackers", "url": "https://www.reddit.com/r/Biohackers/", "description": "Biohacking community on Reddit."},
        {"name": "quantifiedself.com", "title": "Quantified Self Forum", "url": "https://forum.quantifiedself.com", "description": "Self-tracking and health optimization community."},
        {"name": "peaknootropics.com", "title": "Peak Nootropics Community", "url": "https://www.reddit.com/r/nootropics/", "description": "Nootropics and cognitive enhancement community."},
    ]

    kw_lower = keyword.lower()
    for f in known_forums:
        desc = f.get("description", "").lower()
        title = f.get("title", "").lower()
        if any(k in desc or k in title or k in kw_lower for k in [kw_lower, "biohack", "health", "quantum", "optim", "longev"]):
            results.append({
                "platform": "Forum",
                "name": f["name"],
                "title": f["title"],
                "description": f.get("description", ""),
                "members": 0,
                "active_users": 0,
                "url": f["url"],
                "type": f.get("type", "Mixed"),
                "saved": False
            })

    return results

def classify_intent(text):
    text = text.lower()
    buyer_words = ["buy", "sell", "product", "service", "recommend", "review", "purchase", "coach", "consult", "hire", "price", "cost", "deal", "offer"]
    learner_words = ["learn", "study", "beginner", "question", "help", "how to", "advice", "newbie", "guide", "tutorial"]
    buyer_score = sum(1 for w in buyer_words if w in text)
    learner_score = sum(1 for w in learner_words if w in text)
    if buyer_score > learner_score:
        return "Buyers"
    elif learner_score > buyer_score:
        return "Learners"
    return "Mixed"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search")
def search():
    keyword = request.args.get("q", "").strip()
    platform = request.args.get("platform", "all")
    min_members = int(request.args.get("min_members", 0))
    activity = request.args.get("activity", "all")
    intent = request.args.get("intent", "all")

    if not keyword:
        return render_template("index.html", error="Please enter a keyword.")

    results = []

    if platform in ("all", "reddit"):
        results += search_reddit(keyword, min_members, activity)

    if platform in ("all", "forum"):
        results += search_forums(keyword)

    # Filter by intent
    if intent != "all":
        results = [r for r in results if r["type"] == intent]

    # Mark saved ones
    saved = load_saved()
    saved_urls = {s["url"] for s in saved}
    for r in results:
        r["saved"] = r["url"] in saved_urls

    return render_template("results.html", results=results, keyword=keyword, count=len(results))

@app.route("/save", methods=["POST"])
def save_community():
    data = request.json
    saved = load_saved()
    urls = {s["url"] for s in saved}
    if data["url"] not in urls:
        data["saved_at"] = datetime.now().strftime("%Y-%m-%d")
        data["notes"] = ""
        saved.append(data)
        save_data(saved)
    return jsonify({"status": "saved"})

@app.route("/unsave", methods=["POST"])
def unsave_community():
    data = request.json
    saved = load_saved()
    saved = [s for s in saved if s["url"] != data["url"]]
    save_data(saved)
    return jsonify({"status": "removed"})

@app.route("/saved")
def saved_page():
    saved = load_saved()
    return render_template("saved.html", saved=saved)

@app.route("/notes", methods=["POST"])
def update_notes():
    data = request.json
    saved = load_saved()
    for s in saved:
        if s["url"] == data["url"]:
            s["notes"] = data["notes"]
    save_data(saved)
    return jsonify({"status": "updated"})

@app.route("/export")
def export_csv():
    saved = load_saved()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["platform", "name", "title", "description", "members", "active_users", "url", "type", "saved_at", "notes"])
    writer.writeheader()
    for row in saved:
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="nichify_saved.csv"
    )

if __name__ == "__main__":
    app.run(debug=True)
