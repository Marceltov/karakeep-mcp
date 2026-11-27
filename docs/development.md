# Development and releases

```bash
uv sync
uv run pytest -q                 # unit tests against a fake Karakeep (respx)
uv run ruff format && uv run ruff check
npx prettier@3 --check .         # YAML, JSON, README; not docs/
uvx --with mkdocs-material==9.7.7 --with 'mkdocs<2' mkdocs serve
```

**Live tests** run against a real Karakeep and create and delete their own bookmark:

```bash
KARAKEEP_LIVE_URL=https://karakeep.example.com KARAKEEP_LIVE_KEY=ak2_... uv run pytest -q tests/live
```

With `KARAKEEP_LIVE_EMAIL` and `KARAKEEP_LIVE_PASSWORD` they also mint a key by email and password and revoke it again.

**Layout:** `config.py` (every setting), `karakeep.py` (the one HTTP client), `auth.py` (the login form and its grant), `links.py` (web links, result shapes), `tools/` (one module per area), `server.py`.

**A new tool** goes into its area's module, returns a `Result` with `guidance`, and gets a test that checks its request, its `guidance` and its `url`. `test_every_tool_declares_guidance_in_output_schema` counts the tools: change the number there.

**Releases:** set `version` in `pyproject.toml`, merge, then tag `vX.Y.Z` on `main` with an annotated tag whose subject is the release's headline. The release workflow checks the tag, runs the tests, publishes `ghcr.io/marceltov/karakeep-mcp:X.Y.Z`, `X.Y` and `latest` with SBOM and provenance, and writes the release notes from the merged pull requests.
