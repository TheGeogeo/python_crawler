# crawler.py
import time
import threading
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

import db


def normalize_url(base: str, href: str) -> Optional[str]:
    if not href:
        return None

    href = href.strip()
    low = href.lower()
    if low.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None

    abs_url = urljoin(base, href)
    abs_url, _ = urldefrag(abs_url)

    parsed = urlparse(abs_url)
    if parsed.scheme not in ("http", "https"):
        return None

    return parsed.geturl().strip()


@dataclass
class CrawlerConfig:
    db_path: str
    seed_url: str
    same_domain_only: bool = False          # défaut: crawl tout
    max_pages: Optional[int] = None         # défaut: illimité
    threads: int = 1                        # défaut: 1 thread
    request_timeout: int = 10
    delay_seconds: float = 0.5
    user_agent: str = "SimpleCrawler/1.0"


class Crawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.stop_event = threading.Event()

        self.seed_host = urlparse(self.config.seed_url).netloc.lower()

        self._count_lock = threading.Lock()
        self._processed_pages = 0

    def start_seed(self) -> None:
        db.init_db(self.config.db_path)
        db.add_url(self.config.db_path, self.config.seed_url, depth=0, discovered_from=None)

    def stop(self) -> None:
        self.stop_event.set()

    def _allowed_by_scope(self, url: str) -> bool:
        if not self.config.same_domain_only:
            return True
        return urlparse(url).netloc.lower() == self.seed_host

    def _should_stop_for_limit(self) -> bool:
        if self.config.max_pages is None:
            return False
        with self._count_lock:
            return self._processed_pages >= self.config.max_pages

    def _mark_processed_and_maybe_stop(self) -> None:
        if self.config.max_pages is None:
            return
        with self._count_lock:
            self._processed_pages += 1
            if self._processed_pages >= self.config.max_pages:
                self.stop_event.set()

    def worker_loop(self, worker_id: int) -> None:
        """
        Boucle d’un worker. Plusieurs workers peuvent tourner en parallèle.
        Chaque worker a sa propre session requests (thread-safe).
        """
        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})

        while not self.stop_event.is_set():
            if self._should_stop_for_limit():
                self.stop_event.set()
                break

            item = db.pop_next_queued(self.config.db_path)
            if item is None:
                time.sleep(0.3)
                continue

            url_id = item["id"]
            url = item["url"]
            depth = item["depth"]

            try:
                resp = session.get(url, timeout=self.config.request_timeout, allow_redirects=True)
                status_code = resp.status_code

                content_type = (resp.headers.get("Content-Type") or "").lower()
                if "text/html" not in content_type:
                    db.mark_crawled(self.config.db_path, url_id, status_code)
                    self._mark_processed_and_maybe_stop()
                    time.sleep(self.config.delay_seconds)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    n = normalize_url(resp.url, a.get("href"))
                    if not n:
                        continue
                    if not self._allowed_by_scope(n):
                        continue
                    db.add_url(self.config.db_path, n, depth=depth + 1, discovered_from=url)

                db.mark_crawled(self.config.db_path, url_id, status_code)
                self._mark_processed_and_maybe_stop()

            except Exception as e:
                db.mark_error(self.config.db_path, url_id, str(e))
                self._mark_processed_and_maybe_stop()

            time.sleep(self.config.delay_seconds)