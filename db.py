# db.py
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse


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
    Return True if the URL is new, False if it already exists in the database.
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
    Fetch the next URL in 'queued' and atomically switch it to 'crawling'.
    (Important for multi-threaded workers)
    """
    with get_conn(db_path) as conn:
        # Acquire a write lock while selecting/updating to avoid thread races.
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            "SELECT id, url, depth FROM urls WHERE status='queued' ORDER BY id ASC LIMIT 1"
        ).fetchone()

        if not row:
            return None

        conn.execute(
            "UPDATE urls SET status='crawling' WHERE id=? AND status='queued'",
            (row["id"],),
        )

        # Defensive check in case another edge case occurs.
        if conn.total_changes == 0:
            return None

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


def depth_histogram(db_path: str, max_depth: int = 8) -> List[Dict[str, Any]]:
    if max_depth < 0:
        max_depth = 0

    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT depth, COUNT(*) AS c FROM urls GROUP BY depth ORDER BY depth ASC"
        ).fetchall()

    buckets = {d: 0 for d in range(max_depth + 1)}
    overflow = 0
    for row in rows:
        depth = int(row["depth"])
        count = int(row["c"])
        if depth <= max_depth:
            buckets[depth] += count
        else:
            overflow += count

    result = [{"label": str(depth), "count": buckets[depth]} for depth in range(max_depth + 1)]
    if overflow > 0:
        result.append({"label": f">{max_depth}", "count": overflow})

    return result


def http_status_buckets(db_path: str) -> List[Dict[str, Any]]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
              CASE
                WHEN http_status BETWEEN 200 AND 299 THEN '2xx'
                WHEN http_status BETWEEN 300 AND 399 THEN '3xx'
                WHEN http_status BETWEEN 400 AND 499 THEN '4xx'
                WHEN http_status BETWEEN 500 AND 599 THEN '5xx'
                ELSE 'other'
              END AS bucket,
              COUNT(*) AS c
            FROM urls
            WHERE http_status IS NOT NULL
            GROUP BY bucket
            """
        ).fetchall()

    counts = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "other": 0}
    for row in rows:
        counts[str(row["bucket"])] = int(row["c"])

    return [{"label": label, "count": counts[label]} for label in ("2xx", "3xx", "4xx", "5xx", "other")]


def top_domains(db_path: str, limit: int = 8) -> List[Dict[str, Any]]:
    if limit < 1:
        return []

    with get_conn(db_path) as conn:
        rows = conn.execute("SELECT url FROM urls").fetchall()

    counts: Dict[str, int] = {}
    for row in rows:
        host = urlparse(str(row["url"])).netloc.lower().strip()
        if not host:
            continue
        counts[host] = counts.get(host, 0) + 1

    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [{"label": domain, "count": count} for domain, count in ordered]


def activity_last_hours(db_path: str, hours: int = 24) -> List[Dict[str, Any]]:
    if hours < 1:
        return []

    now_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start_hour = now_hour - timedelta(hours=hours - 1)
    start_value = start_hour.strftime("%Y-%m-%d %H:%M:%S")

    with get_conn(db_path) as conn:
        discovered_rows = conn.execute(
            """
            SELECT strftime('%Y-%m-%d %H:00:00', first_seen) AS bucket, COUNT(*) AS c
            FROM urls
            WHERE first_seen >= ?
            GROUP BY bucket
            """,
            (start_value,),
        ).fetchall()

        crawled_rows = conn.execute(
            """
            SELECT strftime('%Y-%m-%d %H:00:00', last_crawled) AS bucket, COUNT(*) AS c
            FROM urls
            WHERE last_crawled IS NOT NULL AND last_crawled >= ?
            GROUP BY bucket
            """,
            (start_value,),
        ).fetchall()

    discovered_map = {str(row["bucket"]): int(row["c"]) for row in discovered_rows}
    crawled_map = {str(row["bucket"]): int(row["c"]) for row in crawled_rows}

    series: List[Dict[str, Any]] = []
    for i in range(hours):
        bucket_dt = start_hour + timedelta(hours=i)
        bucket_key = bucket_dt.strftime("%Y-%m-%d %H:00:00")
        series.append(
            {
                "label": bucket_dt.strftime("%H:%M"),
                "discovered": discovered_map.get(bucket_key, 0),
                "crawled": crawled_map.get(bucket_key, 0),
            }
        )

    return series
