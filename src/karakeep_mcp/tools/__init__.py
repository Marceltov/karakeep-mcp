"""The tools, one module per area; each has `register(mcp, client)`."""

from . import assets, bookmarks, highlights, lists, tags

ALL = [bookmarks, lists, tags, highlights, assets]
