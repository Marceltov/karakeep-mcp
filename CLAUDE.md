# CLAUDE.md

A FastMCP server in front of Karakeep's REST API: each person signs in once (OAuth, mcp-login-oauth) with their own Karakeep API key, and every tool acts as them.

## Commands

- `uv sync` — install
- `uv run pytest -q` — tests (`tests/live/` runs only with `KARAKEEP_LIVE_URL` and `KARAKEEP_LIVE_KEY` set)
- `uv run ruff format` and `uv run ruff check` — format and lint (160 columns, shared `ruff.toml`)
- `uv run karakeep-mcp` — run the server (needs `KARAKEEP_URL`; see `.env.example`)
- `uv run --group docs mkdocs serve` — docs site

## Architecture

- `src/karakeep_mcp/config.py` — every setting, from the environment; nothing else reads `os.environ`.
- `karakeep.py` — the one HTTP client to Karakeep (REST `/api/v1` and tRPC); maps Karakeep's errors to messages for Claude.
- `auth.py` — the login form: an API key, or email and password exchanged for a key named `Claude`. The grant is `{"api_key", "key_id"}`.
- `links.py` — web-app URLs and the result helper.
- `tools/` — one module per area (bookmarks, lists, tags, highlights, assets), each with `register(mcp, client)`.
- `server.py` — builds the FastMCP server, serves `/mcp` and `/healthz`.

## Rules

- Every tool result is a dict with `guidance: list[str]` (what to do next, built from what this call did) and a `url` into Karakeep's web app for every bookmark, list and tag it names.
- Tool names follow upstream's `karakeep-app/karakeep` MCP server (kebab-case), so prompts carry over.
- Tests never touch `/data`: `tests/conftest.py` points `DATA_DIR` at a temp dir for every test.
- Decisions are ADRs in `docs/adr/`.
