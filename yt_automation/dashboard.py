"""
dashboard.py — Local review dashboard for the Shorts pipeline.

Workflow: pro_shorts_creator.create_draft() writes pending records to
output/review_queue.json (script, stock-footage thumbnails, voice preview).
This dashboard lets you look at each draft, edit the script, approve it
(renders + uploads via pro_shorts_creator.render_and_publish, respecting
config.UPLOAD_PRIVACY) or reject it. Every draft stays in the queue file
permanently as a record, whatever you decide.

Run: python dashboard.py, then open http://localhost:5000
"""

import os
import threading
import time

from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string

import config
import pro_shorts_creator as psc
import viral_analytics
import copyright_compliance
from logger import log

app = Flask(__name__)

LIST_TEMPLATE = """
<!doctype html>
<title>FramedFacts Review Dashboard</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.4rem; }
  .record { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .status { font-weight: bold; text-transform: uppercase; font-size: 0.8rem; padding: 2px 8px; border-radius: 4px; }
  .status-pending { background: #fff3cd; }
  .status-rendering { background: #cfe2ff; }
  .status-uploaded { background: #d1e7dd; }
  .status-rejected { background: #f8d7da; }
  .status-failed { background: #f8d7da; }
  .flag-ok { background: #d1e7dd; }
  .flag-warn { background: #f8d7da; }
  .thumbs img { height: 80px; margin-right: 6px; border-radius: 4px; }
  a.btn, button { display: inline-block; margin-top: 8px; margin-right: 6px; padding: 6px 12px;
                  border-radius: 6px; border: 1px solid #888; background: #f5f5f5; cursor: pointer;
                  text-decoration: none; color: #000; font-size: 0.9rem; }
  form { display: inline; }
</style>
<h1>FramedFacts Review Dashboard</h1>
<form method="post" action="{{ url_for('refresh_stats') }}"><button type="submit">Refresh Stats</button></form>
<a class="btn" href="{{ url_for('monetization') }}">Monetization / YPP Status</a>
{% for r in records %}
  <div class="record">
    <span class="status status-{{ r.status }}">{{ r.status }}</span>
    <span class="status {{ 'flag-ok' if r.advertiser_friendly else 'flag-warn' }}">
      {{ 'Advertiser-friendly' if r.advertiser_friendly else 'Guideline issues' }}
    </span>
    <strong>{{ r.script.title }}</strong>
    <div class="thumbs">
      {% for t in r.clip_thumbs %}{% if t %}<img src="{{ url_for('media', path=t) }}">{% endif %}{% endfor %}
    </div>
    <p>{{ r.script.hook }}</p>
    {% if r.youtube_url %}<p><a href="{{ r.youtube_url }}" target="_blank">{{ r.youtube_url }}</a>
       {% if r.views is not none %} — {{ r.views }} views, {{ r.likes }} likes{% endif %}</p>{% endif %}
    <a class="btn" href="{{ url_for('detail', record_id=r.id) }}">Open</a>
    {% if r.status == 'pending' %}
      <form method="post" action="{{ url_for('approve', record_id=r.id) }}"><button type="submit">Approve</button></form>
      <form method="post" action="{{ url_for('reject', record_id=r.id) }}"><button type="submit">Reject</button></form>
    {% endif %}
  </div>
{% endfor %}
"""

DETAIL_TEMPLATE = """
<!doctype html>
<title>{{ r.script.title }}</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
  textarea, input[type=text] { width: 100%; font-family: inherit; font-size: 1rem; margin-bottom: 8px; }
  .thumbs img { height: 120px; margin-right: 6px; border-radius: 4px; }
  button, a.btn { padding: 8px 14px; border-radius: 6px; border: 1px solid #888; background: #f5f5f5;
                  cursor: pointer; margin-right: 6px; text-decoration: none; color: #000; }
</style>
<p><a href="{{ url_for('index') }}">&larr; back</a></p>
<h1>{{ r.script.title }}</h1>
<p><span class="status">{{ r.status }}</span></p>
<div class="thumbs">
  {% for t in r.clip_thumbs %}{% if t %}<img src="{{ url_for('media', path=t) }}">{% endif %}{% endfor %}
</div>
<audio controls src="{{ url_for('media', path=r.voice_path) }}"></audio>

<form method="post" action="{{ url_for('edit', record_id=r.id) }}">
  <label>Hook</label>
  <textarea name="hook" rows="2">{{ r.script.hook }}</textarea>
  <label>Body</label>
  <textarea name="body" rows="4">{{ r.script.body }}</textarea>
  <label>CTA</label>
  <textarea name="cta" rows="2">{{ r.script.cta }}</textarea>
  <label>Title</label>
  <input type="text" name="title" value="{{ r.script.title }}">
  <button type="submit">Save Edits (regenerates voice preview)</button>
</form>

{% if r.status == 'pending' %}
<form method="post" action="{{ url_for('approve', record_id=r.id) }}">
  <button type="submit">Approve &amp; Publish ({{ upload_privacy }})</button>
</form>
<form method="post" action="{{ url_for('reject', record_id=r.id) }}">
  <label>Reason (optional)</label>
  <input type="text" name="note">
  <button type="submit">Reject</button>
</form>
{% endif %}
{% if r.youtube_url %}<p><a href="{{ r.youtube_url }}" target="_blank">{{ r.youtube_url }}</a></p>{% endif %}
"""


