import os

os.makedirs("nichify/static", exist_ok=True)
os.makedirs("nichify/templates", exist_ok=True)
os.makedirs("nichify/data", exist_ok=True)

files = {}

files["requirements.txt"] = "flask\nrequests\n"

files["app.py"] = '''from flask import Flask, render_template, request, jsonify, send_file
import requests, json, os, csv, io
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "data/saved.json"

def load_saved():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE) as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2)

def classify_intent(text):
    text = text.lower()
    b = sum(1 for w in ["buy","sell","product","service","recommend","review","purchase","coach","consult","hire","price","cost","deal","offer"] if w in text)
    l = sum(1 for w in ["learn","study","beginner","question","help","how to","advice","newbie","guide","tutorial"] if w in text)
    return "Buyers" if b > l else ("Learners" if l > b else "Mixed")

def search_reddit(keyword, min_members=0, activity="all"):
    results = []
    try:
        url = f"https://www.reddit.com/search.json?q={keyword}&type=sr&limit=25"
        res = requests.get(url, headers={"User-Agent": "Nichify/1.0"}, timeout=10)
        for item in res.json().get("data", {}).get("children", []):
            s = item["data"]
            members = s.get("subscribers") or 0
            active = s.get("accounts_active") or 0
            if members < min_members: continue
            if activity == "active" and active < 100: continue
            if activity == "dead" and active >= 100: continue
            results.append({"platform":"Reddit","name":s.get("display_name_prefixed",""),"title":s.get("title",""),"description":(s.get("public_description") or "")[:200],"members":members,"active_users":active,"url":f"https://reddit.com{s.get(chr(39)+'url'+chr(39),chr(39)+chr(39))}","type":classify_intent(s.get("public_description","")+" "+s.get("title","")),"saved":False})
    except Exception as e: print(f"Reddit error: {e}")
    return results

def search_forums(keyword):
    known = [
        {"name":"longecity.org","title":"Longecity - Immortality Institute","url":"https://www.longecity.org/forum/","description":"Leading forum for biohackers, nootropics, and life extension enthusiasts.","type":"Buyers"},
        {"name":"biohack.me","title":"Biohack.me Community","url":"https://forum.biohack.me","description":"Community for grinders and DIY biohackers.","type":"Mixed"},
        {"name":"quantifiedself.com","title":"Quantified Self Forum","url":"https://forum.quantifiedself.com","description":"Self-tracking and health optimization community.","type":"Mixed"},
        {"name":"reddit.com/r/nootropics","title":"r/Nootropics","url":"https://www.reddit.com/r/nootropics/","description":"Nootropics and cognitive enhancement community.","type":"Buyers"},
        {"name":"reddit.com/r/Biohackers","title":"r/Biohackers","url":"https://www.reddit.com/r/Biohackers/","description":"Biohacking community on Reddit.","type":"Mixed"},
    ]
    kw = keyword.lower()
    return [{"platform":"Forum","name":f["name"],"title":f["title"],"description":f.get("description",""),"members":0,"active_users":0,"url":f["url"],"type":f.get("type","Mixed"),"saved":False} for f in known if any(k in f.get("description","").lower() or k in f.get("title","").lower() or k in kw for k in [kw,"biohack","health","quantum","optim","longev","noot"])]

@app.route("/")
def index(): return render_template("index.html")

@app.route("/search")
def search():
    keyword = request.args.get("q","").strip()
    platform = request.args.get("platform","all")
    min_members = int(request.args.get("min_members",0))
    activity = request.args.get("activity","all")
    intent = request.args.get("intent","all")
    if not keyword: return render_template("index.html", error="Please enter a keyword.")
    results = []
    if platform in ("all","reddit"): results += search_reddit(keyword, min_members, activity)
    if platform in ("all","forum"): results += search_forums(keyword)
    if intent != "all": results = [r for r in results if r["type"] == intent]
    saved_urls = {s["url"] for s in load_saved()}
    for r in results: r["saved"] = r["url"] in saved_urls
    return render_template("results.html", results=results, keyword=keyword, count=len(results))

@app.route("/save", methods=["POST"])
def save_community():
    data = request.json
    saved = load_saved()
    if data["url"] not in {s["url"] for s in saved}:
        data["saved_at"] = datetime.now().strftime("%Y-%m-%d")
        data["notes"] = ""
        saved.append(data)
        save_data(saved)
    return jsonify({"status":"saved"})

@app.route("/unsave", methods=["POST"])
def unsave_community():
    data = request.json
    save_data([s for s in load_saved() if s["url"] != data["url"]])
    return jsonify({"status":"removed"})

@app.route("/saved")
def saved_page(): return render_template("saved.html", saved=load_saved())

@app.route("/notes", methods=["POST"])
def update_notes():
    data = request.json
    saved = load_saved()
    for s in saved:
        if s["url"] == data["url"]: s["notes"] = data["notes"]
    save_data(saved)
    return jsonify({"status":"updated"})

@app.route("/export")
def export_csv():
    saved = load_saved()
    output = io.StringIO()
    fields = ["platform","name","title","description","members","active_users","url","type","saved_at","notes"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in saved: writer.writerow({k: row.get(k,"") for k in fields})
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name="nichify_saved.csv")

if __name__ == "__main__":
    app.run(debug=True)
'''

