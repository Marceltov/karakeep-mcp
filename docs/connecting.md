# Connect Claude

## claude.ai and the Claude apps

1. In claude.ai: **Settings → Connectors → Add custom connector**, URL `https://karakeep-mcp.example.com/mcp`.
2. **Connect** opens the login page. Either:
    - paste a **Karakeep API key** (in Karakeep: **Settings → API Keys → New API key**), or
    - open **No API key at hand?** and enter your Karakeep **email and password**. Karakeep then creates a key named `Claude` in your account, which you see and can revoke under API Keys.

    Accounts that sign in to Karakeep only through single sign-on (OIDC) have no password: use an API key.

3. Ask Claude something like "What did I save about sourdough?"

Each person connects with their own key and sees only their own bookmarks. Disconnecting the connector ends its access at once; a key that was created by the email-and-password login is deleted from Karakeep with it, a pasted key stays.

## Claude Code

Claude Code can use OAuth the same way, or send a key directly:

```bash
claude mcp add --transport http karakeep https://karakeep-mcp.example.com/mcp \
  --header "Authorization: Bearer YOUR_KARAKEEP_API_KEY"
```

The server checks the key against Karakeep on every request.
