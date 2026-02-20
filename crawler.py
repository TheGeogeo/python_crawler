# crawler.py
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

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
    same_domain_only: bool = False
    max_pages: Optional[int] = None
    threads: int = 1
    request_timeout: int = 10
    delay_seconds: float = 0.5
    user_agent: str = "SimpleCrawler/1.0"


class Crawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.stop_event = threading.Event()
        self._run_event = threading.Event()
        self._run_event.set()

        self.seed_host = urlparse(self.config.seed_url).netloc.lower()

        self._count_lock = threading.Lock()
        self._processed_pages = 0

        self._delay_lock = threading.Lock()

        self._workers_lock = threading.Lock()
        self._workers: Dict[int, Tuple[threading.Thread, threading.Event]] = {}
        self._next_worker_id = 0

    def start_seed(self) -> None:
        db.init_db(self.config.db_path)
        db.add_url(self.config.db_path, self.config.seed_url, depth=0, discovered_from=None)

    def stop(self) -> None:
        self.stop_event.set()
        self._run_event.set()
        with self._workers_lock:
            for _, worker_stop_event in self._workers.values():
                worker_stop_event.set()

    def pause(self) -> None:
        self._run_event.clear()

    def resume(self) -> None:
        self._run_event.set()

    def is_paused(self) -> bool:
        return not self._run_event.is_set()

    def set_delay_seconds(self, seconds: float) -> float:
        value = max(0.0, float(seconds))
        with self._delay_lock:
            self.config.delay_seconds = value
        return value

    def get_delay_seconds(self) -> float:
        with self._delay_lock:
            return float(self.config.delay_seconds)

    def _cleanup_dead_workers_locked(self) -> None:
        dead_ids = [worker_id for worker_id, (thread, _) in self._workers.items() if not thread.is_alive()]
        for worker_id in dead_ids:
            del self._workers[worker_id]

    def start_workers(self, count: int) -> int:
        if count <= 0:
            return 0

        to_start: list[threading.Thread] = []
        with self._workers_lock:
            self._cleanup_dead_workers_locked()
            for _ in range(count):
                worker_id = self._next_worker_id
                self._next_worker_id += 1

                worker_stop_event = threading.Event()
                thread = threading.Thread(
                    target=self.worker_loop,
                    args=(worker_id, worker_stop_event),
                    name=f"crawler-{worker_id}",
                    daemon=True,
                )
                self._workers[worker_id] = (thread, worker_stop_event)
                to_start.append(thread)

        for thread in to_start:
            thread.start()

        return len(to_start)

    def add_threads(self, count: int) -> int:
        return self.start_workers(count)

    def remove_threads(self, count: int) -> int:
        if count <= 0:
            return 0

        with self._workers_lock:
            self._cleanup_dead_workers_locked()
            active_ids = [
                worker_id
                for worker_id in sorted(self._workers.keys(), reverse=True)
                if self._workers[worker_id][0].is_alive() and not self._workers[worker_id][1].is_set()
            ]
            to_stop_ids = active_ids[:count]
            for worker_id in to_stop_ids:
                _, worker_stop_event = self._workers[worker_id]
                worker_stop_event.set()

        return len(to_stop_ids)

    def runtime_status(self) -> Dict[str, Any]:
        with self._workers_lock:
            self._cleanup_dead_workers_locked()
            worker_ids = sorted(self._workers.keys())
            alive_threads = sum(1 for thread, _ in self._workers.values() if thread.is_alive())
            configured_threads = len(self._workers)

        with self._count_lock:
            processed_pages = self._processed_pages

        return {
            "paused": self.is_paused(),
            "stop_requested": self.stop_event.is_set(),
            "delay_seconds": self.get_delay_seconds(),
            "configured_threads": configured_threads,
            "alive_threads": alive_threads,
            "worker_ids": worker_ids,
            "processed_pages": processed_pages,
            "max_pages": self.config.max_pages,
        }

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

    def worker_loop(self, worker_id: int, worker_stop_event: Optional[threading.Event] = None) -> None:
        """
        Worker loop. Multiple workers can run in parallel.
        Each worker has its own requests session.
        """
        if worker_stop_event is None:
            worker_stop_event = threading.Event()

        session = requests.Session()
        session.headers.update({"User-Agent": self.config.user_agent})

        while not self.stop_event.is_set() and not worker_stop_event.is_set():
            if self._should_stop_for_limit():
                self.stop_event.set()
                break

            if self.is_paused():
                time.sleep(0.2)
                continue

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
                    delay = self.get_delay_seconds()
                    if delay > 0:
                        time.sleep(delay)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    normalized = normalize_url(resp.url, a.get("href"))
                    if not normalized:
                        continue
                    if not self._allowed_by_scope(normalized):
                        continue
                    db.add_url(self.config.db_path, normalized, depth=depth + 1, discovered_from=url)

                db.mark_crawled(self.config.db_path, url_id, status_code)
                self._mark_processed_and_maybe_stop()

            except Exception as e:
                db.mark_error(self.config.db_path, url_id, str(e))
                self._mark_processed_and_maybe_stop()

            delay = self.get_delay_seconds()
            if delay > 0:
                time.sleep(delay)
