"""stdio MCP server for Hermes on Render: exposes pc_run tool -> relay /run."""
import json, os, sys, urllib.request

RELAY = "http://127.0.0.1:" + os.environ.get("PORT", "10000") + "/run"
TOKEN = os.environ.get("PC_AGENT_TOKEN", "")

def rpc_result(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

TOOLS = [{
    "name": "pc_run",
    "description": "Run a shell command on Luka's Windows PC (when it's on and the agent is connected). Returns stdout/stderr/exit_code.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to run (Windows cmd syntax)"},
            "timeout": {"type": "integer", "description": "Seconds, default 120, max 600"}
        },
        "required": ["command"]
    }
}]

def call_pc(cmd, timeout):
    req = urllib.request.Request(RELAY,
        data=json.dumps({"cmd": cmd, "timeout": timeout}).encode(),
        headers={"Content-Type": "application/json", "X-Agent-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=timeout + 20) as r:
        return json.loads(r.read().decode())

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    rid = msg.get("id")
    method = msg.get("method", "")
    if method == "initialize":
        send(rpc_result(rid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "pc-bridge", "version": "1.0"}}))
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send(rpc_result(rid, {"tools": TOOLS}))
    elif method == "tools/call":
        params = msg.get("params", {})
        if params.get("name") == "pc_run":
            args = params.get("arguments", {})
            try:
                res = call_pc(args.get("command", ""), int(args.get("timeout", 120)))
                text = res.get("output") or res.get("error") or "(no output)"
                if res.get("exit_code") not in (None, 0):
                    text += f"\n[exit_code={res['exit_code']}]"
                send(rpc_result(rid, {"content": [{"type": "text", "text": text}]}))
            except Exception as e:
                send(rpc_result(rid, {"content": [{"type": "text", "text": f"pc_run failed: {str(e)[:300]}"}], "isError": True}))
        else:
            send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown tool"}})
    elif rid is not None:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown method {method}"}})
