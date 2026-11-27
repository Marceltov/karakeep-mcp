# karakeep-mcp

An MCP server for [Karakeep](https://karakeep.app): each person signs in once from claude.ai, the Claude apps or Claude Code with their own Karakeep API key (or email and password), and Claude searches, reads, saves and tags their bookmarks as them. Thirty tools, named as in Karakeep's own MCP server, which speaks only stdio and acts as one user per process ([why this one exists](https://karakeep-mcp.marceltov.de/adr/0001-own-server-instead-of-upstreams-stdio-one/)).

```bash
curl -O https://raw.githubusercontent.com/Marceltov/karakeep-mcp/main/compose.yaml
curl -o .env https://raw.githubusercontent.com/Marceltov/karakeep-mcp/main/.env.example   # fill in, chmod 600
docker compose pull && docker compose up -d
```

**Documentation:** [karakeep-mcp.marceltov.de](https://karakeep-mcp.marceltov.de/): [run it](https://karakeep-mcp.marceltov.de/getting-started/), [connect Claude](https://karakeep-mcp.marceltov.de/connecting/), [tools](https://karakeep-mcp.marceltov.de/tools/), [configuration](https://karakeep-mcp.marceltov.de/configuration/).

Licensed under the [MIT License](https://github.com/Marceltov/karakeep-mcp/blob/main/LICENSE).
