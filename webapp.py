# webapp.py
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

import db


def create_app(db_path: str) -> FastAPI:
    app = FastAPI(title="URL Collector")

    @app.get("/", response_class=HTMLResponse)
    def home():
        s = db.stats(db_path)
        html = f"""
        <html>
          <head><meta charset="utf-8"><title>URL Collector</title></head>
          <body style="font-family: Arial, sans-serif; margin: 24px;">
            <h1>URL Collector</h1>
            <p>
              Total: <b>{s['total']}</b> —
              Queued: <b>{s['queued']}</b> —
              Crawling: <b>{s['crawling']}</b> —
              Crawled: <b>{s['crawled']}</b> —
              Error: <b>{s['error']}</b>
            </p>
            <p>
              <a href="/urls">Voir toutes les URLs</a> |
              <a href="/urls?status=queued">Queued</a> |
              <a href="/urls?status=crawled">Crawled</a> |
              <a href="/urls?status=error">Error</a>
            </p>
            <hr/>
            <p>API JSON: <a href="/api/urls">/api/urls</a></p>
          </body>
        </html>
        """
        return html

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

            items.append(f"""
              <li style="margin: 6px 0;">
                <a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>
                <div style="color:#555; font-size: 12px;">{meta}</div>
              </li>
            """)

        html = f"""
        <html>
          <head><meta charset="utf-8"><title>URLs</title></head>
          <body style="font-family: Arial, sans-serif; margin: 24px;">
            <h1>URLs</h1>
            <p><a href="/">Retour</a></p>
            <p>Filtre status: <b>{status or "all"}</b> — limit={limit} offset={offset}</p>
            <ul style="padding-left: 18px;">
              {''.join(items) if items else '<li>Aucune URL.</li>'}
            </ul>
          </body>
        </html>
        """
        return html

    @app.get("/api/urls")
    def api_urls(
        status: str | None = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
        offset: int = Query(default=0, ge=0),
    ):
        rows = db.list_urls(db_path, status=status, limit=limit, offset=offset)
        return JSONResponse({"items": rows, "stats": db.stats(db_path)})

    return app