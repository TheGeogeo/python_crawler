# webapp.py
from html import escape
from typing import Any, Dict, List

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

import db


BASE_HEAD = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: dark;
    --bg-0: #060a14;
    --bg-1: #0f1729;
    --bg-2: #16213a;
    --panel: rgba(15, 23, 41, 0.78);
    --border: #293a5f;
    --text: #e9efff;
    --muted: #a5b1ce;
    --link: #9dd7ff;
    --accent: #70b7ff;
    --success: #34d399;
    --warn: #fbbf24;
    --danger: #f87171;
    --surface-1: #131f38;
    --surface-2: #0f1729;
  }

  * { box-sizing: border-box; }

  html, body {
    margin: 0;
    padding: 0;
  }

  body {
    min-height: 100vh;
    font-family: "Space Grotesk", "Segoe UI", sans-serif;
    color: var(--text);
    background:
      radial-gradient(1200px 600px at 0% -10%, #223763 0%, transparent 55%),
      radial-gradient(1000px 500px at 100% 0%, #1b2f56 0%, transparent 50%),
      linear-gradient(160deg, var(--bg-0), var(--bg-1) 45%, var(--bg-2));
    padding: 24px 14px;
  }

  .shell {
    max-width: 1120px;
    margin: 0 auto;
  }

  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(4px);
  }

  .topline {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }

  h1 {
    margin: 0;
    font-size: clamp(1.5rem, 2vw + 1rem, 2.1rem);
    letter-spacing: 0.3px;
  }

  .muted {
    color: var(--muted);
    font-size: 0.95rem;
  }

  .stats-grid {
    margin-top: 16px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 10px;
  }

  .stat {
    background: linear-gradient(180deg, var(--surface-1), var(--surface-2));
    border: 1px solid #31466f;
    border-radius: 12px;
    padding: 10px 12px;
  }

  .stat-label {
    color: var(--muted);
    font-size: 0.79rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }

  .stat-value {
    margin-top: 4px;
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.1;
  }

  .stat-value.queued { color: var(--warn); }
  .stat-value.crawling { color: var(--accent); }
  .stat-value.crawled { color: var(--success); }
  .stat-value.error { color: var(--danger); }

  .actions {
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 999px;
    border: 1px solid #3c5482;
    background: #14203a;
    color: var(--text);
    padding: 8px 12px;
    font-size: 0.88rem;
    text-decoration: none;
    transition: border-color 0.14s ease, background-color 0.14s ease, transform 0.14s ease;
  }

  .chip:hover {
    border-color: #5f7fb9;
    background: #1b2d50;
    transform: translateY(-1px);
  }

  .divider {
    border: 0;
    border-top: 1px solid var(--border);
    margin: 18px 0 14px;
  }

  .meta-line {
    color: var(--muted);
    margin: 0;
  }

  .meta-line a {
    color: var(--link);
    text-underline-offset: 2px;
  }

  .list {
    list-style: none;
    padding: 0;
    margin: 14px 0 0;
    display: grid;
    gap: 10px;
  }

  .list-item {
    border: 1px solid #2d4168;
    background: linear-gradient(180deg, #131f36, #0f1729);
    border-radius: 12px;
    padding: 12px;
  }

  .list-item a {
    color: var(--link);
    text-decoration: none;
    word-break: break-word;
    font-weight: 500;
  }

  .list-item a:hover {
    text-decoration: underline;
    text-underline-offset: 2px;
  }

  .item-meta {
    margin-top: 7px;
    color: var(--muted);
    font-size: 0.8rem;
    font-family: "IBM Plex Mono", Consolas, "Courier New", monospace;
    word-break: break-word;
  }

  .no-items {
    color: var(--muted);
  }

  .analytics-grid {
    margin-top: 16px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .panel {
    border: 1px solid #2e4269;
    border-radius: 14px;
    background: linear-gradient(180deg, #13203a, #0f1729);
    padding: 14px;
    min-height: 220px;
  }

  .panel.wide {
    grid-column: span 2;
  }

  .panel-title {
    margin: 0 0 12px;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.2px;
  }

  .empty-state {
    color: var(--muted);
    margin: 0;
    font-size: 0.9rem;
  }

  .hbar-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 10px;
  }

  .hbar-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: var(--muted);
    font-size: 0.85rem;
    margin-bottom: 5px;
  }

  .hbar-head b {
    color: var(--text);
    font-family: "IBM Plex Mono", Consolas, "Courier New", monospace;
    font-weight: 500;
  }

  .hbar-track {
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: #1a2743;
    border: 1px solid #2b3f65;
    overflow: hidden;
  }

  .hbar-fill {
    display: block;
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #4da6ff, #77b8ff);
  }

  .hbar-fill.warn { background: linear-gradient(90deg, #d79b21, #fbbf24); }
  .hbar-fill.success { background: linear-gradient(90deg, #1e9f75, #34d399); }
  .hbar-fill.danger { background: linear-gradient(90deg, #c35a5a, #f87171); }

  .donut-wrap {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .donut {
    width: 170px;
    height: 170px;
    border-radius: 50%;
    border: 1px solid #33466d;
    display: grid;
    place-items: center;
    position: relative;
    flex: 0 0 auto;
  }

  .donut::before {
    content: "";
    width: 95px;
    height: 95px;
    border-radius: 50%;
    background: #0f1729;
    border: 1px solid #2f4269;
    display: block;
  }

  .donut-center {
    position: absolute;
    text-align: center;
  }

  .donut-center b {
    display: block;
    font-size: 1.3rem;
    line-height: 1.1;
  }

  .donut-center span {
    font-size: 0.78rem;
    color: var(--muted);
  }

  .legend {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 8px;
    min-width: 220px;
  }

  .legend li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    font-size: 0.86rem;
    color: var(--muted);
  }

  .legend .left {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
  }

  .dot.queued { background: #fbbf24; }
  .dot.crawling { background: #70b7ff; }
  .dot.crawled { background: #34d399; }
  .dot.error { background: #f87171; }

  .legend b {
    color: var(--text);
    font-family: "IBM Plex Mono", Consolas, "Courier New", monospace;
    font-weight: 500;
  }

  .timeline-meta {
    margin-top: -6px;
    margin-bottom: 10px;
    color: var(--muted);
    font-size: 0.84rem;
  }

  .timeline-legend {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 10px;
    color: var(--muted);
    font-size: 0.82rem;
  }

  .timeline {
    list-style: none;
    margin: 0;
    padding: 0 0 2px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(20px, 1fr));
    gap: 4px;
    align-items: end;
    min-height: 180px;
  }

  .timeline-col {
    min-width: 0;
  }

  .timeline-bars {
    height: 124px;
    border: 1px solid #2b3f65;
    border-radius: 8px;
    background: #14213b;
    display: flex;
    align-items: end;
    justify-content: center;
    gap: 2px;
    padding: 4px 3px;
  }

  .timeline-bar {
    width: 6px;
    border-radius: 3px 3px 0 0;
    min-height: 2px;
    display: inline-block;
  }

  .timeline-bar.discovered { background: #7ebeff; }
  .timeline-bar.crawled { background: #34d399; }

  .timeline-label {
    margin-top: 4px;
    font-size: 0.66rem;
    color: var(--muted);
    text-align: center;
    white-space: nowrap;
  }

  @media (max-width: 940px) {
    .analytics-grid {
      grid-template-columns: minmax(0, 1fr);
    }

    .panel.wide {
      grid-column: span 1;
    }
  }

  @media (max-width: 640px) {
    .card { padding: 16px; }
    .chip { padding: 7px 10px; }
    .donut { width: 150px; height: 150px; }
    .donut::before { width: 84px; height: 84px; }
  }
</style>
"""


STATUS_COLORS = {
    "queued": "#fbbf24",
    "crawling": "#70b7ff",
    "crawled": "#34d399",
    "error": "#f87171",
}


def render_page(title: str, body: str) -> str:
    return f"""
    <html>
      <head>
        <title>{title}</title>
        {BASE_HEAD}
      </head>
      <body>
        <main class="shell">
          <section class="card">
            {body}
          </section>
        </main>
      </body>
    </html>
    """


def render_hbar_chart(title: str, items: List[Dict[str, Any]], color_class: str = "") -> str:
    if not items:
        return f"""
        <h2 class="panel-title">{escape(title)}</h2>
        <p class="empty-state">No data available yet.</p>
        """

    max_count = max(int(item.get("count", 0)) for item in items) if items else 0
    if max_count <= 0:
        max_count = 1

    rows = []
    for item in items:
        label = escape(str(item.get("label", "")))
        count = int(item.get("count", 0))
        width = (count / max_count) * 100.0
        rows.append(
            f"""
            <li>
              <div class="hbar-head">
                <span>{label}</span>
                <b>{count}</b>
              </div>
              <div class="hbar-track">
                <span class="hbar-fill {color_class}" style="width:{width:.2f}%"></span>
              </div>
            </li>
            """
        )

    return f"""
    <h2 class="panel-title">{escape(title)}</h2>
    <ul class="hbar-list">
      {"".join(rows)}
    </ul>
    """


def render_status_donut(summary: Dict[str, int]) -> str:
    total = int(summary.get("total", 0))
    segments = [
        ("queued", int(summary.get("queued", 0))),
        ("crawling", int(summary.get("crawling", 0))),
        ("crawled", int(summary.get("crawled", 0))),
        ("error", int(summary.get("error", 0))),
    ]

    if total <= 0:
        gradient = "#253753 0% 100%"
    else:
        start = 0.0
        pieces = []
        for key, value in segments:
            share = (value / total) * 100.0
            end = start + share
            pieces.append(f"{STATUS_COLORS[key]} {start:.2f}% {end:.2f}%")
            start = end
        gradient = ", ".join(pieces) if pieces else "#253753 0% 100%"

    legend_rows = []
    for key, value in segments:
        pct = (value / total * 100.0) if total > 0 else 0.0
        legend_rows.append(
            f"""
            <li>
              <span class="left">
                <span class="dot {key}"></span>
                <span>{escape(key.title())}</span>
              </span>
              <b>{value} ({pct:.1f}%)</b>
            </li>
            """
        )

    return f"""
    <h2 class="panel-title">Status Distribution</h2>
    <div class="donut-wrap">
      <div class="donut" style="background: conic-gradient({gradient});">
        <div class="donut-center">
          <b>{total}</b>
          <span>total</span>
        </div>
      </div>
      <ul class="legend">
        {"".join(legend_rows)}
      </ul>
    </div>
    """


def render_activity_timeline(series: List[Dict[str, Any]], hours: int) -> str:
    if not series:
        return """
        <h2 class="panel-title">Discovery vs Crawl Activity</h2>
        <p class="empty-state">No activity data available yet.</p>
        """

    max_value = max(
        max(int(item.get("discovered", 0)), int(item.get("crawled", 0)))
        for item in series
    )
    if max_value <= 0:
        max_value = 1

    columns = []
    label_step = 3 if len(series) > 16 else 2
    for idx, item in enumerate(series):
        label = escape(str(item.get("label", "")))
        discovered = int(item.get("discovered", 0))
        crawled = int(item.get("crawled", 0))
        discovered_h = (discovered / max_value) * 100.0
        crawled_h = (crawled / max_value) * 100.0
        show_label = idx % label_step == 0 or idx == len(series) - 1
        visible_label = label if show_label else "&nbsp;"

        columns.append(
            f"""
            <li class="timeline-col">
              <div class="timeline-bars">
                <span class="timeline-bar discovered" style="height:{discovered_h:.2f}%" title="discovered: {discovered}"></span>
                <span class="timeline-bar crawled" style="height:{crawled_h:.2f}%" title="crawled: {crawled}"></span>
              </div>
              <div class="timeline-label">{visible_label}</div>
            </li>
            """
        )

    return f"""
    <h2 class="panel-title">Discovery vs Crawl Activity</h2>
    <p class="timeline-meta">Last {hours} hours, normalized on max={max_value}</p>
    <div class="timeline-legend">
      <span><span class="dot" style="background:#7ebeff;"></span> discovered</span>
      <span><span class="dot" style="background:#34d399;"></span> crawled</span>
    </div>
    <ul class="timeline">
      {"".join(columns)}
    </ul>
    """


def create_app(db_path: str) -> FastAPI:
    app = FastAPI(title="URL Collector")

    @app.get("/", response_class=HTMLResponse)
    def home():
        s = db.stats(db_path)
        body = f"""
        <div class="topline">
          <h1>URL Collector</h1>
          <span class="muted">Live crawl dashboard</span>
        </div>

        <div class="stats-grid">
          <article class="stat">
            <div class="stat-label">Total</div>
            <div class="stat-value">{s['total']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Queued</div>
            <div class="stat-value queued">{s['queued']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Crawling</div>
            <div class="stat-value crawling">{s['crawling']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Crawled</div>
            <div class="stat-value crawled">{s['crawled']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Error</div>
            <div class="stat-value error">{s['error']}</div>
          </article>
        </div>

        <nav class="actions">
          <a class="chip" href="/stats">Statistics</a>
          <a class="chip" href="/urls">View all URLs</a>
          <a class="chip" href="/urls?status=queued">Queued</a>
          <a class="chip" href="/urls?status=crawled">Crawled</a>
          <a class="chip" href="/urls?status=error">Error</a>
        </nav>

        <hr class="divider"/>
        <p class="meta-line">JSON API: <a href="/api/urls">/api/urls</a> | <a href="/api/stats">/api/stats</a></p>
        """
        return render_page("URL Collector", body)

    @app.get("/urls", response_class=HTMLResponse)
    def urls(
        status: str | None = Query(default=None, description="queued|crawling|crawled|error"),
        limit: int = Query(default=200, ge=1, le=2000),
        offset: int = Query(default=0, ge=0),
    ):
        rows = db.list_urls(db_path, status=status, limit=limit, offset=offset)

        items = []
        for r in rows:
            url = r["url"]
            st = r["status"]
            depth = r["depth"]
            http_status = r.get("http_status")
            err = (r.get("error") or "")
            meta = f"[{st}] depth={depth}"
            if http_status is not None:
                meta += f" http={http_status}"
            if err:
                meta += f" error={err}"

            safe_href = escape(url, quote=True)
            safe_url_text = escape(url)
            safe_meta = escape(meta)
            items.append(
                f"""
              <li class="list-item">
                <a href="{safe_href}" target="_blank" rel="noopener noreferrer">{safe_url_text}</a>
                <div class="item-meta">{safe_meta}</div>
              </li>
            """
            )

        status_text = escape(status or "all")
        items_html = "".join(items) if items else '<li class="list-item no-items">No URLs.</li>'

        body = f"""
        <div class="topline">
          <h1>URLs</h1>
          <nav class="actions">
            <a class="chip" href="/stats">Statistics</a>
            <a class="chip" href="/">Back</a>
          </nav>
        </div>

        <p class="meta-line">Status filter: <b>{status_text}</b> | limit={limit} | offset={offset}</p>
        <ul class="list">
          {items_html}
        </ul>
        """
        return render_page("URLs", body)

    @app.get("/stats", response_class=HTMLResponse)
    def stats_page(
        hours: int = Query(default=24, ge=6, le=72, description="Window size for timeline charts"),
    ):
        summary = db.stats(db_path)
        depth_data = db.depth_histogram(db_path, max_depth=8)
        http_data = db.http_status_buckets(db_path)
        domain_data = db.top_domains(db_path, limit=8)
        activity_data = db.activity_last_hours(db_path, hours=hours)

        processed = summary["crawled"] + summary["error"]
        success_rate = (summary["crawled"] / processed * 100.0) if processed > 0 else 0.0

        body = f"""
        <div class="topline">
          <h1>Crawler Statistics</h1>
          <nav class="actions">
            <a class="chip" href="/urls">URLs</a>
            <a class="chip" href="/">Back</a>
          </nav>
        </div>

        <p class="meta-line">Data window: last <b>{hours}h</b> | Success rate: <b>{success_rate:.1f}%</b></p>

        <div class="stats-grid">
          <article class="stat">
            <div class="stat-label">Total URLs</div>
            <div class="stat-value">{summary['total']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Queued</div>
            <div class="stat-value queued">{summary['queued']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Crawled</div>
            <div class="stat-value crawled">{summary['crawled']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Errors</div>
            <div class="stat-value error">{summary['error']}</div>
          </article>
          <article class="stat">
            <div class="stat-label">Success Rate</div>
            <div class="stat-value">{success_rate:.1f}%</div>
          </article>
        </div>

        <div class="analytics-grid">
          <section class="panel">
            {render_status_donut(summary)}
          </section>
          <section class="panel">
            {render_hbar_chart("HTTP Status Classes", http_data)}
          </section>
          <section class="panel">
            {render_hbar_chart("Depth Distribution", depth_data, "warn")}
          </section>
          <section class="panel">
            {render_hbar_chart("Top Domains", domain_data, "success")}
          </section>
          <section class="panel wide">
            {render_activity_timeline(activity_data, hours)}
          </section>
        </div>
        """
        return render_page("Crawler Statistics", body)

    @app.get("/api/urls")
    def api_urls(
        status: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
        offset: int = Query(default=0, ge=0),
    ):
        rows = db.list_urls(db_path, status=status, limit=limit, offset=offset)
        return JSONResponse({"items": rows, "stats": db.stats(db_path)})

    @app.get("/api/stats")
    def api_stats(
        hours: int = Query(default=24, ge=6, le=72),
    ):
        summary = db.stats(db_path)
        payload = {
            "stats": summary,
            "depth_distribution": db.depth_histogram(db_path, max_depth=8),
            "http_status_buckets": db.http_status_buckets(db_path),
            "top_domains": db.top_domains(db_path, limit=8),
            "activity_last_hours": db.activity_last_hours(db_path, hours=hours),
        }
        return JSONResponse(payload)

    return app
