"""
BuildReady-AI root entry point.
Exposes 'app' so running `uvicorn main:app` directly from the project root works seamlessly,
in addition to `uvicorn backend.main:app`.
"""
import sys
from pathlib import Path

# Add backend directory to sys.path so modules resolve smoothly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.main import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
