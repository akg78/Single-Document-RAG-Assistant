"""Import shims so ragas can load against newer langchain-community."""

from __future__ import annotations

import sys
import types


def ensure_ragas_compat() -> None:
    """Provide langchain_community.chat_models.vertexai if the package dropped it."""
    mod_name = "langchain_community.chat_models.vertexai"
    if mod_name in sys.modules:
        return
    try:
        __import__(mod_name)
        return
    except ModuleNotFoundError:
        pass

    stub = types.ModuleType(mod_name)

    class ChatVertexAI:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise RuntimeError("ChatVertexAI is unavailable in this environment.")

    stub.ChatVertexAI = ChatVertexAI
    sys.modules[mod_name] = stub

    # Ensure parent packages exist in sys.modules for nested imports
    parent = "langchain_community.chat_models"
    if parent not in sys.modules:
        try:
            __import__(parent)
        except ModuleNotFoundError:
            sys.modules[parent] = types.ModuleType(parent)
