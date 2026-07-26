# Portfolio Research MCP Server 📈

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that gives any
AI coding assistant or chat client live **stock and portfolio research** tools, powered by
Yahoo Finance data. Written in Python with [FastMCP](https://gofastmcp.com), it speaks
**Streamable HTTP** so you can host it once and connect from Claude, Cursor, VS Code,
Google Antigravity, Windsurf, and terminal-based agents.

> Ask your assistant: *"Analyze my portfolio: 10 AAPL bought at $150 and 5 MSFT at $300,"*
> and it will call this server, price the holdings live, and report your gain/loss and weights.

---

## 🚀 Try it instantly (public demo)

A live instance is already hosted — you don't need to deploy anything to test it.

| | |
|---|---|
| **URL** | `https://stock-research-mcp.onrender.com/mcp` |
| **Auth header** | `Authorization: Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98` |

Drop those into any config block in [Connect it to your IDE / agent](#connect-it-to-your-ide--agent) below and start asking questions.

> ⚠️ **This is a shared public demo token** for trying the server out. It may be rate-limited,
> rotated, or taken down at any time, and the instance sleeps after ~15 min idle (first call
> may take 30–60s to wake). For anything real, [deploy your own](#deploy-free-on-render) and set
> your own private `MCP_AUTH_TOKEN`.

---

## Tools

| Tool | What it does |
|------|--------------|
| `get_quote` | Latest price, day change, volume, market cap for a ticker |
| `get_fundamentals` | P/E, EPS, dividend yield, beta, 52-week range, sector, analyst rating |
| `get_price_history` | Historical OHLC candles (`period`/`interval`) for trend analysis |
| `get_news` | Recent news headlines with links for a ticker |
| `analyze_portfolio` | Value a set of holdings; per-position + total gain/loss and weights |
| `compare_tickers` | Side-by-side valuation snapshot for several tickers |

Data source: [`yfinance`](https://pypi.org/project/yfinance/) — free, no API key required.

---

## Quick start (local)

Requires Python 3.10+.

```bash
git clone <your-repo-url> stock-research-mcp
cd stock-research-mcp

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python server.py
```

The server starts at:

- **MCP endpoint:** `http://127.0.0.1:8000/mcp`
- **Health check:** `http://127.0.0.1:8000/health` → `ok`

Locally, auth is **disabled** unless you set `MCP_AUTH_TOKEN` (see [Security](#security)).

---

## Deploy free on Render

Render's free web-service tier hosts this at a public HTTPS URL. A `render.yaml` blueprint is
included.

1. Push this repo to GitHub.
2. In the [Render dashboard](https://dashboard.render.com): **New + → Blueprint**, select your repo.
   Render reads `render.yaml` and provisions a free web service.
   *(Or **New + → Web Service** manually: Build `pip install -r requirements.txt`,
   Start `python server.py`.)*
3. Under **Environment**, set a secret `MCP_AUTH_TOKEN` (a long random string).
4. Deploy. Your server is live at:

   ```
   https://<your-app-name>.onrender.com/mcp
   ```

> ⚠️ **Free-tier cold starts:** free instances spin down after ~15 minutes idle. The next
> request wakes it and can take **30–60 seconds**. Upgrade to any paid instance to stay
> always-on. Hit `/health` to warm it before a demo.

---

## Connect it to your IDE / agent

The blocks below use the **public demo** URL and token so you can copy-paste and go. To use
your own deployment, swap in your Render URL and your private `MCP_AUTH_TOKEN` (or
`http://127.0.0.1:8000/mcp` with no header for a local run).

> **⚠️ The config key differs by client.** Cursor and VS Code use `url`; **Antigravity and
> Windsurf use `serverUrl`**; Claude Code uses a CLI command. Copy the right block below.

### Claude Code (terminal)

```bash
claude mcp add --transport http stock-research \
  https://stock-research-mcp.onrender.com/mcp \
  --header "Authorization: Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
```

Then check it: `claude mcp list`. Remove with `claude mcp remove stock-research`.

### Claude Desktop

Claude Desktop connects to remote servers through the `mcp-remote` bridge (needs Node.js).
Edit `claude_desktop_config.json` (Settings → Developer → Edit Config):

```json
{
  "mcpServers": {
    "stock-research": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "https://stock-research-mcp.onrender.com/mcp",
        "--header", "Authorization: Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
      ]
    }
  }
}
```

Restart Claude Desktop. Tools appear under the 🔌 (MCP) icon.

### Cursor

Edit `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "stock-research": {
      "url": "https://stock-research-mcp.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
      }
    }
  }
}
```

Then **Settings → MCP** and confirm the server shows green.

### Google Antigravity

Antigravity uses **`serverUrl`** (not `url`). Open the MCP store via the **"…"** menu in the
agent panel → **Manage MCP Servers → View raw config**, or edit
`~/.gemini/config/mcp_config.json` directly:

```json
{
  "mcpServers": {
    "stock-research": {
      "serverUrl": "https://stock-research-mcp.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
      }
    }
  }
}
```

Save, then **Customizations → Installed MCP Servers → Refresh**.

### Windsurf

Windsurf also uses **`serverUrl`**. Edit `~/.codeium/windsurf/mcp_config.json`
(or **Settings → Cascade → MCP Servers → Manage → View raw config**):

```json
{
  "mcpServers": {
    "stock-research": {
      "serverUrl": "https://stock-research-mcp.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
      }
    }
  }
}
```

Click **Refresh** in the MCP panel.

### VS Code (Copilot agent mode)

Create `.vscode/mcp.json` in your workspace (or run **MCP: Add Server** from the Command
Palette):

```json
{
  "servers": {
    "stock-research": {
      "type": "http",
      "url": "https://stock-research-mcp.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
      }
    }
  }
}
```

Open Copilot Chat, switch to **Agent** mode, and the tools become available.

### Other terminal / stdio-only agents

Clients that speak the remote MCP shape can reuse the Cursor block above (`url` + `headers`).
For agents that **only** support local stdio servers, bridge to the remote URL with
[`mcp-remote`](https://www.npmjs.com/package/mcp-remote):

```bash
npx -y mcp-remote https://stock-research-mcp.onrender.com/mcp \
  --header "Authorization: Bearer mYfUEnx-jnDKlUTHIkUXhCWhMBPgxuzmSvCfxegrt98"
```

Point the client's `command`/`args` at that (as in the Claude Desktop example).

---

## Usage examples

Once connected, try prompts like:

- *"What's AAPL trading at right now?"* → `get_quote`
- *"Compare NVDA, AMD and INTC on valuation."* → `compare_tickers`
- *"Show me TSLA's price history over the last 6 months."* → `get_price_history`
- *"Any recent news on MSFT?"* → `get_news`
- *"Analyze my portfolio: 10 AAPL at $150, 5 MSFT at $300, 20 NVDA at $110."* → `analyze_portfolio`

---

## Security

- If `MCP_AUTH_TOKEN` is **set**, every request to `/mcp` must send
  `Authorization: Bearer <token>` or it's rejected with `401`. Always set it in production.
- If it's **unset**, auth is off — fine for `localhost`, never for a public URL.
- A shared bearer token is a pragmatic choice for a personal/portfolio project. The MCP spec's
  full answer for public servers is **OAuth 2.1 with PKCE**; adopt that if you expose this to
  untrusted clients.
- The token shown in this README is a **deliberately public demo token** so anyone can try the
  hosted instance. Never reuse it for a private deployment — generate your own with
  `python -c "import secrets; print(secrets.token_urlsafe(32))"` and keep it secret.

---

## Project structure

```
.
├── server.py          # FastMCP app: tools, bearer-auth middleware, /health, HTTP transport
├── portfolio.py       # yfinance data layer (pure, testable, returns plain dicts)
├── requirements.txt   # fastmcp, yfinance, uvicorn
├── render.yaml        # Render blueprint (free web service)
├── .env.example       # MCP_AUTH_TOKEN, PORT
└── README.md
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| First request after idle is very slow | Render free-tier cold start (~30–60s). Ping `/health` to warm it, or upgrade the instance. |
| `401 Unauthorized` | Token in the client header must exactly match `MCP_AUTH_TOKEN` on the server. |
| Empty / `error` fields from a tool | yfinance can rate-limit or return partial data. Retry shortly, or verify the ticker symbol. |
| Client shows the server but no tools | Confirm the URL ends in `/mcp` and (for Antigravity/Windsurf) that you used `serverUrl`, not `url`. |

---

## License

MIT — do whatever you like. Data is provided by Yahoo Finance via `yfinance` and is subject to
their terms; this project is for research/educational use, not investment advice.