files["static/style.css"] = """:root{--pink:#ff1493;--pink-light:#ff69b4;--pink-pale:#ffe4f0;--pink-dark:#c0005a;--dark:#1a1a2e;--text:#222;--muted:#777;--border:#f0c0d8}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#fdf0f7;color:var(--text);min-height:100vh}
nav{background:var(--pink);padding:0 2rem;display:flex;align-items:center;justify-content:space-between;height:60px;box-shadow:0 2px 12px rgba(255,20,147,.3)}
.logo{font-size:1.6rem;font-weight:800;color:white;text-decoration:none}
.logo span{opacity:.7;font-weight:400;font-size:1rem;margin-left:4px}
nav a{color:rgba(255,255,255,.9);text-decoration:none;font-weight:600;font-size:.95rem;padding:6px 14px;border-radius:20px;transition:background .2s}
nav a:hover{background:rgba(255,255,255,.2)}
nav a.active{background:white;color:var(--pink)}
.hero{text-align:center;padding:60px 1rem 40px}
.hero h1{font-size:2.4rem;font-weight:800;color:var(--dark);margin-bottom:10px}
.hero h1 span{color:var(--pink)}
.hero p{color:var(--muted);font-size:1.05rem;margin-bottom:30px}
.search-box{max-width:680px;margin:0 auto;background:white;border-radius:16px;padding:28px;box-shadow:0 4px 24px rgba(255,20,147,.1);border:1.5px solid var(--border)}
.search-row{display:flex;gap:10px;margin-bottom:16px}
.search-row input{flex:1;padding:12px 18px;border:2px solid var(--border);border-radius:10px;font-size:1rem;outline:none}
.search-row input:focus{border-color:var(--pink)}
.btn-pink{background:var(--pink);color:white;border:none;padding:12px 24px;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer;white-space:nowrap}
.btn-pink:hover{background:var(--pink-dark)}
.filters{display:flex;gap:10px;flex-wrap:wrap}
.filters select{flex:1;min-width:130px;padding:9px 12px;border:2px solid var(--border);border-radius:8px;font-size:.9rem;background:white;outline:none;cursor:pointer}
.filters select:focus{border-color:var(--pink)}
.results-header{max-width:900px;margin:24px auto 10px;padding:0 1rem;display:flex;align-items:center;justify-content:space-between}
.results-header h2{font-size:1.2rem;color:var(--dark)}
.count{background:var(--pink-pale);color:var(--pink-dark);font-weight:700;padding:4px 12px;border-radius:20px;font-size:.9rem}
.results-grid{max-width:900px;margin:0 auto;padding:0 1rem 3rem;display:grid;gap:14px}
.card{background:white;border-radius:14px;padding:20px;border:1.5px solid var(--border);box-shadow:0 2px 10px rgba(255,20,147,.06);display:flex;gap:16px;align-items:flex-start;transition:box-shadow .2s,transform .15s}
.card:hover{box-shadow:0 6px 24px rgba(255,20,147,.15);transform:translateY(-2px)}
.card-icon{width:44px;height:44px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}
.card-icon.reddit{background:#ff4500;color:white}
.card-icon.forum{background:var(--pink-pale);color:var(--pink)}
.card-body{flex:1;min-width:0}
.card-title{font-size:1rem;font-weight:700;color:var(--dark);margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-desc{font-size:.88rem;color:var(--muted);margin-bottom:10px;line-height:1.5}
.card-meta{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.badge{font-size:.78rem;padding:3px 10px;border-radius:20px;font-weight:600}
.badge-platform{background:#f0f0f0;color:#555}
.badge-buyers{background:#e8f5e9;color:#2e7d32}
.badge-learners{background:#e3f2fd;color:#1565c0}
.badge-mixed{background:#fff3e0;color:#e65100}
.card-stats{font-size:.8rem;color:var(--muted)}
.card-actions{display:flex;flex-direction:column;gap:8px;align-items:flex-end;flex-shrink:0}
.btn-save{background:var(--pink-pale);color:var(--pink);border:1.5px solid var(--pink-light);padding:7px 14px;border-radius:8px;font-size:.85rem;font-weight:700;cursor:pointer;transition:all .2s;white-space:nowrap}
.btn-save:hover,.btn-save.saved{background:var(--pink);color:white}
.btn-visit{color:var(--pink);font-size:.82rem;font-weight:600;text-decoration:none}
.btn-visit:hover{text-decoration:underline}
.page-header{max-width:900px;margin:30px auto 10px;padding:0 1rem;display:flex;align-items:center;justify-content:space-between}
.page-header h1{font-size:1.5rem;font-weight:800;color:var(--dark)}
.btn-export{background:white;color:var(--pink);border:2px solid var(--pink);padding:9px 20px;border-radius:9px;font-size:.9rem;font-weight:700;text-decoration:none;transition:all .2s}
.btn-export:hover{background:var(--pink);color:white}
.notes-input{width:100%;margin-top:8px;padding:7px 10px;border:1.5px solid var(--border);border-radius:7px;font-size:.85rem;resize:none;outline:none;font-family:inherit}
.notes-input:focus{border-color:var(--pink)}
.saved-date{font-size:.78rem;color:var(--muted);margin-top:4px}
.btn-remove{background:#fff0f0;color:#c0392b;border:1.5px solid #f5b7b1;padding:6px 12px;border-radius:7px;font-size:.82rem;font-weight:600;cursor:pointer;transition:all .2s}
.btn-remove:hover{background:#c0392b;color:white}
.empty{text-align:center;padding:60px 1rem;color:var(--muted)}
.empty .icon{font-size:3rem;margin-bottom:12px}
.empty h3{font-size:1.2rem;margin-bottom:6px;color:var(--dark)}
.toast{position:fixed;bottom:24px;right:24px;background:var(--pink);color:white;padding:12px 22px;border-radius:10px;font-weight:600;box-shadow:0 4px 16px rgba(255,20,147,.4);opacity:0;transform:translateY(10px);transition:all .3s;z-index:999;pointer-events:none}
.toast.show{opacity:1;transform:translateY(0)}
@media(max-width:600px){.hero h1{font-size:1.7rem}.card{flex-direction:column}.card-actions{flex-direction:row;align-items:center}.filters{flex-direction:column}.search-row{flex-direction:column}}
"""

