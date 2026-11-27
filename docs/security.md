# Security

- **The server holds no Karakeep key of its own.** Every request runs with the key of the person who signed in; Karakeep decides what that key may see, so one person never sees another's bookmarks.
- **Keys at rest are encrypted** in the login store (mcp-login-oauth's Fernet store, keyed by `MCP_OAUTH_SECRET`). Claude only ever holds opaque OAuth tokens bound to this server.
- **The email-and-password login** sends both straight to Karakeep's `apiKeys.exchange`, the endpoint Karakeep's browser extension uses. Neither is stored or logged; only the key Karakeep returns is kept. Karakeep limits it to 10 attempts in 15 minutes, and mcp-login-oauth slows down guessing on the login page as well.
- **Disconnecting** a connector revokes its OAuth tokens at once, and deletes the `Claude` key the email-and-password login created. A pasted key is never deleted by this server.
- **A key revoked in Karakeep** stops working on the next call; Claude is told to reconnect.
- **TLS** to Karakeep is checked against the operating system's trust store (truststore).

Reporting a vulnerability: [`SECURITY.md`](https://github.com/Marceltov/karakeep-mcp/blob/main/SECURITY.md).
