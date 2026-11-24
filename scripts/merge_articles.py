"""Merge newly scraped/fetched Foundry blog articles into the persistent
dataset at data/articles.json. Supports two sources:

  - "techcommunity": scraped via Playwright from the Tech Community blog board
    (raw items have relative hrefs like /blog/azure-ai-foundry-blog/.../<id>,
    and a display date like "Nov 18, 2026").
  - "devblog": fetched from the devblogs.microsoft.com/foundry RSS feed
    (raw items have absolute hrefs ending in a slug, and an RFC 822 pubDate).

Dedups by a source-qualified id, keeps the richest excerpt/tags seen so far,
and never deletes previously-seen articles even if they scroll off the
live page's default view or feed window.

Usage:
    python merge_articles.py <raw_json_path> <repo_root> <source>
    where <source> is "techcommunity" or "devblog"
"""
import json
import sys
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


def parse_date(raw, source):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        if source == "devblog":
            dt = parsedate_to_datetime(raw)
            return dt.replace(tzinfo=None)
        else:
            return datetime.strptime(raw, "%b %d, %Y")
    except Exception:
        return None


def normalize(raw_items, source):
    cleaned = []
    seen = set()
    base_url = "https://techcommunity.microsoft.com"
    for a in raw_items:
        href = (a.get("href") or "").strip()
        if not href:
            continue
        url = base_url + href if href.startswith("/") else href
        title = (a.get("title") or "").strip()
        if not title or title.lower() == "read the blog":
            continue

        if source == "techcommunity":
            slug = url.rstrip("/").split("/")[-1]
            if not slug.isdigit():
                continue
            art_id = f"tc-{slug}"
        else:
            slug = url.rstrip("/").split("/")[-1]
            if not slug:
                continue
            art_id = f"db-{slug}"

        if art_id in seen:
            continue
        seen.add(art_id)

        tags = []
        for t in a.get("tags", []):
            t = t.strip().lower()
            if t and t not in tags:
                tags.append(t)
        tags = tags[:8]

        excerpt = (a.get("excerpt") or "").replace("\n", " ").strip()
        if excerpt == title:
            excerpt = ""
        if len(excerpt) > 220:
            excerpt = excerpt[:217].rsplit(" ", 1)[0] + "..."

        dt = parse_date(a.get("date"), source)
        display_date = dt.strftime("%b %d, %Y") if dt else (a.get("date") or "").strip()
        date_iso = dt.strftime("%Y-%m-%d") if dt else ""

        cleaned.append({
            "id": art_id,
            "source": source,
            "title": title,
            "url": url,
            "date": display_date,
            "dateISO": date_iso,
            "readTime": (a.get("readTime") or "").strip(),
            "excerpt": excerpt,
            "tags": tags,
            "author": (a.get("author") or "").strip(),
        })
    return cleaned


def merge(existing, new):
    by_id = {a["id"]: a for a in existing}
    added = 0
    for a in new:
        if a["id"] not in by_id:
            added += 1
            by_id[a["id"]] = a
        else:
            cur = by_id[a["id"]]
            for key in ("title", "date", "dateISO", "readTime", "excerpt", "author", "source"):
                if not cur.get(key) and a.get(key):
                    cur[key] = a[key]
            if len(a.get("tags", [])) > len(cur.get("tags", [])):
                cur["tags"] = a["tags"]
    return list(by_id.values()), added


def main():
    raw_path = sys.argv[1]
    repo_root = sys.argv[2]
    source = sys.argv[3] if len(sys.argv) > 3 else "techcommunity"
    assert source in ("techcommunity", "devblog"), "source must be techcommunity or devblog"

    data_path = os.path.join(repo_root, "data", "articles.json")

    with open(raw_path, encoding="utf-8") as f:
        raw_items = json.load(f)
    new_articles = normalize(raw_items, source)

    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    merged, added = merge(existing, new_articles)
    merged.sort(key=lambda a: a.get("dateISO") or "0000-00-00")

    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    meta_path = os.path.join(repo_root, "data", "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    history = meta.get("runHistory", [])
    history.append({
        "ranAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "totalArticles": len(merged),
        "newArticles": added,
    })
    meta["runHistory"] = history[-180:]  # keep last ~180 runs across both sources
    meta["lastRun"] = history[-1]["ranAt"]
    meta["totalArticles"] = len(merged)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"merged ({source}): total={len(merged)} added={added}")


if __name__ == "__main__":
    main()
