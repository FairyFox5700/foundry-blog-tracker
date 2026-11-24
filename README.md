# Microsoft Foundry Blog Tracker

A daily-refreshed dashboard tracking posts from the
[Microsoft Foundry blog](https://techcommunity.microsoft.com/category/azure-ai-foundry) on Tech Community.

**Live site:** published via GitHub Pages from this repo's `main` branch (see repo settings).

## What it does

- Scrapes the Foundry blog board once a day and accumulates every article ever seen into `data/articles.json` (nothing is ever dropped, even once it scrolls off the live page).
- Regenerates `index.html`, a self-contained dashboard with:
  - A **posts-per-day trend chart** (Chart.js)
  - A **top-tags bar chart** (Chart.js)
  - A **tag map diagram** (Mermaid.js) showing how topics cluster
  - A searchable, sortable, filterable article list
  - Per-article **"Relevant to me"** and **"Read"** checkboxes, saved locally in your browser (`localStorage`)
- Commits and pushes the refreshed data + site automatically.

## Repo layout

```
data/
  articles.json   # accumulated dataset, source of truth
  meta.json       # run history / last-refreshed timestamp
scripts/
  merge_articles.py  # merges a fresh scrape into data/articles.json
  build.py           # regenerates index.html from data/articles.json
index.html        # generated dashboard (published via GitHub Pages)
```

## Regenerating locally

```bash
python scripts/merge_articles.py <raw_scrape.json> .
python scripts/build.py .
```

`raw_scrape.json` is the raw array of `{title, href, date, readTime, excerpt, tags, author}` objects captured from the blog board page.
