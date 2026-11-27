# Run it

karakeep-mcp is one container. It needs to reach your Karakeep, and for claude.ai it needs a public HTTPS address of its own behind a reverse proxy.

1. Put [`compose.yaml`](https://github.com/Marceltov/karakeep-mcp/blob/main/compose.yaml) and a copy of [`.env.example`](https://github.com/Marceltov/karakeep-mcp/blob/main/.env.example) named `.env` in a folder on the server.
2. Fill in `.env` (all settings: [Configuration](configuration.md)):

    ```bash
    KARAKEEP_URL=https://karakeep.example.com
    MCP_BASE_URL=https://karakeep-mcp.example.com
    MCP_OAUTH_SECRET=$(openssl rand -hex 32)   # write the value, not this line
    ```

    `chmod 600 .env`, and keep the secret in your password manager.

3. Start it:

    ```bash
    docker compose pull && docker compose up -d
    curl -fsS http://localhost:8000/healthz   # {"status":"ok"}
    ```

4. Put your reverse proxy in front: `https://karakeep-mcp.example.com` to port 8000, with no extra login in front of it (claude.ai can't pass one; the login page is the gate). The proxy passes `/mcp`, `/.well-known/*`, `/authorize`, `/token`, `/register`, `/revoke` and `/login` as they are.

    ```caddy
    karakeep-mcp.example.com {
        reverse_proxy 127.0.0.1:8000
    }
    ```

5. Check it from outside: `curl -fsS https://karakeep-mcp.example.com/.well-known/oauth-authorization-server` shows the issuer.

Then [connect Claude](connecting.md).

To follow releases instead of `main`, pin a version: `image: ghcr.io/marceltov/karakeep-mcp:0.1`.
