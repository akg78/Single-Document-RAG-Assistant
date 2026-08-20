"""Pytest configuration — keep tests fast by skipping model preload."""

import os

os.environ.setdefault("PRELOAD_MODELS", "false")
