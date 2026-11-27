# Tools

Thirty tools, named as in [Karakeep's own MCP server](https://docs.karakeep.com/integrations/mcp/), so prompts written for it carry over. Each acts as the signed-in person. Every result carries `guidance`, a short list of what to do next given what the call did, and a `url` into Karakeep's web app for each bookmark, list and tag it names. Tools that delete are marked destructive, so clients ask before calling them.

## Bookmarks

| Tool | What it does |
|---|---|
| `search-bookmarks` | Full-text search with Karakeep's qualifiers (`#tag`, `list:`, `is:fav`, `after:`…), paged |
| `get-bookmark` | Title, link, note, AI summary, tags |
| `get-bookmark-content` | The saved page as Markdown, in chunks |
| `create-bookmark` | Save a link or a text note; an existing link is returned, not duplicated |
| `update-bookmark` | Title, note, summary, archived, favourite |
| `delete-bookmark` | Delete for good (Karakeep has no trash) |
| `check-url` | Is this link saved already? |
| `get-bookmark-lists` | The lists a bookmark is in |

## Lists

| Tool | What it does |
|---|---|
| `get-lists` | All lists |
| `get-list` | One list |
| `get-list-bookmarks` | The bookmarks in a list, paged |
| `create-list` | A new manual list, optionally nested |
| `update-list` | Rename, icon, description, move |
| `delete-list` | Delete a list; its bookmarks stay |
| `add-bookmark-to-list` | Put a bookmark into a list |
| `remove-bookmark-from-list` | Take it out again |

## Tags

| Tool | What it does |
|---|---|
| `get-tags` | All tags with counts, filterable, paged |
| `get-tag` | One tag |
| `get-tag-bookmarks` | The bookmarks with a tag, paged |
| `update-tag` | Rename a tag everywhere |
| `delete-tag` | Delete a tag; its bookmarks stay |
| `attach-tag-to-bookmark` | Tag a bookmark (new names become tags) |
| `detach-tag-from-bookmark` | Untag a bookmark |

## Highlights

| Tool | What it does |
|---|---|
| `list-highlights` | All highlights, paged |
| `get-bookmark-highlights` | The highlights in one bookmark |
| `get-highlight` | One highlight |
| `create-highlight` | Mark a passage |
| `update-highlight` | Colour or note |
| `delete-highlight` | Delete a highlight |

## Assets

| Tool | What it does |
|---|---|
| `get-asset` | A temporary download link for a bookmark's file |

## Left out

- **Admin endpoints** (users, recrawl, reindex): an assistant acting for one person has no business there.
- **Backups and feeds**: rare, and done better in Karakeep itself.
- **Uploading files**: claude.ai's connectors pass no files to a server.
- **Summarize**: it starts AI inference on Karakeep's side, which may cost money; Karakeep already summarises new bookmarks itself.
