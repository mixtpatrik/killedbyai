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
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SITE_URL = "https://killedbyai.net/"


def slugify(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


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
    collateral_html = ""
    if item.get("collateral"):
        collateral_html = f'<div class="card-collateral"><span class="collateral-icon">⚠️</span> {esc(item["collateral"])}</div>'
    slug = slugify(item["name"])
    death_type = item.get("deathType", "product-killed")
    return f'''<article class="card" id="{slug}" data-type="{esc(item["type"])}" data-death-type="{death_type}" data-name="{esc(item["name"].lower())}" data-desc="{esc(item["description"].lower())}" data-killer="{esc(item["killedBy"].lower())}" data-cause="{esc(item["causeOfDeath"].lower())}" data-date-close="{esc(item["dateClose"])}" data-date-open="{esc(item["dateOpen"])}" data-days="{days}">
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
  {collateral_html}
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
                "url": SITE_URL + "#" + slugify(item["name"]),
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


def build_faq(items):
    from collections import Counter

    total = len(items)
    killers = Counter(i["killedBy"] for i in items)
    top_killer, top_count = killers.most_common(1)[0]
    types = Counter(i["type"] for i in items)
    shortest = min(items, key=lambda i: days_between(i["dateOpen"], i["dateClose"]))
    shortest_days = days_between(shortest["dateOpen"], shortest["dateClose"])

    recent_5 = sorted(items, key=lambda i: i["dateClose"], reverse=True)[:5]
    recent_list = ", ".join(i["name"] for i in recent_5)

    sora = next((i for i in items if "Sora" in i["name"] and i["type"] == "app"), None)
    sora_answer = sora["description"] if sora else "OpenAI shut down Sora in April 2026 due to unsustainable compute costs."

    faqs = [
        {
            "q": "What is Killed by AI?",
            "a": f"Killed by AI is an open-source tracker of discontinued AI products, models, startups, and hardware. It currently documents {total} casualties of the artificial intelligence industry, from deprecated API models to billion-dollar startup failures."
        },
        {
            "q": "Why did OpenAI shut down Sora?",
            "a": sora_answer
        },
        {
            "q": "Which company has killed the most AI products?",
            "a": f"{top_killer} leads with {top_count} discontinued products, followed by {killers.most_common(2)[1][0]} with {killers.most_common(2)[1][1]}."
        },
        {
            "q": "What was the shortest-lived AI product?",
            "a": f"{shortest['name']} lasted just {format_lifespan(shortest_days)}. {shortest['description']}"
        },
        {
            "q": "What AI products were most recently discontinued?",
            "a": f"The most recent casualties include: {recent_list}."
        },
        {
            "q": "How many AI products have been shut down?",
            "a": f"We track {total} discontinued AI products across {types.get('model', 0)} deprecated models, {types.get('app', 0)} killed apps, {types.get('service', 0)} ended services, {types.get('startup', 0)} failed startups, and {types.get('hardware', 0)} dead hardware products."
        },
        {
            "q": "What was the OpenAI AI Text Classifier and why was it discontinued?",
            "a": "OpenAI's AI Text Classifier was a tool launched in January 2023 to detect AI-generated text. It was pulled in July 2023 after just 6 months because it could only correctly identify 26% of AI-written text while falsely flagging 9% of human writing."
        },
    ]

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f["a"],
                },
            }
            for f in faqs
        ],
    }

    faq_html_items = "\n".join(
        f'''<details class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
  <summary itemprop="name">{esc(f["q"])}</summary>
  <div class="faq-answer" itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
    <p itemprop="text">{esc(f["a"])}</p>
  </div>
</details>'''
        for f in faqs
    )

    return faq_schema, faq_html_items


def build_rss(items):
    """Build an RSS 2.0 feed sorted by most recently killed."""
    sorted_items = sorted(items, key=lambda i: i["dateClose"], reverse=True)[:30]
    today = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    rss_items = []
    for item in sorted_items:
        slug = slugify(item["name"])
        pub_date = datetime.strptime(item["dateClose"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y 00:00:00 +0000"
        )
        rss_items.append(
            f"""    <item>
      <title>{esc(item["name"])} — Killed by {esc(item["killedBy"])}</title>
      <link>{SITE_URL}#{slug}</link>
      <guid isPermaLink="true">{SITE_URL}#{slug}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{esc(item["description"])}</description>
      <category>{esc(item["type"])}</category>
    </item>"""
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Killed by AI — The AI Graveyard</title>
    <link>{SITE_URL}</link>
    <description>A digital cemetery for discontinued AI models, apps, startups, and hardware.</description>
    <language>en-us</language>
    <lastBuildDate>{today}</lastBuildDate>
    <atom:link href="{SITE_URL}feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(rss_items)}
  </channel>
</rss>
'''


def build_killer_leaderboard(items):
    from collections import Counter
    killers = Counter(i["killedBy"] for i in items)
    top10 = killers.most_common(10)
    max_count = top10[0][1] if top10 else 1
    rows = []
    for killer, count in top10:
        pct = count / max_count * 100
        rows.append(
            f'<button class="lb-row" data-killer="{esc(killer.lower())}">'
            f'<span class="lb-name">{esc(killer)}</span>'
            f'<span class="lb-bar-wrap"><span class="lb-bar" style="width:{pct}%"></span></span>'
            f'<span class="lb-count">{count}</span>'
            f'</button>'
        )
    return "\n".join(rows)


def build_pace(items):
    from collections import Counter
    years = Counter(int(year(i["dateClose"])) for i in items)
    current_year = datetime.utcnow().year
    kills_this_year = years.get(current_year, 0)
    month_now = datetime.utcnow().month
    pace_per_month = round(kills_this_year / max(month_now, 1), 1)
    projected = round(pace_per_month * 12)
    return kills_this_year, pace_per_month, projected


def build_stats(items):
    """Compute summary statistics for the stats ribbon."""
    from collections import Counter
    total = len(items)
    lifespans = [days_between(i["dateOpen"], i["dateClose"]) for i in items]
    avg_lifespan = sum(lifespans) // total if total else 0

    killers = Counter(i["killedBy"] for i in items)
    top_killer, top_killer_count = killers.most_common(1)[0]

    shortest = min(items, key=lambda i: days_between(i["dateOpen"], i["dateClose"]))
    shortest_days = days_between(shortest["dateOpen"], shortest["dateClose"])

    return {
        "avg_lifespan": format_lifespan(avg_lifespan),
        "top_killer": top_killer,
        "top_killer_count": top_killer_count,
        "shortest_name": shortest["name"],
        "shortest_days": format_lifespan(shortest_days),
    }


def build_timeline(items):
    """Render a bar chart of kills per year (last 5 years only)."""
    from collections import Counter
    current_year = datetime.utcnow().year
    years = Counter(int(year(item["dateClose"])) for item in items)
    min_y = current_year - 4
    max_y = current_year
    max_count = max(years.get(y, 0) for y in range(min_y, max_y + 1))

    bars = []
    for y in range(min_y, max_y + 1):
        count = years.get(y, 0)
        height_pct = (count / max_count * 100) if max_count else 0
        bars.append(
            f'<button class="bar" data-year="{y}" aria-label="{count} killed in {y}" '
            f'style="--bar-height: {height_pct}%;">'
            f'<span class="bar-count">{count}</span>'
            f'<span class="bar-fill"></span>'
            f'<span class="bar-label">{str(y)[-2:]}</span>'
            f'</button>'
        )
    return "\n".join(bars), min_y, max_y, max_count


VALID_DEATH_TYPES = {
    "model-upgrade", "product-killed", "startup-failed",
    "acqui-hired", "feature-removed", "hardware-failed",
}
VALID_TYPES = {"app", "model", "service", "startup", "hardware"}
GRAVEYARD_REQUIRED = (
    "name", "dateOpen", "dateClose", "description",
    "type", "causeOfDeath", "killedBy", "link",
)


def validate(data, ldata, cs_data):
    """Data hygiene checks. Returns a list of human-readable warnings.

    These encode the failure modes that have actually bitten this project:
    entries buried in the graveyard before they died, coming-soon items that
    quietly expired, and duplicate rows silently inflating the totals.
    """
    today = datetime.utcnow().strftime("%Y-%m-%d")
    warnings = []

    seen = set()
    for item in data:
        name = item.get("name", "<unnamed>")
        if name in seen:
            warnings.append(f"graveyard: duplicate entry '{name}'")
        seen.add(name)

        for field in GRAVEYARD_REQUIRED:
            if not item.get(field):
                warnings.append(f"graveyard: '{name}' missing required field '{field}'")

        if item.get("dateClose", "") > today:
            warnings.append(
                f"graveyard: '{name}' dies {item['dateClose']} (future) — "
                f"it belongs in coming-soon.json until then"
            )
        if item.get("dateOpen") and item.get("dateClose") and item["dateClose"] <= item["dateOpen"]:
            warnings.append(
                f"graveyard: '{name}' closes {item['dateClose']} on/before it opened {item['dateOpen']}"
            )
        if item.get("deathType") not in VALID_DEATH_TYPES:
            warnings.append(f"graveyard: '{name}' has invalid deathType '{item.get('deathType')}'")
        if item.get("type") not in VALID_TYPES:
            warnings.append(f"graveyard: '{name}' has invalid type '{item.get('type')}'")

    graveyard_names = {i.get("name", "").lower() for i in data}
    for item in cs_data:
        name = item.get("name", "<unnamed>")
        if item.get("dateShutdown", "") < today:
            warnings.append(
                f"coming-soon: '{name}' died {item['dateShutdown']} — move it to graveyard.json"
            )
        if name.lower() in graveyard_names:
            warnings.append(f"coming-soon: '{name}' is already in the graveyard — remove one")

    layoff_keys = set()
    for item in ldata:
        key = (item.get("company"), item.get("date"))
        if key in layoff_keys:
            warnings.append(
                f"layoffs: duplicate '{item.get('company')}' on {item.get('date')} — inflates the job total"
            )
        layoff_keys.add(key)

    return warnings


def main():
    data = json.loads((ROOT / "graveyard.json").read_text())
    template = (ROOT / "template.html").read_text()

    cards_html = "\n".join(render_card(item) for item in data)
    jsonld = json.dumps(build_jsonld(data), indent=2)
    timeline_html, min_year, max_year, max_count = build_timeline(data)
    stats = build_stats(data)
    faq_schema, faq_html = build_faq(data)
    leaderboard_html = build_killer_leaderboard(data)
    kills_ytd, pace_per_month, projected_eoy = build_pace(data)

    type_counts = {}
    for item in data:
        type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1

    output = (template
              .replace("{{CARDS}}", cards_html)
              .replace("{{JSONLD}}", jsonld)
              .replace("{{FAQ_JSONLD}}", json.dumps(faq_schema, indent=2))
              .replace("{{FAQ_HTML}}", faq_html)
              .replace("{{COUNT}}", str(len(data)))
              .replace("{{TIMELINE}}", timeline_html)
              .replace("{{YEAR_RANGE}}", f"{min_year}–{max_year}")
              .replace("{{MAX_COUNT}}", str(max_count))
              .replace("{{AVG_LIFESPAN}}", stats["avg_lifespan"])
              .replace("{{TOP_KILLER}}", esc(stats["top_killer"]))
              .replace("{{TOP_KILLER_COUNT}}", str(stats["top_killer_count"]))
              .replace("{{SHORTEST_NAME}}", esc(stats["shortest_name"]))
              .replace("{{SHORTEST_DAYS}}", stats["shortest_days"])
              .replace("{{COUNT_APP}}", str(type_counts.get("app", 0)))
              .replace("{{COUNT_MODEL}}", str(type_counts.get("model", 0)))
              .replace("{{COUNT_SERVICE}}", str(type_counts.get("service", 0)))
              .replace("{{COUNT_STARTUP}}", str(type_counts.get("startup", 0)))
              .replace("{{COUNT_HARDWARE}}", str(type_counts.get("hardware", 0)))
              .replace("{{LEADERBOARD}}", leaderboard_html)
              .replace("{{KILLS_YTD}}", str(kills_ytd))
              .replace("{{PACE_PER_MONTH}}", str(pace_per_month))
              .replace("{{PROJECTED_EOY}}", str(projected_eoy))
              .replace("{{CURRENT_YEAR}}", str(datetime.utcnow().year))
              .replace("{{FUNDING_B}}", f"{sum(d.get('fundingM', 0) for d in data) / 1000:.1f}")
              .replace("{{LAST_UPDATED}}", datetime.utcnow().strftime("%B %d, %Y")))

    # Inject layoffs stats into main page
    layoffs_path_check = ROOT / "layoffs.json"
    if layoffs_path_check.exists():
        ldata = json.loads(layoffs_path_check.read_text())
        total_jobs_lost = sum(l["jobs"] for l in ldata)
        output = (output
                  .replace("{{TOTAL_JOBS_LOST}}", f"{total_jobs_lost:,}")
                  .replace("{{TOTAL_COMPANIES_LAYOFFS}}", str(len(ldata))))
    else:
        output = output.replace("{{TOTAL_JOBS_LOST}}", "0").replace("{{TOTAL_COMPANIES_LAYOFFS}}", "0")

    (ROOT / "index.html").write_text(output)
    (ROOT / "sitemap.xml").write_text(build_sitemap())
    (ROOT / "robots.txt").write_text(build_robots())
    (ROOT / "feed.xml").write_text(build_rss(data))

    # Build Employee Graveyard
    layoffs_path = ROOT / "layoffs.json"
    if layoffs_path.exists():
        layoffs = json.loads(layoffs_path.read_text())
        layoffs_template = (ROOT / "layoffs-template.html").read_text()
        total_jobs = sum(l["jobs"] for l in layoffs)
        total_companies = len(layoffs)
        layoffs_sorted = sorted(layoffs, key=lambda l: l["jobs"], reverse=True)
        max_jobs = layoffs_sorted[0]["jobs"] if layoffs_sorted else 1

        rows_html = "\n".join(
            f'''<article class="layoff-row">
  <div class="layoff-bar-wrap">
    <div class="layoff-bar" style="width: {l["jobs"] / max_jobs * 100}%"></div>
  </div>
  <div class="layoff-info">
    <div class="layoff-header">
      <h2 class="layoff-company">{esc(l["company"])}</h2>
      <span class="layoff-count">{l["jobs"]:,}</span>
    </div>
    <p class="layoff-desc">{esc(l["description"])}</p>
    <div class="layoff-meta">
      <span class="layoff-roles">{esc(l["roles"])}</span>
      <span class="layoff-date">{l["date"][:7]}</span>
      <a class="layoff-source" href="{esc(l["source"])}" target="_blank" rel="noopener">Source</a>
    </div>
  </div>
</article>'''
            for l in layoffs_sorted
        )

        by_year = {}
        for l in layoffs:
            y = l["date"][:4]
            by_year[y] = by_year.get(y, 0) + l["jobs"]
        year_stats = " | ".join(f"{y}: {c:,}" for y, c in sorted(by_year.items()))

        layoffs_out = (layoffs_template
                       .replace("{{ROWS}}", rows_html)
                       .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
                       .replace("{{TOTAL_COMPANIES}}", str(total_companies))
                       .replace("{{YEAR_STATS}}", year_stats)
                       .replace("{{LAST_UPDATED}}", datetime.utcnow().strftime("%B %d, %Y")))
        (ROOT / "layoffs.html").write_text(layoffs_out)
        print(f"Built layoffs.html with {total_companies} companies, {total_jobs:,} jobs")

    # Build Funding Burned page
    funded = sorted(
        [i for i in data if i.get("fundingM")],
        key=lambda i: i["fundingM"],
        reverse=True,
    )
    if funded:
        fund_template = (ROOT / "funding-template.html").read_text()
        total_m = sum(i["fundingM"] for i in funded)
        total_b = f"{total_m / 1000:.1f}"
        max_fund = funded[0]["fundingM"]

        fund_rows = "\n".join(
            f'''<article class="fund-row">
  <div class="fund-bar-wrap"><div class="fund-bar" style="width:{i["fundingM"]/max_fund*100}%"></div></div>
  <div class="fund-info">
    <div class="fund-header">
      <h2 class="fund-name">{esc(i["name"])}</h2>
      <span class="fund-amount">${i["fundingM"]:,.0f}M</span>
    </div>
    <p class="fund-desc">{esc(i["description"])}</p>
    <div class="fund-meta">
      <span class="fund-type">{esc(i["type"])}</span>
      <span class="fund-dates">{i["dateOpen"][:4]}–{i["dateClose"][:4]}</span>
      {f'<a class="fund-source" href="{esc(i["link"])}" target="_blank" rel="noopener">Source</a>' if i.get("link") else ""}
    </div>
  </div>
</article>'''
            for i in funded
        )

        fund_out = (fund_template
                    .replace("{{ROWS}}", fund_rows)
                    .replace("{{TOTAL_B}}", total_b)
                    .replace("{{COUNT}}", str(len(funded)))
                    .replace("{{LAST_UPDATED}}", datetime.utcnow().strftime("%B %d, %Y")))
        (ROOT / "funding.html").write_text(fund_out)
        print(f"Built funding.html: ${total_b}B across {len(funded)} startups")

    # Build Coming Soon page
    cs_path = ROOT / "coming-soon.json"
    if cs_path.exists():
        cs_data = json.loads(cs_path.read_text())
        cs_template = (ROOT / "coming-soon-template.html").read_text()
        cs_sorted = sorted(cs_data, key=lambda i: i["dateShutdown"])
        now = datetime.utcnow()

        cs_rows = []
        for item in cs_sorted:
            shutdown = datetime.strptime(item["dateShutdown"], "%Y-%m-%d")
            days_left = (shutdown - now).days
            if days_left > 0:
                countdown = f"{days_left}d left"
                dead_class = ""
            else:
                countdown = "DEAD"
                dead_class = " dead"

            cs_rows.append(
                f'''<article class="doom-card">
  <div class="doom-header">
    <h2 class="doom-name">{esc(item["name"])}</h2>
    <span class="doom-countdown{dead_class}">{countdown}</span>
  </div>
  <p class="doom-desc">{esc(item["description"])}</p>
  <div class="doom-meta">
    <span class="doom-tag">Killed by: {esc(item["killedBy"])}</span>
    <span>Shutdown: {item["dateShutdown"]}</span>
    <span>Replacement: {esc(item["replacement"])}</span>
    <a class="doom-source" href="{esc(item["link"])}" target="_blank" rel="noopener">Source</a>
  </div>
</article>'''
            )

        cs_out = (cs_template
                  .replace("{{ROWS}}", "\n".join(cs_rows))
                  .replace("{{COUNT}}", str(len(cs_sorted))))
        (ROOT / "coming-soon.html").write_text(cs_out)
        print(f"Built coming-soon.html with {len(cs_sorted)} entries")

    # Build sitemap
    today = datetime.utcnow().strftime("%Y-%m-%d")
    pages = [
        (SITE_URL, "1.0"),
        (SITE_URL + "layoffs.html", "0.8"),
        (SITE_URL + "funding.html", "0.8"),
        (SITE_URL + "coming-soon.html", "0.8"),
        (SITE_URL + "api.html", "0.6"),
    ]
    sitemap_urls = "\n".join(
        f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>{prio}</priority>\n  </url>"
        for url, prio in pages
    )
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_urls}
</urlset>
'''
    (ROOT / "sitemap.xml").write_text(sitemap_xml)

    print(f"Built index.html with {len(data)} entries")
    print("Generated sitemap.xml, robots.txt, feed.xml")

    ldata_for_check = json.loads((ROOT / "layoffs.json").read_text()) if (ROOT / "layoffs.json").exists() else []
    cs_for_check = json.loads((ROOT / "coming-soon.json").read_text()) if (ROOT / "coming-soon.json").exists() else []
    warnings = validate(data, ldata_for_check, cs_for_check)
    if warnings:
        print(f"\n⚠️  {len(warnings)} data warning(s):")
        for w in warnings:
            print(f"   - {w}")
    else:
        print("✓ Data checks passed")


if __name__ == "__main__":
    main()
