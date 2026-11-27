---
status: accepted
date: 2026-11-27
decision-makers: Marcel Bruckner
---

# Our own server, not upstream's stdio one

## Context and Problem Statement

A household runs one Karakeep with an account per person and wants Claude (claude.ai, the Claude apps, Claude Code) to use it, each person with their own bookmarks. claude.ai reaches an MCP server only over HTTP, with an OAuth login.

Karakeep ships an MCP server (`ghcr.io/karakeep-app/karakeep-mcp`, `apps/mcp` in karakeep-app/karakeep). It speaks only stdio (`serveStdio(createMcpServer)`) and builds one Karakeep client at start-up from `KARAKEEP_API_KEY`, so one process is one Karakeep user, and nothing on a request can change that.

## Considered Options

1. Upstream's server behind an HTTP bridge with one fixed key and a login in front.
2. Upstream's server behind a bridge that starts one process per session, with that session's key.
3. Our own FastMCP server on Karakeep's REST API, with mcp-login-oauth as the login.

## Decision Outcome

Option 3. Each login's grant is the person's Karakeep API key (pasted, or created by Karakeep's `apiKeys.exchange` from email and password); every tool calls `/api/v1` with it. The tools keep upstream's names.

Option 1 lets everyone who can sign in act as the one key's owner. Option 2 needs a bridge of our own that spawns and reaps a Node process per session; that is our own code too, without being able to add `guidance` and links to the results, and a process per person costs more memory than one Python server.

### Consequences

- Good: each person sees only their own bookmarks, and Karakeep, not this server, decides that.
- Good: every result can carry `guidance` and links into the web app, which a wrapped stdio server can't.
- Good: one small process for every user (about 77 MiB idle).
- Bad: the tools follow Karakeep's API by hand. A new endpoint or a changed shape reaches Claude only when this server changes; upstream's server gets it with Karakeep's release.
- Bad: the email-and-password login depends on `apiKeys.exchange`, a tRPC endpoint that is not part of Karakeep's documented REST API and may change with any release.