files["static/script.js"] = """function showToast(msg){const t=document.getElementById("toast");if(!t)return;t.textContent=msg;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2500)}
function handleSave(btn){const isSaved=btn.classList.contains("saved");const payload={url:btn.dataset.url,name:btn.dataset.name,platform:btn.dataset.platform,members:parseInt(btn.dataset.members)||0,active_users:0,type:btn.dataset.type,description:btn.dataset.desc,title:btn.dataset.name};fetch(isSaved?"/unsave":"/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}).then(r=>r.json()).then(()=>{btn.classList.toggle("saved");btn.textContent=isSaved?"Save":"Saved";showToast(isSaved?"Removed from saved":"Saved!")})}
function saveNotes(url,textarea){fetch("/notes",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,notes:textarea.value})}).then(()=>showToast("Notes saved!"))}
function removeSaved(btn,url){fetch("/unsave",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})}).then(()=>{const card=btn.closest(".card");card.style.transition="opacity 0.3s";card.style.opacity="0";setTimeout(()=>{card.remove();showToast("Removed!")},300)})}
"""

files["templates/index.html"] = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Nichify v1</title><link rel="stylesheet" href="/static/style.css"></head>
<body>
<nav><a href="/" class="logo">Nichify <span>v1</span></a><div><a href="/" class="active">Search</a><a href="/saved">Saved</a></div></nav>
<div class="hero">
  <h1>Find Your <span>Niche Audience</span></h1>
  <p>Discover Reddit communities & forums in any niche. Save, export, and track the best ones.</p>
  <div class="search-box">
    <form action="/search" method="get">
      <div class="search-row">
        <input type="text" name="q" placeholder="e.g. biohacking, quantum biology..." autofocus value="{{ request.args.get('q', '') }}">
        <button type="submit" class="btn-pink">Search</button>
      </div>
      <div class="filters">
        <select name="platform"><option value="all">All Platforms</option><option value="reddit">Reddit Only</option><option value="forum">Forums Only</option></select>
        <select name="min_members"><option value="0">Any Size</option><option value="1000">1K+ Members</option><option value="10000">10K+ Members</option><option value="50000">50K+ Members</option></select>
        <select name="activity"><option value="all">Any Activity</option><option value="active">Active Only</option><option value="dead">Low Activity</option></select>
        <select name="intent"><option value="all">All Intent</option><option value="Buyers">Buyers</option><option value="Learners">Learners</option><option value="Mixed">Mixed</option></select>
      </div>
    </form>
    {% if error %}<p style="color:red;margin-top:12px;font-size:.9rem;">{{ error }}</p>{% endif %}
  </div>
