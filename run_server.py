"""Local launcher for the GxP Sentinel API (127.0.0.1:8765)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.api.app import create_app

app = create_app("data/gxp.db")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8765, debug=False)
