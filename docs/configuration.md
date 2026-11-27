# Configuration

Every setting is an environment variable, read in one place (`src/karakeep_mcp/config.py`) and listed with comments in [`.env.example`](https://github.com/Marceltov/karakeep-mcp/blob/main/.env.example).

| Variable | Default | What it does |
|---|---|---|
| `KARAKEEP_URL` | required | Your Karakeep, as this server reaches it (a LAN address is fine). |
| `KARAKEEP_PUBLIC_URL` | `KARAKEEP_URL` | Karakeep's public address, for the links in results. |
| `MCP_BASE_URL` | unset | This server's public HTTPS address, without `/mcp`. With `MCP_OAUTH_SECRET` it turns the OAuth login on. |
| `MCP_OAUTH_SECRET` | unset | Encrypts the login store; at least 32 random characters. Changing it signs everyone out. |
| `DATA_DIR` | `/data` | Where the login store lives (`DATA_DIR/oauth`). |
| `VERIFY_TLS` | `true` | Check Karakeep's certificate against the operating system's trust store. `false` turns checking off. |
| `MCP_HOST`, `MCP_PORT` | `0.0.0.0`, `8000` | Where the server listens. |
| `MCP_ALLOWED_HOSTS` | unset | Comma-separated Host names to accept; unset accepts any (the token is the gate). |

Without `MCP_BASE_URL` and `MCP_OAUTH_SECRET` there is no login page: the server accepts only Karakeep API keys in the `Authorization` header, which is enough for Claude Code on a LAN.

**The login store** holds the OAuth clients and tokens, encrypted, and each login's Karakeep key. It is cheap to lose: everyone signs in again, nothing else. A volume that is not backed up is fine.
