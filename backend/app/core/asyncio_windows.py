"""
Windows: Playwright precisa de subprocessos asyncio — só funciona com ProactorEventLoop.
SelectorEventLoop → NotImplementedError vazio no login (sintoma comum com uvicorn/IDE).
"""
from __future__ import annotations

import asyncio
import sys


def ensure_windows_proactor_event_loop_policy() -> str:
    """Define Proactor no Windows; devolve nome da policy activa."""
    if sys.platform != "win32":
        return type(asyncio.get_event_loop_policy()).__name__
    policy = asyncio.WindowsProactorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    return type(asyncio.get_event_loop_policy()).__name__
