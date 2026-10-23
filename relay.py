"""Relay: public health endpoint + /ws/agent (PC agent) + /run (MCP caller).
Single public port (Render $PORT). Commands correlated by id."""
import asyncio, json, uuid, os
from aiohttp import web, WSMsgType

TOKEN = os.environ.get("PC_AGENT_TOKEN", "")
agent_ws = None
pending = {}  # id -> Future

async def health(request):
    return web.Response(text="ok")

async def ws_agent(request):
    global agent_ws
    if request.headers.get("X-Agent-Token") != TOKEN:
        return web.Response(status=403, text="bad token")
    ws = web.WebSocketResponse(max_msg_size=10 * 1024 * 1024)
    await ws.prepare(request)
    agent_ws = ws
    print("agent connected", flush=True)
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception:
                    continue
                rid = data.get("id")
                if rid in pending and not pending[rid].done():
                    pending[rid].set_result(data)
    finally:
        if agent_ws is ws:
            agent_ws = None
        print("agent disconnected", flush=True)
    return ws

async def run_cmd(request):
    if request.headers.get("X-Agent-Token") != TOKEN:
        return web.json_response({"error": "forbidden"}, status=403)
    if agent_ws is None or agent_ws.closed:
        return web.json_response({"error": "agent offline"}, status=503)
    body = await request.json()
    rid = uuid.uuid4().hex
    fut = asyncio.get_event_loop().create_future()
    pending[rid] = fut
    await agent_ws.send_str(json.dumps({"id": rid, "cmd": body.get("cmd", ""), "timeout": body.get("timeout", 120)}))
    try:
        res = await asyncio.wait_for(fut, timeout=body.get("timeout", 120) + 15)
    except asyncio.TimeoutError:
        res = {"id": rid, "error": "timeout"}
    pending.pop(rid, None)
    return web.json_response(res)

app = web.Application()
app.router.add_get("/", health)
app.router.add_get("/ws/agent", ws_agent)
app.router.add_post("/run", run_cmd)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), print=None)
