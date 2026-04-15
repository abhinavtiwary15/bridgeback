import subprocess
import time
import sys
import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import logging

# ── Setup Logging ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BridgeBackRunner")

app = FastAPI(title="BridgeBack Gateway")

# ── Internal Ports ───────────────────────────────────────────────────────────
STREAMLIT_PORT = 8501
FASTAPI_PORT = 8000
GATEWAY_PORT = 7860  # Hugging Face default

# ── Proxy Logic ──────────────────────────────────────────────────────────────
async def proxy_request(request: Request, target_url: str):
    client = httpx.AsyncClient(base_url=target_url)
    url = request.url.path
    if request.url.query:
        url += f"?{request.url.query}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Simple proxy for all methods
    method = request.method
    content = await request.body()
    
    try:
        response = await client.request(
            method, 
            url, 
            headers=headers, 
            content=content,
            follow_redirects=False
        )
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return {"error": "Target service unavailable", "detail": str(e)}

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_api(path: str, request: Request):
    """Route all /api requests to the FastAPI backend."""
    target = f"http://localhost:{FASTAPI_PORT}"
    return await proxy_request(request, target)

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_web(path: str, request: Request):
    """Route everything else to Streamlit."""
    target = f"http://localhost:{STREAMLIT_PORT}"
    return await proxy_request(request, target)

# ── Process Management ───────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gateway":
        # Run the gateway proxy
        uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
    else:
        # 1. Start Streamlit
        logger.info("Starting Streamlit...")
        st_proc = subprocess.Popen([
            "streamlit", "run", "app.py", 
            "--server.port", str(STREAMLIT_PORT), 
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ])
        
        # 2. Start FastAPI
        logger.info("Starting FastAPI...")
        api_proc = subprocess.Popen([
            "uvicorn", "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", str(FASTAPI_PORT)
        ])
        
        # 3. Start Gateway in this process
        logger.info(f"Starting Gateway on port {GATEWAY_PORT}...")
        try:
            uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
        finally:
            st_proc.terminate()
            api_proc.terminate()
