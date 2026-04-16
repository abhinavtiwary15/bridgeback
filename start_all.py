"""
BridgeBack — HF Spaces entrypoint.
Runs Streamlit directly on port 7860 (no proxy needed — app uses LocalBackend).
FastAPI is started in background for any internal API calls.
"""

import logging
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BridgeBackRunner")

STREAMLIT_PORT = 7860
FASTAPI_PORT = 8000


if __name__ == "__main__":
    # Start FastAPI in background (used by LocalBackend internally)
    api_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(FASTAPI_PORT),
        ]
    )
    logger.info(f"FastAPI started on port {FASTAPI_PORT}")

    # Small delay to let FastAPI initialise
    time.sleep(3)

    # Run Streamlit directly on the exposed port — no proxy needed
    logger.info(f"Starting Streamlit on port {STREAMLIT_PORT}...")
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.port",
                str(STREAMLIT_PORT),
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
                "--server.enableCORS",
                "false",
                "--server.enableXsrfProtection",
                "false",
            ],
            check=True,
        )
    finally:
        api_proc.terminate()