def _web_paths(r: dict) -> dict:
    """Return a copy of the record with filesystem paths using forward
    slashes, safe to embed in URLs regardless of OS."""
    r = dict(r)
    r["clip_thumbs"] = [(t or "").replace(os.sep, "/") for t in r.get("clip_thumbs", [])]
    r["voice_path"] = (r.get("voice_path") or "").replace(os.sep, "/")
    return r


@app.route("/")
def index():
    records = sorted(psc._load_queue(), key=lambda r: r["created_at"], reverse=True)
    records = [_web_paths(r) for r in records]
    for r in records:
        failed = copyright_compliance.check_guidelines(r.get("script", {}))
        r["advertiser_friendly"] = not failed
    return render_template_string(LIST_TEMPLATE, records=records)


@app.route("/record/<record_id>")
def detail(record_id):
    r = _web_paths(psc._get_record(record_id))
    return render_template_string(DETAIL_TEMPLATE, r=r, upload_privacy=config.UPLOAD_PRIVACY)


@app.route("/record/<record_id>/edit", methods=["POST"])
def edit(record_id):
    r = psc._get_record(record_id)
    script = r["script"]
    changed = any(request.form.get(k, "") != script.get(k, "") for k in ("hook", "body", "cta"))
    script["hook"] = request.form.get("hook", script.get("hook", ""))
    script["body"] = request.form.get("body", script.get("body", ""))
    script["cta"] = request.form.get("cta", script.get("cta", ""))
    script["title"] = request.form.get("title", script.get("title", ""))

    voice_path = r["voice_path"]
    if changed:
        voice_path = psc.generate_voiceover(script)

    psc._update_record(record_id, script=script, voice_path=voice_path)
    return redirect(url_for("detail", record_id=record_id))


@app.route("/record/<record_id>/approve", methods=["POST"])
def approve(record_id):
    psc._update_record(record_id, status="rendering")
    threading.Thread(target=psc.render_and_publish, args=(record_id,), daemon=True).start()
    return redirect(url_for("index"))


@app.route("/record/<record_id>/reject", methods=["POST"])
def reject(record_id):
    note = request.form.get("note", "")
    psc._update_record(record_id, status="rejected", decision_notes=note)
    return redirect(url_for("index"))


@app.route("/refresh-stats", methods=["POST"])
def refresh_stats():
    videos = viral_analytics.fetch_recent_video_stats()
    by_id = {v["video_id"]: v for v in videos}
    records = psc._load_queue()
    for r in records:
        url = r.get("youtube_url") or ""
        vid = url.rsplit("=", 1)[-1] if "=" in url else ""
        if vid in by_id:
            r["views"] = by_id[vid]["views"]
            r["likes"] = by_id[vid]["likes"]
            r["stats_synced_at"] = time.time()
    psc._save_queue(records)
    return redirect(url_for("index"))


MONETIZATION_TEMPLATE = """
<!doctype html>
<title>Monetization / YPP Status</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }
  .metric { border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .eligible { background: #d1e7dd; }
  .not-eligible { background: #fff3cd; }
  .error { background: #f8d7da; }
</style>
<p><a href="{{ url_for('index') }}">&larr; back</a></p>
<h1>YouTube Partner Program Status</h1>
{% if error %}
  <div class="metric error"><strong>Could not fetch live data:</strong> {{ error }}</div>
{% else %}
  <div class="metric {{ 'eligible' if ypp.eligible else 'not-eligible' }}">
    <strong>{{ 'ELIGIBLE' if ypp.eligible else 'NOT YET ELIGIBLE' }}</strong>
    {% if ypp.qualifying_path %} — via {{ ypp.qualifying_path }}{% endif %}
  </div>
  <div class="metric">
    Subscribers: {{ ypp.subscribers }} / 1,000
    {% if ypp.subscribers_needed %} ({{ ypp.subscribers_needed }} more needed){% endif %}
  </div>
  <div class="metric">
    Watch hours (trailing 12mo): {{ ypp.watch_hours_12mo }} / 4,000
    {% if ypp.watch_hours_needed %} ({{ ypp.watch_hours_needed }} more needed){% endif %}
  </div>
  <div class="metric">
    Shorts views (trailing 90d): {{ ypp.shorts_views_90d }} / 10,000,000
    {% if ypp.shorts_views_needed %} ({{ ypp.shorts_views_needed }} more needed){% endif %}
  </div>
{% endif %}
"""


@app.route("/monetization")
def monetization():
    try:
        import ypp_tracker
        ypp = ypp_tracker.check_eligibility()
        return render_template_string(MONETIZATION_TEMPLATE, ypp=ypp, error=None)
    except Exception as e:
        return render_template_string(MONETIZATION_TEMPLATE, ypp=None, error=str(e))


@app.route("/media/<path:path>")
def media(path):
    directory, filename = os.path.split(os.path.abspath(path))
    return send_from_directory(directory, filename)


if __name__ == "__main__":
    log("Dashboard running at http://localhost:5000")
    app.run(debug=False, port=5000)
