"""Links into Karakeep's web app, the result every tool returns, and the trimmed shapes of Karakeep's objects."""

from pydantic import BaseModel, ConfigDict

from .config import Settings


class Result(BaseModel):
    """Every tool's result: its data, plus `guidance`, what Claude should do next given what this call did."""

    model_config = ConfigDict(extra="allow")
    guidance: list[str]


class Links:
    def __init__(self, settings: Settings):
        self.base = settings.public_url

    def bookmark(self, id: str) -> str:
        return f"{self.base}/dashboard/preview/{id}"

    def list(self, id: str) -> str:
        return f"{self.base}/dashboard/lists/{id}"

    def tag(self, id: str) -> str:
        return f"{self.base}/dashboard/tags/{id}"


def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def slim_bookmark(b: dict, links: Links) -> dict:
    content = b.get("content") or {}
    kind = content.get("type")
    return _drop_none(
        {
            "id": b["id"],
            "url": links.bookmark(b["id"]),
            "type": kind,
            "title": b.get("title") or content.get("title") or content.get("fileName"),
            "link": content.get("url") if kind == "link" else content.get("sourceUrl"),
            "description": content.get("description"),
            "text": content.get("text") if kind == "text" else None,
            "note": b.get("note"),
            "summary": b.get("summary"),
            "createdAt": b.get("createdAt"),
            "archived": b.get("archived"),
            "favourited": b.get("favourited"),
            "tags": [{"id": t["id"], "name": t["name"]} for t in b.get("tags") or []],
        }
    )


def slim_list(item: dict, links: Links) -> dict:
    keys = ("id", "name", "description", "icon", "parentId", "type", "query")
    return _drop_none({**{k: item.get(k) for k in keys}, "url": links.list(item["id"])})


def slim_tag(tag: dict, links: Links) -> dict:
    keys = ("id", "name", "numBookmarks", "numBookmarksByAttachedType")
    return _drop_none({**{k: tag.get(k) for k in keys}, "url": links.tag(tag["id"])})


def slim_highlight(h: dict, links: Links) -> dict:
    keys = ("id", "bookmarkId", "text", "note", "color", "startOffset", "endOffset", "createdAt")
    return _drop_none({**{k: h.get(k) for k in keys}, "url": links.bookmark(h["bookmarkId"])})


def page_guidance(count: int, next_cursor: str | None, noun: str) -> list[str]:
    if next_cursor:
        return [f"{count} {noun} on this page; there are more: call again with nextCursor as cursor."]
    return [f"{count} {noun}; that is all."]
