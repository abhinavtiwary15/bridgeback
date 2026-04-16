import asyncio
import logging
import subprocess
import sys

import httpx
import uvicorn
import websockets
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import StreamingResponse

# ── Setup Logging ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BridgeBackRunner")

app = FastAPI(title="BridgeBack Gateway")

# ── Internal Ports ───────────────────────────────────────────────────────────
STREAMLIT_PORT = 8501
FASTAPI_PORT = 8000
GATEWAY_PORT = 7860


# ── Proxy Logic (HTTP) ──────────────────────────────────────────────────────
async def proxy_request(request: Request, target_url: str):
    client = httpx.AsyncClient(base_url=target_url)
    url = request.url.path
    if request.url.query:
        url += f"?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)

    method = request.method
    content = await request.body()

    try:
        response = await client.request(
            method, url, headers=headers, content=content, follow_redirects=True
        )
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return {"error": "Target service unavailable", "detail": str(e)}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_api(path: str, request: Request):
    return await proxy_request(request, f"http://localhost:{FASTAPI_PORT}")


# ── WebSocket Bridge (Streamlit Fix) ─────────────────────────────────────────
@app.websocket("/{path:path}")
async def proxy_websocket(websocket: WebSocket, path: str):
    """Bridge for Streamlit WebSockets."""
    target_ws_url = f"ws://localhost:{STREAMLIT_PORT}/{path}"
    await websocket.accept()

    try:
        async with websockets.connect(target_ws_url) as target_ws:

            async def forward_to_client():
                async for message in target_ws:
                    await websocket.send_text(message) if isinstance(
                        message, str
                    ) else await websocket.send_bytes(message)

            from fastapi import WebSocketDisconnect

            async def forward_to_target():
                try:
                    while True:
                        message = await websocket.receive()
                        if "text" in message:
                            await target_ws.send(message["text"])
                        elif "bytes" in message:
                            await target_ws.send(message["bytes"])
                        elif message["type"] == "websocket.disconnect":
                            break
                except WebSocketDisconnect:
                    pass

            await asyncio.gather(forward_to_client(), forward_to_target())
    except Exception as e:
        logger.error(f"WS Bridge Error: {e}")
    finally:
        await websocket.close()


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_web(path: str, request: Request):
    return await proxy_request(request, f"http://localhost:{STREAMLIT_PORT}")


# ── Process Management ───────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "gateway":
        uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
    else:
        # 1. Start Streamlit (CORS + XSRF must be disabled for reverse-proxy to work)
        st_proc = subprocess.Popen(
            [
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
            ]
        )

        # Wait for Streamlit to be ready before accepting gateway traffic
        import time

        logger.info("Waiting for Streamlit to start...")
        time.sleep(8)

        # 2. Start FastAPI
        api_proc = subprocess.Popen(
            [
                "uvicorn",
                "api.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(FASTAPI_PORT),
            ]
        )

        # 3. Start Gateway
        logger.info(f"Starting Multi-Platform Gateway on port {GATEWAY_PORT}...")
        try:
            uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
        finally:
            st_proc.terminate()
            api_proc.terminate()
