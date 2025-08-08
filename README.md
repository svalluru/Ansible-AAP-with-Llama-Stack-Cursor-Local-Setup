# Ansible-AAP-with-Llama-Stack-Cursor-Local-Setup

# From Zero to Working Agents: Wiring AAP’s MCP Server → Ollama → Llama Stack → Cursor

Want a clean, reproducible path from a local **AAP MCP Server** to a full **agentic workflow** that responds to natural‑language prompts (including inside Cursor)? Here’s a copy‑pasteable, end‑to‑end blog you can follow.

---

## What you’ll build

- A local **MCP Server** (AAP) speaking **Server‑Sent Events (SSE)**
- **Ollama** running a local model (e.g., `llama3.2:3b`)
- **Llama Stack** in Docker that can call your MCP tools
- A small **registration script** that plugs your MCP server into Llama Stack
- A **Cursor** custom MCP profile so you can ask “get me list of projects” and get tool‑powered results

---

## Prereqs

- macOS or Linux
- Python 3.10+ (or `uv` for Python project management)
- Docker
- Git
- Cursor (optional, for the final IDE test)
- Port availability: `8000` (MCP server), `11434` (Ollama), `8321` (Llama Stack)

> **Tip (macOS)**: Docker networking to host services uses `host.docker.internal`. We’ll lean on that later.

---

## 1) Setup the AAP MCP Server

**Repo:** `https://github.com/sibilleb/AAP-Enterprise-MCP-Server`

### 1.1 Clone and install
```bash
git clone https://github.com/sibilleb/AAP-Enterprise-MCP-Server
cd AAP-Enterprise-MCP-Server
```

If you’re using **uv** (recommended):
```bash
# Install uv if you don’t have it:
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

uv venv
. .venv/bin/activate
uv pip install -r requirements.txt
```

(If you’re using plain pip, just create a venv and `pip install -r requirements.txt`.)

### 1.2 Ensure SSE transport in `ansible.py`
Open `ansible.py` and make sure the MCP server is started with **SSE** transport:
```python
# inside ansible.py
# ensure something like:
mcp.run(transport="sse")
```

> If the project currently uses WebSocket or default transport, switch it to `transport="sse"` so Cursor and Llama Stack can connect easily.

### 1.3 Run the server
```bash
uv run ansible.py
```

**Expected output:**
```
(base) svalluru@svalluru1-mac AAP-Enterprise-MCP-Server % uv run ansible.py
INFO:     Started server process [12997]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Keep this terminal running.

---

## 2) Start Ollama (local LLM runtime)

**Quickstart:** `https://github.com/ollama/ollama/blob/main/README.md#quickstart`

### 2.1 Install & run
- Install Ollama for your OS.
- Start the daemon (it usually runs at `http://localhost:11434`).

### 2.2 Pull a model
```bash
ollama pull llama3.2:3b
```
(Use your preferred model—just keep the name consistent with the Llama Stack env var you’ll set.)

---

## 3) Start Llama Stack (container)

**Docs:** `https://llama-stack.readthedocs.io/en/latest/distributions/self_hosted_distro/starter.html`

**Important:** Environment variables must be set **before** the image name in `docker run`.

```bash
docker run -it   -p 8321:8321   -e INFERENCE_MODEL=llama3.2:3b   -e OLLAMA_URL=http://host.docker.internal:11434   container-id
```

> If you used the `distribution-starter:0.2.17` image, swap that in place of the image ID.  
> If the container says `llama-stack: not found`, the image may not have the CLI on PATH or expects a startup script. Use the exact starter image/command from the docs you followed.

Once running, Llama Stack should be listening at `http://localhost:8321`.

---

## 4) Register the AAP MCP server with Llama Stack

Create `mcp_client.py` anywhere on your host:

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

client.toolgroups.register(
    toolgroup_id="mcp::aap",
    provider_id="model-context-protocol",
    mcp_endpoint={"uri": "http://host.docker.internal:8000/sse"},
)
```

Run it (in a separate terminal):
```bash
python mcp_client.py
```

### 4.1 Verify registration
```bash
llama-stack-client toolgroups list
```

**Expected output:**
```
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ identifier         ┃ provider_id            ┃ args ┃ mcp_endpoint                                            ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ builtin::websearch │ tavily-search          │ None │ None                                                    │
│ builtin::rag       │ rag-runtime            │ None │ None                                                    │
│ mcp::aap           │ model-context-protocol │ None │ McpEndpoint(uri='http://host.docker.internal:8000/sse') │
└────────────────────┴────────────────────────┴──────┴─────────────────────────────────────────────────────────┘
```

---

## 5) Run a prompt via Llama Stack Client

Now that the toolgroup is registered, you can run the Llama Stack client to invoke an agent that calls your MCP tools based on user prompts. A typical pattern is:

```bash
llama-stack-client inference chat   --system "You are an agent that can use mcp::aap tools when helpful."   --user "get me list of projects"
```
or

run Llama-stack-client.py

You should see the model route to `mcp::aap` as needed and print a response that reflects your AAP MCP tool’s implementation.

> Exact flags may vary slightly depending on your Llama Stack build. If your distro exposes an “agent” or “tool-use” demo command, use that one. The key is: with the toolgroup in place, the agent can now call your MCP endpoints.

---

## 6) Use it in Cursor (Custom MCP Server)

Cursor can talk directly to MCP servers via a JSON profile.

1. In Cursor, go to **Settings → MCP** and **Create New Custom MCP Server**.
2. Use a minimal `mcp.json` similar to:

```json
{
  "name": "AAP MCP",
  "transport": "sse",
  "command": "curl",
  "args": ["-N", "http://localhost:8000/sse"],
  "env": {}
}
```

3. Save. In a new chat inside Cursor, ask:
   > **“get me list of projects”**

…Cursor should call your MCP server and return the tool output.

<img width="747" height="804" alt="Screenshot 2025-08-08 at 7 28 56 PM" src="https://github.com/user-attachments/assets/a07129da-ea3e-4fe9-a8dc-799106d62d33" />



