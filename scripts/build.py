"""Generate index.html (the published tracker) from data/articles.json and
data/meta.json. Self-contained aside from CDN-hosted Chart.js and Mermaid.js
(this is published via GitHub Pages, not the OneDrive sandbox, so CDN use is fine).

Usage:
    python build.py <repo_root>
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone


def load(repo_root):
    with open(os.path.join(repo_root, "data", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    meta_path = os.path.join(repo_root, "data", "meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    return articles, meta


def parse_date(d):
    try:
        return datetime.strptime(d, "%b %d, %Y")
    except Exception:
        return None


def build_chart_data(articles):
    tag_counter = Counter()
    day_counter = Counter()
    author_counter = Counter()
    for a in articles:
        for t in a.get("tags", []):
            tag_counter[t] += 1
        dt = parse_date(a.get("date", ""))
        if dt:
            day_counter[dt.strftime("%Y-%m-%d")] += 1
        if a.get("author"):
            author_counter[a["author"]] += 1

    top_tags = tag_counter.most_common(12)
    days_sorted = sorted(day_counter.items(), key=lambda kv: kv[0])
    top_authors = author_counter.most_common(8)

    return {
        "tagLabels": [t for t, _ in top_tags],
        "tagCounts": [c for _, c in top_tags],
        "dayLabels": [d for d, _ in days_sorted],
        "dayCounts": [c for _, c in days_sorted],
        "authorLabels": [a for a, _ in top_authors],
        "authorCounts": [c for _, c in top_authors],
    }


def build_mermaid(articles):
    tag_counter = Counter()
    for a in articles:
        for t in a.get("tags", []):
            tag_counter[t] += 1
    top = tag_counter.most_common(10)

    def safe_id(s, i):
        return f"T{i}"

    lines = ["graph LR", '  ROOT["Microsoft Foundry Blog"]']
    for i, (tag, count) in enumerate(top):
        node_id = safe_id(tag, i)
        label = tag.replace('"', "'")
        lines.append(f'  ROOT --> {node_id}["{label} ({count})"]')
    return "\n".join(lines)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Microsoft Foundry Blog Tracker</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  window.__mermaid = mermaid;
</script>
<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("scoutTheme");
    const theme =
      param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>
<style>
:root {
  color-scheme: light;
  --cp-bg: #f7f4ef;
  --cp-bg-elevated: #fcfbf8;
  --cp-surface: #ffffff;
  --cp-surface-soft: #f5f5f5;
  --cp-border: #dedede;
  --cp-border-strong: #919191;
  --cp-text: #242424;
  --cp-text-muted: #5c5c5c;
  --cp-text-soft: #6f6f6f;
  --cp-accent: #b11f4b;
  --cp-accent-hover: #9a1a41;
  --cp-accent-soft: rgba(177, 31, 75, 0.08);
  --cp-accent-fg: #ffffff;
  --cp-success: #16a34a;
  --cp-danger: #dc2626;
  --cp-warning: #f59e0b;
  --cp-link: #0078d4;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.12);
  --cp-overlay: rgba(255, 255, 255, 0.8);
  --cp-panel: rgba(255, 255, 255, 0.86);
  --cp-panel-strong: rgba(255, 255, 255, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.55);
  --cp-highlight: rgba(177, 31, 75, 0.12);
}
html[data-theme="dark"] {
  color-scheme: dark;
  --cp-bg: #3d3b3a;
  --cp-bg-elevated: #343231;
  --cp-surface: #292929;
  --cp-surface-soft: #2e2e2e;
  --cp-border: #474747;
  --cp-border-strong: #5f5f5f;
  --cp-text: #dedede;
  --cp-text-muted: #919191;
  --cp-text-soft: #b0b0b0;
  --cp-accent: #fd8ea1;
  --cp-accent-hover: #fb7b91;
  --cp-accent-soft: rgba(253, 142, 161, 0.14);
  --cp-accent-fg: #1a1a1a;
  --cp-success: #4ade80;
  --cp-danger: #f87171;
  --cp-warning: #fbbf24;
  --cp-link: #4da6ff;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
  --cp-overlay: rgba(41, 41, 41, 0.88);
  --cp-panel: rgba(41, 41, 41, 0.72);
  --cp-panel-strong: rgba(41, 41, 41, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.04);
  --cp-highlight: rgba(253, 142, 161, 0.12);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--cp-bg);
  color: var(--cp-text);
  font-family: "Segoe UI", Aptos, Calibri, -apple-system, BlinkMacSystemFont, sans-serif;
}
.wrap { max-width: 1080px; margin: 0 auto; padding: 32px 20px 64px; }
header.page-header { margin-bottom: 20px; }
h1 { font-size: 1.6rem; margin: 0 0 6px; }
h2 { font-size: 1.15rem; margin: 0 0 12px; }
.subtitle { color: var(--cp-text-muted); font-size: 0.92rem; margin: 0 0 6px; }
.subtitle a { color: var(--cp-link); }
.run-meta { color: var(--cp-text-soft); font-size: 0.8rem; margin: 0 0 18px; }

.dash-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;
}
@media (max-width: 760px) { .dash-grid { grid-template-columns: 1fr; } }
.panel {
  background: var(--cp-surface); border: 1px solid var(--cp-border);
  border-radius: 16px; padding: 16px 18px;
  box-shadow: 0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14);
}
.panel.full { grid-column: 1 / -1; }
.panel canvas { max-height: 260px; }
.mermaid { background: var(--cp-surface-soft); border-radius: 10px; padding: 12px; overflow-x: auto; }

.toolbar {
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
  background: var(--cp-surface); border: 1px solid var(--cp-border);
  border-radius: 0.625rem; padding: 12px 14px; margin-bottom: 18px;
  box-shadow: 0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14);
}
.toolbar input[type="search"] {
  flex: 1 1 220px; padding: 8px 12px; border-radius: 0.625rem;
  border: 1px solid var(--cp-border); background: var(--cp-surface-soft);
  color: var(--cp-text); font-size: 0.92rem;
}
.toolbar select {
  padding: 8px 10px; border-radius: 0.625rem; border: 1px solid var(--cp-border);
  background: var(--cp-surface-soft); color: var(--cp-text); font-size: 0.9rem;
}
.toggle-btn {
  padding: 8px 14px; border-radius: 0.625rem; border: 1px solid var(--cp-border);
  background: var(--cp-surface-soft); color: var(--cp-text); font-size: 0.86rem;
  cursor: pointer; white-space: nowrap;
}
.toggle-btn.active {
  background: var(--cp-accent); color: var(--cp-accent-fg); border-color: var(--cp-accent);
}
.stats { color: var(--cp-text-muted); font-size: 0.85rem; margin: 0 0 14px; }

.card {
  background: var(--cp-surface); border: 1px solid var(--cp-border);
  border-radius: 16px; padding: 16px 18px; margin-bottom: 14px;
  box-shadow: 0 0 2px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.14);
  transition: border-color 0.15s ease;
}
.card.is-relevant { border-color: var(--cp-accent); }
.card.is-read { opacity: 0.6; }
.card-top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.card-title { font-size: 1.05rem; margin: 0 0 4px; line-height: 1.35; }
.card-title a { color: var(--cp-text); text-decoration: none; }
.card-title a:hover { color: var(--cp-accent); text-decoration: underline; }
.meta { color: var(--cp-text-muted); font-size: 0.82rem; margin-bottom: 8px; }
.excerpt { color: var(--cp-text-soft); font-size: 0.9rem; line-height: 1.5; margin: 0 0 10px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.tag {
  font-size: 0.74rem; padding: 2px 9px; border-radius: 999px;
  background: var(--cp-accent-soft); color: var(--cp-accent); border: 1px solid var(--cp-border);
  cursor: pointer; user-select: none;
}
.tag.tag-active { background: var(--cp-accent); color: var(--cp-accent-fg); }
.actions { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.action-label {
  display: flex; align-items: center; gap: 6px; font-size: 0.85rem;
  color: var(--cp-text-muted); cursor: pointer; user-select: none;
}
.action-label input { accent-color: var(--cp-accent); width: 15px; height: 15px; cursor: pointer; }
.open-link {
  margin-left: auto; font-size: 0.85rem; color: var(--cp-link); text-decoration: none;
}
.open-link:hover { text-decoration: underline; }
.empty-state {
  text-align: center; color: var(--cp-text-muted); padding: 40px 20px;
  border: 1px dashed var(--cp-border); border-radius: 16px;
}
footer { text-align: center; color: var(--cp-text-muted); font-size: 0.78rem; margin-top: 24px; }
</style>
</head>
<body>
<div class="wrap">
  <header class="page-header">
    <h1>Microsoft Foundry Blog Tracker</h1>
    <p class="subtitle">Daily snapshot of <a href="https://techcommunity.microsoft.com/category/azure-ai-foundry" target="_blank" rel="noopener">Microsoft Foundry @ Tech Community</a> &mdash; mark what's relevant and track what you've read. Your selections are saved locally in this browser.</p>
    <p class="run-meta" id="runMeta"></p>
  </header>

  <div class="dash-grid">
    <div class="panel">
      <h2>Posts per day</h2>
      <canvas id="trendChart"></canvas>
    </div>
    <div class="panel">
      <h2>Top tags</h2>
      <canvas id="tagChart"></canvas>
    </div>
    <div class="panel full">
      <h2>Top tag map</h2>
      <div class="mermaid" id="tagDiagram">__MERMAID_DIAGRAM__</div>
    </div>
  </div>

  <div class="toolbar">
    <input type="search" id="searchBox" placeholder="Search title, excerpt, or tag...">
    <select id="sortSelect">
      <option value="date-desc">Newest first</option>
      <option value="date-asc">Oldest first</option>
      <option value="title-asc">Title A-Z</option>
    </select>
    <button class="toggle-btn" id="relevantFilterBtn">★ Relevant only</button>
    <button class="toggle-btn" id="unreadFilterBtn">Unread only</button>
  </div>

  <p class="stats" id="statsLine"></p>

  <div id="cardList"></div>
  <div class="empty-state" id="emptyState" style="display:none;">No articles match your filters.</div>

  <footer>Refreshed automatically once a day via an unattended scrape + publish pipeline. Read/relevant marks persist per-browser via localStorage.</footer>
</div>

<script>
const ARTICLES = __ARTICLES_JSON__;
const META = __META_JSON__;
const CHART_DATA = __CHART_JSON__;
const STORAGE_KEY = "foundryBlogTrackerState";

document.getElementById("runMeta").textContent =
  `Last refreshed: ${META.lastRun ? new Date(META.lastRun).toLocaleString() : "unknown"} \u00b7 ${ARTICLES.length} articles tracked`;

function loadState() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
  catch (e) { return {}; }
}
function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}
let state = loadState();

let activeTag = null;
let showRelevantOnly = false;
let showUnreadOnly = false;

function getEntry(id) {
  return state[id] || { read: false, relevant: false };
}
function setEntry(id, patch) {
  state[id] = Object.assign(getEntry(id), patch);
  saveState(state);
}

function parseDate(d) {
  const t = Date.parse(d);
  return isNaN(t) ? 0 : t;
}

function render() {
  const search = document.getElementById("searchBox").value.trim().toLowerCase();
  const sortMode = document.getElementById("sortSelect").value;

  let items = ARTICLES.filter(a => {
    const entry = getEntry(a.id);
    if (showRelevantOnly && !entry.relevant) return false;
    if (showUnreadOnly && entry.read) return false;
    if (activeTag && !a.tags.includes(activeTag)) return false;
    if (search) {
      const hay = (a.title + " " + a.excerpt + " " + a.tags.join(" ")).toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  items.sort((a, b) => {
    if (sortMode === "date-desc") return parseDate(b.date) - parseDate(a.date);
    if (sortMode === "date-asc") return parseDate(a.date) - parseDate(b.date);
    if (sortMode === "title-asc") return a.title.localeCompare(b.title);
    return 0;
  });

  const list = document.getElementById("cardList");
  list.innerHTML = "";
  document.getElementById("emptyState").style.display = items.length ? "none" : "block";

  const total = ARTICLES.length;
  const relevantCount = ARTICLES.filter(a => getEntry(a.id).relevant).length;
  const readCount = ARTICLES.filter(a => getEntry(a.id).read).length;
  document.getElementById("statsLine").textContent =
    `${total} articles tracked \u00b7 ${relevantCount} marked relevant \u00b7 ${readCount} read \u00b7 showing ${items.length}`;

  items.forEach(a => {
    const entry = getEntry(a.id);
    const card = document.createElement("div");
    card.className = "card" + (entry.relevant ? " is-relevant" : "") + (entry.read ? " is-read" : "");

    const top = document.createElement("div");
    top.className = "card-top";
    const titleWrap = document.createElement("div");
    const h3 = document.createElement("h3");
    h3.className = "card-title";
    const link = document.createElement("a");
    link.href = a.url; link.target = "_blank"; link.rel = "noopener";
    link.textContent = a.title;
    h3.appendChild(link);
    titleWrap.appendChild(h3);

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = [a.date, a.readTime ? a.readTime + " min read" : "", a.author].filter(Boolean).join(" \u00b7 ");
    titleWrap.appendChild(meta);
    top.appendChild(titleWrap);
    card.appendChild(top);

    if (a.excerpt) {
      const p = document.createElement("p");
      p.className = "excerpt";
      p.textContent = a.excerpt;
      card.appendChild(p);
    }

    if (a.tags.length) {
      const tagsWrap = document.createElement("div");
      tagsWrap.className = "tags";
      a.tags.forEach(t => {
        const span = document.createElement("span");
        span.className = "tag" + (activeTag === t ? " tag-active" : "");
        span.textContent = t;
        span.addEventListener("click", () => {
          activeTag = activeTag === t ? null : t;
          render();
        });
        tagsWrap.appendChild(span);
      });
      card.appendChild(tagsWrap);
    }

    const actions = document.createElement("div");
    actions.className = "actions";

    const relevantLabel = document.createElement("label");
    relevantLabel.className = "action-label";
    const relevantCb = document.createElement("input");
    relevantCb.type = "checkbox";
    relevantCb.checked = !!entry.relevant;
    relevantCb.addEventListener("change", () => {
      setEntry(a.id, { relevant: relevantCb.checked });
      render();
    });
    relevantLabel.appendChild(relevantCb);
    relevantLabel.appendChild(document.createTextNode("★ Relevant to me"));
    actions.appendChild(relevantLabel);

    const readLabel = document.createElement("label");
    readLabel.className = "action-label";
    const readCb = document.createElement("input");
    readCb.type = "checkbox";
    readCb.checked = !!entry.read;
    readCb.addEventListener("change", () => {
      setEntry(a.id, { read: readCb.checked });
      render();
    });
    readLabel.appendChild(readCb);
    readLabel.appendChild(document.createTextNode("Read"));
    actions.appendChild(readLabel);

    const openLink = document.createElement("a");
    openLink.className = "open-link";
    openLink.href = a.url; openLink.target = "_blank"; openLink.rel = "noopener";
    openLink.textContent = "Open article \u2192";
    actions.appendChild(openLink);

    card.appendChild(actions);
    list.appendChild(card);
  });
}

document.getElementById("searchBox").addEventListener("input", render);
document.getElementById("sortSelect").addEventListener("change", render);
document.getElementById("relevantFilterBtn").addEventListener("click", (e) => {
  showRelevantOnly = !showRelevantOnly;
  e.target.classList.toggle("active", showRelevantOnly);
  render();
});
document.getElementById("unreadFilterBtn").addEventListener("click", (e) => {
  showUnreadOnly = !showUnreadOnly;
  e.target.classList.toggle("active", showUnreadOnly);
  render();
});

render();

function chartTextColor() {
  return getComputedStyle(document.documentElement).getPropertyValue('--cp-text').trim() || '#242424';
}
function chartGridColor() {
  return getComputedStyle(document.documentElement).getPropertyValue('--cp-border').trim() || '#dedede';
}
function chartAccent() {
  return getComputedStyle(document.documentElement).getPropertyValue('--cp-accent').trim() || '#b11f4b';
}

new Chart(document.getElementById('trendChart'), {
  type: 'bar',
  data: {
    labels: CHART_DATA.dayLabels,
    datasets: [{
      label: 'Posts published',
      data: CHART_DATA.dayCounts,
      backgroundColor: chartAccent(),
      borderRadius: 4,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: chartTextColor(), maxRotation: 60, minRotation: 45 }, grid: { color: chartGridColor() } },
      y: { beginAtZero: true, ticks: { color: chartTextColor(), precision: 0 }, grid: { color: chartGridColor() } }
    }
  }
});

new Chart(document.getElementById('tagChart'), {
  type: 'bar',
  data: {
    labels: CHART_DATA.tagLabels,
    datasets: [{
      label: 'Articles',
      data: CHART_DATA.tagCounts,
      backgroundColor: chartAccent(),
      borderRadius: 4,
    }]
  },
  options: {
    indexAxis: 'y',
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { beginAtZero: true, ticks: { color: chartTextColor(), precision: 0 }, grid: { color: chartGridColor() } },
      y: { ticks: { color: chartTextColor() }, grid: { display: false } }
    }
  }
});

window.addEventListener('load', () => {
  const mermaid = window.__mermaid;
  if (!mermaid) return;
  const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default';
  mermaid.initialize({ startOnLoad: true, theme });
});
</script>
</body>
</html>
"""


def main():
    repo_root = sys.argv[1]
    articles, meta = load(repo_root)
    chart_data = build_chart_data(articles)
    mermaid_src = build_mermaid(articles)

    html = HTML_TEMPLATE
    html = html.replace("__ARTICLES_JSON__", json.dumps(articles, ensure_ascii=False))
    html = html.replace("__META_JSON__", json.dumps(meta, ensure_ascii=False))
    html = html.replace("__CHART_JSON__", json.dumps(chart_data, ensure_ascii=False))
    html = html.replace("__MERMAID_DIAGRAM__", mermaid_src)

    out_path = os.path.join(repo_root, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", out_path, len(html), "bytes;", len(articles), "articles")


if __name__ == "__main__":
    main()