</div>
<div id="toast" class="toast"></div>
<script src="/static/script.js"></script>
</body></html>
"""

files["templates/results.html"] = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Results for "{{ keyword }}" — Nichify v1</title><link rel="stylesheet" href="/static/style.css"></head>
<body>
<nav><a href="/" class="logo">Nichify <span>v1</span></a><div><a href="/">Search</a><a href="/saved">Saved</a></div></nav>
<div class="results-header"><h2>Results for "<strong>{{ keyword }}</strong>"</h2><span class="count">{{ count }} found</span></div>
<div class="results-grid">
{% if results %}{% for r in results %}
<div class="card">
  <div class="card-icon {{ r.platform | lower }}">{% if r.platform == "Reddit" %}🟠{% else %}💬{% endif %}</div>
  <div class="card-body">
    <div class="card-title">{{ r.title or r.name }}</div>
    <div class="card-desc">{{ r.description or "No description available." }}</div>
    <div class="card-meta">
      <span class="badge badge-platform">{{ r.platform }}</span>
      <span class="badge badge-{{ r.type | lower }}">{{ r.type }}</span>
      {% if r.members > 0 %}<span class="card-stats">👥 {{ "{:,}".format(r.members) }} members{% if r.active_users > 0 %} &nbsp;•&nbsp; ⚡ {{ "{:,}".format(r.active_users) }} active{% endif %}</span>{% endif %}
    </div>
  </div>
  <div class="card-actions">
    <button class="btn-save {{ 'saved' if r.saved else '' }}"
      data-url="{{ r.url | e }}"
      data-name="{{ r.name | e }}"
      data-platform="{{ r.platform }}"
      data-members="{{ r.members }}"
      data-type="{{ r.type }}"
      data-desc="{{ (r.description or '') | truncate(100) | e }}"
      onclick="handleSave(this)">{{ "Saved" if r.saved else "Save" }}</button>
    <a href="{{ r.url }}" target="_blank" class="btn-visit">Visit →</a>
  </div>
</div>
{% endfor %}{% else %}
<div class="empty"><div class="icon">🔍</div><h3>No results found</h3><p>Try a different keyword or broaden your filters.</p></div>
{% endif %}
</div>
<div id="toast" class="toast"></div>
<script src="/static/script.js"></script>
</body></html>
"""

files["templates/saved.html"] = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Saved — Nichify v1</title><link rel="stylesheet" href="/static/style.css"></head>
<body>
<nav><a href="/" class="logo">Nichify <span>v1</span></a><div><a href="/">Search</a><a href="/saved" class="active">Saved</a></div></nav>
<div class="page-header"><h1>Saved Communities</h1>{% if saved %}<a href="/export" class="btn-export">Export CSV</a>{% endif %}</div>
<div class="results-grid">
{% if saved %}{% for r in saved %}
<div class="card">
  <div class="card-icon {{ r.platform | lower }}">{% if r.platform == "Reddit" %}🟠{% else %}💬{% endif %}</div>
  <div class="card-body">
    <div class="card-title">{{ r.title or r.name }}</div>
    <div class="card-desc">{{ r.description or "No description available." }}</div>
    <div class="card-meta">
      <span class="badge badge-platform">{{ r.platform }}</span>
      <span class="badge badge-{{ r.type | lower }}">{{ r.type }}</span>
      {% if r.members > 0 %}<span class="card-stats">👥 {{ "{:,}".format(r.members) }} members</span>{% endif %}
    </div>
    <textarea class="notes-input" rows="2" placeholder="Add notes..." onblur="saveNotes('{{ r.url }}', this)">{{ r.notes or "" }}</textarea>
    <div class="saved-date">Saved on {{ r.saved_at or "—" }}</div>
  </div>
  <div class="card-actions">
    <button class="btn-remove" onclick="removeSaved(this,'{{ r.url }}')">Remove</button>
    <a href="{{ r.url }}" target="_blank" class="btn-visit">Visit →</a>
  </div>
</div>
{% endfor %}{% else %}
<div class="empty"><div class="icon">📌</div><h3>No saved communities yet</h3><p>Search for a niche and save communities you want to track.</p><br><a href="/" class="btn-pink" style="display:inline-block;padding:10px 24px;border-radius:10px;text-decoration:none;">Start Searching</a></div>
{% endif %}
</div>
<div id="toast" class="toast"></div>
<script src="/static/script.js"></script>
</body></html>
"""

for path, content in files.items():
    full_path = f"nichify/{path}"
    with open(full_path, "w") as f:
        f.write(content)
    print(f"Created: {full_path}")

print("\nDone! Run these next:")
print("  cd nichify")
print("  pip install flask requests")
print("  python app.py")
print("\nThen open in browser: http://127.0.0.1:5000")
