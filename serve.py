"""Run the API on port 8006. From this folder: python serve.py"""

from __future__ import annotations

import os
import pathlib

import uvicorn

ROOT = pathlib.Path(__file__).resolve().parent
os.chdir(ROOT)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8006,
        reload=True,
    )
