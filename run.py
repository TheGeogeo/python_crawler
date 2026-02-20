# run.py
import argparse
import threading
import time
import socket
import webbrowser

import uvicorn

from crawler import Crawler, CrawlerConfig
from webapp import create_app


def wait_port_open(host: str, port: int, timeout_sec: float = 15.0) -> bool:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, help="Seed URL")
    parser.add_argument("--db", default="crawler.sqlite", help="SQLite file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    # Optional: if omitted, crawl is unlimited.
    parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages (if omitted: unlimited)")

    # Default: crawl all domains; use this flag to limit to the seed domain.
    parser.add_argument("--same-domain-only", action="store_true", help="Limit crawling to the seed domain")

    # Multi-thread support
    parser.add_argument("--threads", type=int, default=1, help="Number of crawler threads (default: 1)")

    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    args = parser.parse_args()

    if args.threads < 1:
        raise SystemExit("--threads must be >= 1")

    cfg = CrawlerConfig(
        db_path=args.db,
        seed_url=args.seed,
        same_domain_only=args.same_domain_only,
        max_pages=args.max_pages,
        threads=args.threads,
        delay_seconds=args.delay,
    )

    crawler = Crawler(cfg)
    crawler.start_seed()
    crawler.start_workers(cfg.threads)

    app = create_app(args.db, crawler=crawler)

    # Auto-open browser
    open_host = args.host
    if open_host in ("0.0.0.0", "::"):
        open_host = "127.0.0.1"

    url_to_open = f"http://{open_host}:{args.port}/"

    def open_browser():
        if wait_port_open(open_host, args.port, timeout_sec=15.0):
            webbrowser.open(url_to_open)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()
