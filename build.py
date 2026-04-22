#!/usr/bin/env python3
"""
Build script for Killed by AI.
Reads graveyard.json and generates index.html with:
- Pre-rendered cards in the initial HTML (for SEO indexability)
- Inline JSON data (for JS-based search/filter/sort)
- JSON-LD structured data
"""
import json
import html
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SITE_URL = "https://mixtpatrik.github.io/killedbyai/"


def days_between(a, b):
    d1 = datetime.strptime(a, "%Y-%m-%d")
    d2 = datetime.strptime(b, "%Y-%m-%d")
    return max(0, (d2 - d1).days)


def format_lifespan(days):
    years = days // 365
    months = (days % 365) // 30
    d = days % 30
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    if months and d:
        return f"{months}m {d}d"
    if months:
        return f"{months}m"
    return f"{d}d"


def year(date_str):
    return date_str.split("-")[0]


def esc(s):
    return html.escape(s or "", quote=True)


def render_card(item):
    days = days_between(item["dateOpen"], item["dateClose"])
    lifespan = format_lifespan(days)
    y_open = year(item["dateOpen"])
    y_close = year(item["dateClose"])
    link_html = ""
    if item.get("link"):
        link_html = (
            f'<a class="card-link" href="{esc(item["link"])}" target="_blank" rel="noopener">'
            "Source"
            '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">'
            '<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/>'
            "</svg></a>"
        )
    return f'''<article class="card" data-type="{esc(item["type"])}" data-name="{esc(item["name"].lower())}" data-desc="{esc(item["description"].lower())}" data-killer="{esc(item["killedBy"].lower())}" data-cause="{esc(item["causeOfDeath"].lower())}" data-date-close="{esc(item["dateClose"])}" data-date-open="{esc(item["dateOpen"])}" data-days="{days}">
  <header class="card-header">
    <h2 class="card-name">{esc(item["name"])}</h2>
    <span class="card-lifespan">{y_open} — {y_close}</span>
  </header>
  <p class="card-description">{esc(item["description"])}</p>
  <footer class="card-footer">
    <div class="card-tags">
      <span class="tag">{esc(item["type"])}</span>
      <span class="tag">{esc(item["causeOfDeath"])}</span>
      <span class="tag tag-killer">Killed by: {esc(item["killedBy"])}</span>
    </div>
    <div class="card-age">{lifespan}</div>
  </footer>
  {link_html}
</article>'''


def build_jsonld(items):
    """Build an ItemList JSON-LD for structured data."""
    list_items = []
    for i, item in enumerate(items, 1):
        list_items.append({
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Thing",
                "name": item["name"],
                "description": item["description"],
                "url": item.get("link", SITE_URL),
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Type", "value": item["type"]},
                    {"@type": "PropertyValue", "name": "Launched", "value": item["dateOpen"]},
                    {"@type": "PropertyValue", "name": "Discontinued", "value": item["dateClose"]},
                    {"@type": "PropertyValue", "name": "Cause of Death", "value": item["causeOfDeath"]},
                    {"@type": "PropertyValue", "name": "Killed By", "value": item["killedBy"]},
                ],
            },
        })

    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": SITE_URL + "#website",
                "url": SITE_URL,
                "name": "Killed by AI",
                "description": "A digital cemetery for discontinued AI models, apps, startups, and hardware.",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate": SITE_URL + "?q={search_term_string}",
                    },
                    "query-input": "required name=search_term_string",
                },
            },
            {
                "@type": "Dataset",
                "name": "Killed by AI Graveyard",
                "description": "An open dataset of discontinued AI products, models, startups, and hardware, tracking casualties of the artificial intelligence gold rush.",
                "url": SITE_URL,
                "keywords": "AI graveyard, killed by AI, discontinued AI, deprecated AI models, AI shutdown, dead AI products",
                "license": "https://github.com/mixtpatrik/killedbyai",
                "creator": {"@type": "Person", "name": "Patrik Rojan"},
            },
            {
                "@type": "ItemList",
                "name": "Discontinued AI Products",
                "numberOfItems": len(items),
                "itemListElement": list_items,
            },
        ],
    }


def build_sitemap():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
'''


def build_robots():
    return f'''User-agent: *
Allow: /

Sitemap: {SITE_URL}sitemap.xml
'''


def main():
    data = json.loads((ROOT / "graveyard.json").read_text())
    template = (ROOT / "template.html").read_text()

    cards_html = "\n".join(render_card(item) for item in data)
    jsonld = json.dumps(build_jsonld(data), indent=2)
    data_json = json.dumps(data, separators=(",", ":"))

    output = (template
              .replace("{{CARDS}}", cards_html)
              .replace("{{JSONLD}}", jsonld)
              .replace("{{DATA_JSON}}", data_json)
              .replace("{{COUNT}}", str(len(data)))
              .replace("{{LAST_UPDATED}}", datetime.utcnow().strftime("%B %d, %Y")))

    (ROOT / "index.html").write_text(output)
    (ROOT / "sitemap.xml").write_text(build_sitemap())
    (ROOT / "robots.txt").write_text(build_robots())

    print(f"Built index.html with {len(data)} entries")
    print("Generated sitemap.xml and robots.txt")


if __name__ == "__main__":
    main()
