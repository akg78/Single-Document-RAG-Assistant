"""Tenacity-based retry helpers."""

from collections.abc import Callable
from typing import TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

T = TypeVar("T")


def with_retry(
    *,
    attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 8.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator: exponential backoff on transient failures."""

    return retry(
        reraise=True,
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((OSError, RuntimeError, ConnectionError, TimeoutError)),
    )
