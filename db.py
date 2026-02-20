# db.py
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any


@contextmanager
def get_conn(db_path: str):
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str) -> None:
    with get_conn(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'queued',   -- queued | crawling | crawled | error
            depth INTEGER NOT NULL DEFAULT 0,
            discovered_from TEXT,
            http_status INTEGER,
            error TEXT,
            first_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_crawled DATETIME
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status);")


def add_url(db_path: str, url: str, depth: int = 0, discovered_from: Optional[str] = None) -> bool:
    """
    Retourne True si l'URL est nouvelle, False si déjà en base.
    """
    with get_conn(db_path) as conn:
        try:
            conn.execute(
                "INSERT INTO urls(url, status, depth, discovered_from) VALUES(?, 'queued', ?, ?)",
                (url, depth, discovered_from),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def pop_next_queued(db_path: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la prochaine URL en 'queued' et la passe en 'crawling' atomiquement.
    """
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT id, url, depth FROM urls WHERE status='queued' ORDER BY id ASC LIMIT 1"
        ).fetchone()

        if not row:
            return None

        conn.execute("UPDATE urls SET status='crawling' WHERE id=?", (row["id"],))
        return {"id": row["id"], "url": row["url"], "depth": row["depth"]}


def mark_crawled(db_path: str, url_id: int, http_status: int) -> None:
    with get_conn(db_path) as conn:
        conn.execute("""
            UPDATE urls
            SET status='crawled', http_status=?, error=NULL, last_crawled=CURRENT_TIMESTAMP
            WHERE id=?
        """, (http_status, url_id))


def mark_error(db_path: str, url_id: int, error: str) -> None:
    with get_conn(db_path) as conn:
        conn.execute("""
            UPDATE urls
            SET status='error', error=?, last_crawled=CURRENT_TIMESTAMP
            WHERE id=?
        """, (error[:2000], url_id))


def list_urls(db_path: str, status: Optional[str], limit: int, offset: int) -> List[Dict[str, Any]]:
    q = "SELECT id, url, status, depth, discovered_from, http_status, error, first_seen, last_crawled FROM urls"
    params = []
    if status:
        q += " WHERE status=?"
        params.append(status)
    q += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_conn(db_path) as conn:
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]


def stats(db_path: str) -> Dict[str, int]:
    with get_conn(db_path) as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM urls").fetchone()["c"]
        queued = conn.execute("SELECT COUNT(*) AS c FROM urls WHERE status='queued'").fetchone()["c"]
        crawling = conn.execute("SELECT COUNT(*) AS c FROM urls WHERE status='crawling'").fetchone()["c"]
        crawled = conn.execute("SELECT COUNT(*) AS c FROM urls WHERE status='crawled'").fetchone()["c"]
        error = conn.execute("SELECT COUNT(*) AS c FROM urls WHERE status='error'").fetchone()["c"]
    return {"total": total, "queued": queued, "crawling": crawling, "crawled": crawled, "error": error}