"""Vercel serverless entrypoint.

Vercel imports this module and looks for an ASGI callable named ``app``.
The repository root is prepended to sys.path because the package is not
pip-installed in the serverless build - only the dependencies in
requirements.txt are.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from conciergeagent.server import app  # noqa: E402

__all__ = ["app"]
