"""Merge newly scraped Foundry blog articles (raw JSON from the browser scrape)
into the persistent dataset at data/articles.json. Dedups by article id
(trailing numeric id in the URL), keeps the richest excerpt/tags seen so far,
and never deletes previously-seen articles even if they scroll off the
live page's default view.

Usage:
    python merge_articles.py <raw_scrape_json_path> <repo_root>
"""
import json
import sys
import os
from datetime import datetime, timezone


def normalize(raw_items):
    cleaned = []
    seen = set()
    for a in raw_items:
        href = a.get("href", "")
        if not href:
            continue
        url = "https://techcommunity.microsoft.com" + href if href.startswith("/") else href
        art_id = url.rstrip("/").split("/")[-1]
        if not art_id.isdigit():
            continue
        if art_id in seen:
            continue
        title = (a.get("title") or "").strip()
        if title.lower() == "read the blog":
            continue
        seen.add(art_id)

        tags = []
        for t in a.get("tags", []):
            t = t.strip()
            if t and t not in tags:
                tags.append(t)
        tags = tags[:8]

        excerpt = (a.get("excerpt") or "").replace("\n", " ").strip()
        if excerpt == title:
            excerpt = ""
        if len(excerpt) > 220:
            excerpt = excerpt[:217].rsplit(" ", 1)[0] + "..."

        cleaned.append({
            "id": art_id,
            "title": title,
            "url": url,
            "date": (a.get("date") or "").strip(),
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
            # Fill in anything missing on the stored copy with fresher data
            for key in ("title", "date", "readTime", "excerpt", "author"):
                if not cur.get(key) and a.get(key):
                    cur[key] = a[key]
            if len(a.get("tags", [])) > len(cur.get("tags", [])):
                cur["tags"] = a["tags"]
    return list(by_id.values()), added


def main():
    raw_path = sys.argv[1]
    repo_root = sys.argv[2]
    data_path = os.path.join(repo_root, "data", "articles.json")

    with open(raw_path, encoding="utf-8") as f:
        raw_items = json.load(f)
    new_articles = normalize(raw_items)

    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    merged, added = merge(existing, new_articles)
    merged.sort(key=lambda a: a["date"], reverse=False)

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
        "totalArticles": len(merged),
        "newArticles": added,
    })
    meta["runHistory"] = history[-90:]  # keep last ~90 runs
    meta["lastRun"] = history[-1]["ranAt"]
    meta["totalArticles"] = len(merged)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"merged: total={len(merged)} added={added}")


if __name__ == "__main__":
    main()
