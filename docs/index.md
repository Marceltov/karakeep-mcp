---
hide:
  - toc
---

<div class="kk-hero" markdown>
<img class="kk-hero__mark" src="assets/icon.svg" alt="">

# Your Karakeep bookmarks, for Claude

<p class="kk-hero__lead">An MCP server in front of <a href="https://karakeep.app">Karakeep</a>. Each person signs in once from claude.ai, the Claude apps or Claude Code, with their own Karakeep API key, and Claude searches, reads, saves and tags their bookmarks as them, and only theirs.</p>

[Run it](getting-started.md){ .md-button .md-button--primary }
[Connect Claude](connecting.md){ .md-button }

</div>

## How it works

```mermaid
sequenceDiagram
  participant C as Claude (claude.ai)
  participant S as karakeep-mcp
  participant K as Karakeep
  C->>S: connect: register, authorize (PKCE)
  S->>C: login page: API key, or email and password
  C->>S: the person submits the form
  S->>K: GET /api/v1/users/me with the key<br/>(or apiKeys.exchange: a new key named Claude)
  K-->>S: it works
  S->>C: OAuth tokens (the key stays on the server, encrypted)
  C->>S: tools/call search-bookmarks
  S->>K: GET /api/v1/bookmarks/search, as that person
  K-->>S: their bookmarks
  S-->>C: results, each with a link into Karakeep and guidance for the next step
```

<div class="grid cards" markdown>

- **[30 tools](tools.md)**: bookmarks, lists, tags, highlights and asset links, named as in Karakeep's own MCP server.
- **[Each person as themselves](security.md)**: the login is the person's own Karakeep key; the server holds no key of its own.
- **[Not Karakeep's own MCP server](adr/0001-own-server-instead-of-upstreams-stdio-one.md)**: that one speaks only stdio and acts as one user per process.

</div>
