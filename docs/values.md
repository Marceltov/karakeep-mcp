# What karakeep-mcp stands for

karakeep-mcp lets Claude use a person's Karakeep. This page says what it will stay, and it is the yardstick for every change: a review names the point it touches ("this breaks V1").

## Lines never crossed

### V1. Each person as themselves

Every call runs with the signed-in person's own Karakeep key. The server never holds a key of its own, never shares one between people, and never decides itself who may see what: Karakeep does.

**Rules out:** a service key in the server's configuration; a cache or index shared across logins; falling back to another key when a person's key fails.

**ADRs:** [0001](adr/0001-own-server-instead-of-upstreams-stdio-one.md)

### V2. Nothing usable at rest, nothing in the logs

Keys are stored encrypted, passwords never. A key, a password or a person's bookmarks never reach a log.

**Rules out:** logging a form, a key or a tool result; storing the password for a later exchange.

## What you can rely on

### V3. Results that tell Claude what to do next

Every tool result carries `guidance` and a link into Karakeep for each bookmark, list and tag, so Claude can hand the person the page and knows how to go on (the next page, the rest of a long text, that a link was already saved).

**Rules out:** a tool that returns Karakeep's raw answer without guidance; a result that names a bookmark without its link.

### V4. Karakeep's own names and behaviour

Tool names follow Karakeep's own MCP server, and what a tool does is what Karakeep's API does: no hidden extra writes, no second store of bookmarks.

**Rules out:** renaming tools for taste; a tool that changes more than its name says.
