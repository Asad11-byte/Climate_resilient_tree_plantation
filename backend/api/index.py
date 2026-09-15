"""
Vercel entrypoint. Vercel's Python builder auto-detects an exported ASGI
`app` in this file and runs it as a serverless function — no Mangum or
other adapter needed, unlike some other serverless platforms.

This file is intentionally just a re-export: all real application code
stays in app/main.py and below, importable normally, so nothing about the
app's internal structure needs to change for Vercel specifically.
"""
import sys
from pathlib import Path

# backend/api/index.py needs backend/ itself on the import path so
# `from app...` imports (used throughout the existing codebase) resolve
# the same way they do when running `uvicorn app.main:app` from backend/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402