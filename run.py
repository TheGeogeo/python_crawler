# run.py
import argparse
import threading
import time
import socket
import webbrowser

import uvicorn

from crawler import CrawlerConfig, Crawler
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
    parser.add_argument("--seed", required=True, help="URL de départ")
    parser.add_argument("--db", default="crawler.sqlite", help="Fichier SQLite")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)

    # optionnel : si omis => illimité
    parser.add_argument("--max-pages", type=int, default=None, help="Nombre max de pages (si omis: illimité)")

    # défaut : crawl tout ; flag si tu veux limiter au domaine du seed
    parser.add_argument("--same-domain-only", action="store_true", help="Limiter le crawl au domaine du seed")

    # ✅ multi-threads
    parser.add_argument("--threads", type=int, default=1, help="Nombre de threads crawler (défaut: 1)")

    parser.add_argument("--delay", type=float, default=0.5, help="Délai entre requêtes (secondes)")
    args = parser.parse_args()

    if args.threads < 1:
        raise SystemExit("--threads doit être >= 1")

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

    # Lance N threads workers
    for i in range(cfg.threads):
        t = threading.Thread(target=crawler.worker_loop, args=(i,), name=f"crawler-{i}", daemon=True)
        t.start()

    app = create_app(args.db)

    # ouverture auto navigateur
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