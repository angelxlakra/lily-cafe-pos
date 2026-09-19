"""Per-source throttling for the sign-in paths.

The owner and admin logins are single fixed username/password pairs, so
without this an attacker could guess the owner password at full network
speed against /api/v1/auth/login, or against the MCP consent page (which
authenticates the same credentials and whose per-transaction attempt cap is
no bound at all, because /register lets anyone open fresh transactions).

One limiter instance is shared by every endpoint that authenticates these
credentials, so neither path can be used to bypass the other's limit. It is
in-process state: the backend runs as a single machine, so that is enough,
and it costs no new dependency.
"""

import threading
import time
from collections import deque
from typing import Callable

from starlette.requests import Request

from app.core.config import settings


class LoginThrottle:
    """Sliding-window failure counter keyed by source.

    A source is locked out while it has ``max_failures`` or more failures in
    the last ``window_seconds``. Attempts made during a lockout are not
    counted, so the lockout ends ``window_seconds`` after the failure that
    triggered it rather than being extended by further guessing.
    """

    def __init__(
        self,
        max_failures: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        """Drop failures that have aged out of the window; returns what is left."""
        hits = self._failures.get(key)
        if hits is None:
            return deque()
        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            del self._failures[key]
        return hits

    def retry_after(self, key: str) -> int:
        """Seconds until ``key`` may try again, or 0 if it is not locked out."""
        with self._lock:
            now = self._clock()
            hits = self._prune(key, now)
            if len(hits) < self.max_failures:
                return 0
            # The lockout lifts once enough failures have aged out to drop
            # below the threshold, i.e. when the oldest one that still counts
            # leaves the window.
            oldest_counting = hits[len(hits) - self.max_failures]
            remaining = oldest_counting + self.window_seconds - now
            return max(1, int(remaining) + 1)

    def is_locked(self, key: str) -> bool:
        return self.retry_after(key) > 0

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._prune(key, now)
            self._failures.setdefault(key, deque()).append(now)

    def record_success(self, key: str) -> None:
        """A correct password clears the source's failure history."""
        with self._lock:
            self._failures.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


def client_ip(request: Request) -> str:
    """The real client address.

    The app runs behind Fly's proxy, so the socket peer is the proxy; Fly
    puts the client's address in Fly-Client-IP, and X-Forwarded-For is the
    generic equivalent (first hop is the client). The socket address is the
    fallback for local runs and tests.
    """
    fly = request.headers.get("fly-client-ip", "").strip()
    if fly:
        return fly
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    if request.client is not None and request.client.host:
        return request.client.host
    return "unknown"


LOCKED_OUT_MESSAGE = "Too many failed sign-in attempts. Please try again later."

login_throttle = LoginThrottle(
    max_failures=settings.LOGIN_MAX_FAILURES,
    window_seconds=settings.LOGIN_FAILURE_WINDOW_MINUTES * 60,
)
