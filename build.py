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
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
SITE_URL = "https://killedbyai.net/"
DATA_LICENSE = "https://creativecommons.org/licenses/by/4.0/"


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


TYPE_LABEL = {"app": "App", "model": "Model", "service": "Service", "startup": "Startup", "hardware": "Hardware"}
DEATH_LABEL = {"model-upgrade": "Model deprecation", "product-killed": "Product killed", "startup-failed": "Startup failed",
               "acqui-hired": "Acqui-hired", "feature-removed": "Feature removed", "hardware-failed": "Hardware discontinued"}
NEW_DAYS = 14


def fmt_date(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%B %-d, %Y")


def fmt_month(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%b %Y")


def is_new(item):
    added = item.get("dateAdded")
    return bool(added) and (datetime.utcnow() - datetime.strptime(added, "%Y-%m-%d")).days <= NEW_DAYS


def product_url(item):
    return f"{SITE_URL}dead/{item.get('slug') or slugify(item['name'])}/"


def _git(*args, timeout=30):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def git_dirty(paths):
    return bool(_git("status", "--porcelain", "--", *paths).strip())


_ENTRY_MOD = None


def entry_lastmod_map():
    """Real last-modified date per graveyard entry: newest commit in which that entry's dict changed.
    (git log -S only sees add/remove, so it missed every in-place edit.)"""
    global _ENTRY_MOD
    if _ENTRY_MOD is not None:
        return _ENTRY_MOD
    today = datetime.utcnow().strftime("%Y-%m-%d")
    snaps = []
    for line in _git("log", "--format=%H %cs", "--", "graveyard.json").splitlines():
        sha, date = line.split()
        try:
            snaps.append((date, {e["name"]: e for e in json.loads(_git("show", f"{sha}:graveyard.json"))}))
        except Exception:
            continue
    out = {}
    try:
        work = {e["name"]: e for e in json.loads((ROOT / "graveyard.json").read_text())}
    except Exception:
        work = {}
    for name, cur in work.items():
        if not snaps or snaps[0][1].get(name) != cur:
            out[name] = today          # changed in the working tree (or no history)
            continue
        mod = snaps[0][0]
        for j in range(len(snaps)):
            mod = snaps[j][0]
            if j + 1 >= len(snaps):
                break
            prev = snaps[j + 1][1].get(name)
            if prev is None or prev != cur:
                break
        out[name] = mod
    _ENTRY_MOD = out
    return out


def lm(paths):
    """Content last-modified for a page: today if its inputs are dirty, else their last commit date."""
    if git_dirty(paths):
        return datetime.utcnow().strftime("%Y-%m-%d")
    out = _git("log", "-1", "--format=%cs", "--", *paths).strip()
    return out or datetime.utcnow().strftime("%Y-%m-%d")


PERSON_ID = SITE_URL + "about/#patrik-rojan"
# Full node, not a bare {"@id"} reference: Google's Dataset validator only resolves @id within the same page's
# graph, so sub-pages that referenced the Person defined on /about/ were flagged "Invalid object type for creator".
PERSON_REF = {"@type": "Person", "@id": PERSON_ID, "name": "Patrik Rojan", "url": SITE_URL + "about/",
              "sameAs": ["https://www.linkedin.com/in/patrik-rojan/", "https://github.com/mixtpatrik"]}


def footer_links(active=None):
    links = [("/", "The AI graveyard"), ("/dead/", "All 111 tombstones A–Z"), ("/killed-by/", "By killer"),
             ("/layoffs/", "AI layoffs tracker"), ("/jobs/", "Jobs replaced by AI"), ("/coming-soon/", "Upcoming AI shutdowns"), ("/deprecations.ics", "Shutdown calendar (.ics)"),
             ("/funding/", "Failed AI startups"), ("/api/", "JSON API"), ("/about/", "About & methodology"), ("/feed.xml", "RSS")]
    return " · ".join(f'<a href="{h}">{t}</a>' for h, t in links)


WEBSITE_REF = {"@type": "WebSite", "@id": SITE_URL + "#website", "name": "Killed by AI", "url": SITE_URL}
ORG_REF = {"@type": "Organization", "@id": SITE_URL + "#org", "name": "Killed by AI", "url": SITE_URL}
GRAVEYARD_DATASET_REF = {"@type": "Dataset", "@id": SITE_URL + "api/#graveyard", "name": "Killed by AI Graveyard", "url": SITE_URL}


def webpage_node(url, name, desc, modified, extra=None):
    node = {"@type": "WebPage", "@id": url, "url": url, "name": name, "description": desc,
            "isPartOf": WEBSITE_REF, "dateModified": modified}
    if extra:
        node.update(extra)
    return node


def killer_slug(name):
    return slugify(name)


def git_lastmod(paths, needle=None):
    """Last commit date touching these paths (optionally filtered to commits containing `needle`)."""
    try:
        cmd = ["git", "log", "-1", "--format=%cs"]
        if needle:
            cmd += ["-S", needle]
        cmd += ["--", *paths]
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=15).stdout.strip()
        return out or None
    except Exception:
        return None


def product_title(item):
    name, dt, mon, yr = item["name"], item.get("deathType"), fmt_month(item["dateClose"]), item["dateClose"][:4]
    cands = {
        "model-upgrade": [f"{name} deprecated: retirement date and replacement", f"{name} deprecated ({mon})", f"{name} retired {mon}"],
        "feature-removed": [f"{name} removed: what happened and what replaced it", f"{name} removed ({mon})", f"{name} shut down {mon}"],
        "startup-failed": [f"What happened to {name}? ({yr})", f"{name} shut down ({yr})"],
        "acqui-hired": [f"What happened to {name}? (acqui-hired {yr})", f"What happened to {name}? ({yr})", f"{name} acquired ({yr})"],
        "hardware-failed": [f"{name} discontinued: what happened", f"{name} discontinued ({mon})"],
    }.get(dt, [f"Is {name} dead? Shut down {mon} | Killed by AI", f"Is {name} dead? Shut down {mon}", f"{name} shut down {mon}"])
    for t in cands:
        if len(t) <= 60:
            return t
    return cands[-1][:60]


def render_product(item, ordered, idx, tpl, total, killer_counts):
    name = item["name"]; slug = item.get("slug") or slugify(name); url = product_url(item)
    days = days_between(item["dateOpen"], item["dateClose"]); lifespan = format_lifespan(days)
    seo = item.get("seo") or {}
    title = seo.get("title") or product_title(item)
    h1 = seo.get("h1") or name
    h1_sub = f'<p class="h1sub">{esc(name)}</p>' if seo.get("h1") else ""
    sentences = re.split(r"(?<=[.!?])\s+", item["description"].strip())
    first = sentences[0]
    dlabel = DEATH_LABEL.get(item.get("deathType"), "Killed")
    meta = seo.get("description") or f"{name} was shut down on {fmt_date(item['dateClose'])} after {lifespan}. Killed by {item['killedBy']}. {first}"
    if len(meta) > 155:
        meta = meta[:152].rsplit(" ", 1)[0] + "…"
    revived = "reversed" in item.get("causeOfDeath", "").lower() or "revived" in item.get("causeOfDeath", "").lower()
    verdict = "Dead, then revived" if revived else "Dead"
    subtitle = f"{dlabel} · {item['causeOfDeath']} · shut down {fmt_date(item['dateClose'])}"
    ks = killer_slug(item["killedBy"])
    has_killer_page = killer_counts.get(item["killedBy"], 0) >= 2
    killer_html = f'<a href="/killed-by/{ks}/">{esc(item["killedBy"])}</a>' if has_killer_page else esc(item["killedBy"])
    collateral = f'<div class="collateral"><span aria-hidden="true">⚠️</span><div><strong>Collateral damage:</strong> {esc(item["collateral"])}</div></div>' if item.get("collateral") else ""
    source = f'<a class="btn btn-red" href="{esc(item["link"])}" target="_blank" rel="noopener">Source ↗</a>' if item.get("link") else ""
    # The answer states the verdict and the facts; it does not re-print the description the reader just saw.
    if revived:
        answer = f"It was, briefly. {name} went dark on {fmt_date(item['dateClose'])} — {item['causeOfDeath'].lower()} — and later came back. The timeline above records the outage."
    else:
        answer = (f"Yes. {name} was shut down on {fmt_date(item['dateClose'])}, {lifespan} after its launch on {fmt_date(item['dateOpen'])}. "
                  f"The cause of death was {item['causeOfDeath'].lower()}; it was killed by {item['killedBy']}. "
                  f"Classification: {dlabel.lower()}." + (" Details and the source are above." if item.get("link") else ""))
    # optional long-form sections
    sections = []
    if item.get("timeline"):
        rows = "".join(f'<li><time datetime="{esc(t["date"])}">{fmt_date(t["date"])}</time><p>{esc(t["text"])}</p></li>' for t in item["timeline"])
        sections.append(f'<section class="sec"><h2>Timeline</h2><ol class="timeline">{rows}</ol></section>')
    if item.get("replacement"):
        sections.append(f'<section class="sec"><h2>What replaced {esc(name)}</h2><p>{esc(item["replacement"])}</p></section>')
    if item.get("aftermath"):
        sections.append(f'<section class="sec"><h2>Aftermath</h2><p>{esc(item["aftermath"])}</p></section>')
    faq_items = [{"q": f"Is {name} dead?", "a": answer}] if not item.get("faq") else list(item["faq"])
    faq_html = "".join(f'<details class="qa-item"><summary>{esc(q["q"])}</summary><p>{esc(q["a"])}</p></details>' for q in faq_items)
    related = [o for o in ordered if o is not item and o["killedBy"] == item["killedBy"]]
    related = sorted(related, key=lambda o: o["dateClose"], reverse=True)[:4]
    related_html = ""
    if related:
        rows = "".join(f'<a class="rel" href="{product_url(o)}"><b>{esc(o["name"])}</b><span>{o["dateClose"][:4]}</span></a>' for o in related)
        more = f' <a class="more" href="/killed-by/{ks}/">All {killer_counts[item["killedBy"]]} →</a>' if has_killer_page else ""
        related_html = f'<h2>Also killed by {esc(item["killedBy"])}{more}</h2><div class="related">{rows}</div>'
    prev_ = ordered[idx - 1] if idx > 0 else None
    next_ = ordered[idx + 1] if idx + 1 < len(ordered) else None
    pn = ""
    if prev_: pn += f'<a class="prev" href="{product_url(prev_)}"><small>← Died before</small>{esc(prev_["name"])}</a>'
    if next_: pn += f'<a class="next" href="{product_url(next_)}"><small>Died after →</small>{esc(next_["name"])}</a>'
    pn_html = f'<nav class="prevnext" aria-label="Chronological">{pn}</nav>' if pn else ""
    modified = entry_lastmod_map().get(name) or item.get("dateAdded") or item["dateClose"]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "All tombstones", "item": SITE_URL + "dead/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
        webpage_node(url, title, meta, modified, {
            "datePublished": item.get("dateAdded", item["dateClose"]), "author": PERSON_REF,
            "about": {"@type": "Thing", "name": name, "description": item["description"],
                      "additionalProperty": [
                          {"@type": "PropertyValue", "name": "Launched", "value": item["dateOpen"]},
                          {"@type": "PropertyValue", "name": "Discontinued", "value": item["dateClose"]},
                          {"@type": "PropertyValue", "name": "Cause of death", "value": item["causeOfDeath"]},
                          {"@type": "PropertyValue", "name": "Killed by", "value": item["killedBy"]}]},
            **({"citation": item["link"]} if item.get("link") else {})}),
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq_items]}]}
    out = tpl
    for k, v in {
        "{{TITLE}}": esc(title), "{{OG_TITLE}}": esc(f"{h1} — Killed by AI" if h1 != name else f"{name} — Killed by AI"), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{SLUG}}": slug,
        "{{NAME}}": esc(name), "{{H1}}": esc(h1), "{{H1_SUB}}": h1_sub, "{{NAME_URL}}": html.escape(name.replace(" ", "+"), quote=True), "{{VERDICT}}": verdict, "{{SUBTITLE}}": esc(subtitle),
        "{{DATE_OPEN}}": item["dateOpen"], "{{DATE_OPEN_FMT}}": fmt_date(item["dateOpen"]),
        "{{DATE_CLOSE}}": item["dateClose"], "{{DATE_CLOSE_FMT}}": fmt_date(item["dateClose"]),
        "{{LIFESPAN}}": lifespan, "{{CAUSE}}": esc(item["causeOfDeath"]), "{{KILLER_HTML}}": killer_html,
        "{{TYPE_LABEL}}": TYPE_LABEL.get(item["type"], item["type"]), "{{DESCRIPTION}}": esc(item["description"]),
        "{{COLLATERAL_HTML}}": collateral, "{{SOURCE_HTML}}": source, "{{SECTIONS_HTML}}": "".join(sections), "{{FAQ_HTML}}": faq_html,
        "{{RELATED_HTML}}": related_html, "{{PREV_NEXT_HTML}}": pn_html, "{{COUNT}}": str(total), "{{MODIFIED}}": modified, "{{MODIFIED_FMT}}": fmt_date(modified),
        "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(jsonld, indent=2, ensure_ascii=False),
    }.items():
        out = out.replace(k, v)
    return out


def render_killer_page(killer, items, tpl, total):
    slug = killer_slug(killer); url = f"{SITE_URL}killed-by/{slug}/"
    items = sorted(items, key=lambda i: i["dateClose"], reverse=True)
    n = len(items)
    title = f"{killer}: {n} AI products it killed | Killed by AI"
    if len(title) > 65: title = f"{killer}: {n} AI products killed"
    years = f"{min(i['dateClose'] for i in items)[:4]}–{max(i['dateClose'] for i in items)[:4]}"
    meta = f"Every AI product, model or startup killed by {killer}: {n} deaths between {years}, each with launch date, shutdown date, cause of death and source."
    from collections import Counter as _C
    by_type = _C(TYPE_LABEL.get(i["type"], i["type"]).lower() + "s" for i in items)
    by_year = _C(i["dateClose"][:4] for i in items)
    oldest, newest = items[-1], items[0]
    intro = (f"{killer} has shut down {n} AI products tracked here — "
             + ", ".join(f"{v} {k}" for k, v in by_type.most_common()) + ". "
             + "By year: " + ", ".join(f"{y}: {v}" for y, v in sorted(by_year.items())) + ". "
             + f"The first was {oldest['name']} ({fmt_date(oldest['dateClose'])}); the most recent is {newest['name']} ({fmt_date(newest['dateClose'])}). "
             + f"Each tombstone links its source.")
    rows = "".join(f'<a class="row" href="{product_url(i)}"><span><b>{esc(i["name"])}</b><small>{esc(i["causeOfDeath"])} · {TYPE_LABEL.get(i["type"], i["type"])}</small></span><span class="when">{i["dateClose"]}</span></a>' for i in items)
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": f"Killed by {killer}", "item": url}]},
        {"@type": "ItemList", "name": f"AI products killed by {killer}", "numberOfItems": n,
         "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["name"], "url": product_url(i)} for k, i in enumerate(items)]}]}
    out = tpl
    for k, v in {"{{TITLE}}": esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": f"Killed by {esc(killer)}",
                 "{{H1}}": f"Killed by {esc(killer)}", "{{INTRO}}": esc(intro),
                 "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(jsonld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    return out


def render_jobs_pages(ldata, list_tpl):
    """/jobs/ and /jobs/<role>/ — layoffs re-indexed by the roles AI replaced."""
    roles = json.loads((ROOT / "roles.json").read_text())
    total_jobs = sum(l["jobs"] for l in ldata)
    by_role = {}
    for l in ldata:
        for r in l.get("roleTags", ["various"]):
            by_role.setdefault(r, []).append(l)
    ranked = sorted(by_role.items(), key=lambda kv: -sum(x["jobs"] for x in kv[1]))
    pages = []
    for r, rows in ranked:
        if r == "various" or len(rows) < 2:
            continue
        label = roles.get(r, r); n = len(rows); jobs = sum(x["jobs"] for x in rows)
        rows = sorted(rows, key=lambda x: -x["jobs"])
        url = f"{SITE_URL}jobs/{r}/"
        title = f"{label} jobs replaced by AI: {jobs:,} cut at {n} companies"
        if len(title) > 60: title = f"{label} jobs replaced by AI ({jobs:,} cut)"
        meta = f"{jobs:,} {label.lower()} jobs cut at {n} companies that blamed AI, with the date, the reason given and a source for each: " + ", ".join(x["company"] for x in rows[:4]) + "."
        intro = (f"{label} is one of the roles companies most often name when they attribute layoffs to AI. Across {n} companies tracked here, {jobs:,} jobs in this category were cut "
                 f"(a company's total is counted once per role it named, so role totals overlap). Largest first; every row links its source on the layoffs tracker.")
        rhtml = "".join(f'<a class="row" href="/layoffs/#{slugify(x["company"])}"><span><b>{esc(x["company"])}</b><small>{esc(x["roles"])}</small></span><span class="when">{x["jobs"]:,} · {x["date"][:7]}</span></a>' for x in rows)
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "Jobs replaced by AI", "item": SITE_URL + "jobs/"}, {"@type": "ListItem", "position": 3, "name": label, "item": url}]},
            webpage_node(url, title, meta, lm(["layoffs.json"]), {"@type": "CollectionPage"}),
            {"@type": "ItemList", "numberOfItems": n, "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": f'{x["company"]} — {x["jobs"]:,} jobs', "url": SITE_URL + "layoffs/#" + slugify(x["company"])} for k, x in enumerate(rows)]}]}
        out = list_tpl
        for k, v in {"{{TITLE}}": esc(title + " | Killed by AI") if len(title) <= 47 else esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": f'<a href="/jobs/">Jobs replaced by AI</a> › {esc(label)}',
                     "{{H1}}": f"{esc(label)}: jobs replaced by AI", "{{INTRO}}": esc(intro), "{{ROWS}}": rhtml, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
            out = out.replace(k, v)
        d = ROOT / "jobs" / r; d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(out); pages.append(r)
    # index
    url = SITE_URL + "jobs/"
    rhtml = "".join(f'<a class="row" href="/jobs/{r}/"><span><b>{esc(roles.get(r, r))}</b><small>{len(rows)} companies</small></span><span class="when">{sum(x["jobs"] for x in rows):,}</span></a>' for r, rows in ranked if r in pages)
    title = f"Jobs Replaced by AI: {total_jobs:,} Layoffs by Role | Killed by AI"
    meta = f"Which jobs are being replaced by AI: {total_jobs:,} layoffs at {len(ldata)} companies that blamed AI, broken down by role — customer support, sales, engineering, middle management and more. Sourced."
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "Jobs replaced by AI", "item": url}]},
        webpage_node(url, title, meta, lm(["layoffs.json"]), {"@type": "CollectionPage"}),
        {"@type": "ItemList", "numberOfItems": len(pages), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": roles.get(r, r), "url": f"{SITE_URL}jobs/{r}/"} for k, r in enumerate(pages)]}]}
    out = list_tpl
    for k, v in {"{{TITLE}}": esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": "Jobs replaced by AI",
                 "{{H1}}": "Jobs replaced by AI, by role", "{{INTRO}}": esc(f"The roles companies name when they blame layoffs on AI. {total_jobs:,} jobs across {len(ldata)} companies, re-indexed by the work that was replaced. Customer support leads by a distance. Role totals overlap because one layoff usually hits several roles; the per-company figures are on the layoffs tracker."),
                 "{{ROWS}}": rhtml, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    d = ROOT / "jobs"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)
    return pages


def build_ics(cs_data):
    """deprecations.ics — subscribe to upcoming AI shutdowns in any calendar app."""
    def ics_escape(t):
        return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    stamp = lm(["coming-soon.json"]).replace("-", "") + "T000000Z"   # content date, so builds are reproducible
    events = []
    for c in sorted(cs_data, key=lambda x: x["dateShutdown"]):
        d = c["dateShutdown"].replace("-", "")
        nxt = (datetime.strptime(c["dateShutdown"], "%Y-%m-%d") + __import__("datetime").timedelta(days=1)).strftime("%Y%m%d")
        uid = slugify(c["name"]) + "@killedbyai.net"
        desc = f'{c["description"]} Replacement: {c["replacement"]}. Source: {c["link"]}'
        events.append("BEGIN:VEVENT\r\nUID:" + uid + "\r\nDTSTAMP:" + stamp + "\r\nDTSTART;VALUE=DATE:" + d + "\r\nDTEND;VALUE=DATE:" + nxt
                      + "\r\nSUMMARY:" + ics_escape("🪦 " + c["name"] + " shuts down") + "\r\nDESCRIPTION:" + ics_escape(desc)
                      + "\r\nURL:" + SITE_URL + "coming-soon/#" + slugify(c["name"]) + "\r\nCATEGORIES:AI shutdown\r\nEND:VEVENT")
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Killed by AI//Upcoming AI shutdowns//EN\r\nCALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\n"
            "X-WR-CALNAME:Upcoming AI shutdowns — Killed by AI\r\nX-WR-CALDESC:Confirmed shutdown and deprecation dates for AI products and models. Source: killedbyai.net/coming-soon/\r\nREFRESH-INTERVAL;VALUE=DURATION:P1D\r\n"
            + "\r\n".join(events) + "\r\nEND:VCALENDAR\r\n")


def render_index_pages(data, killer_counts, list_tpl):
    """/dead/ (A–Z, every tombstone) and /killed-by/ (every killer with a page)."""
    az = sorted(data, key=lambda i: i["name"].lower())
    rows = "".join(f'<a class="row" href="{product_url(i)}"><span><b>{esc(i["name"])}</b><small>{esc(i["causeOfDeath"])} · killed by {esc(i["killedBy"])}</small></span><span class="when">{i["dateClose"]}</span></a>' for i in az)
    url = SITE_URL + "dead/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "All tombstones", "item": url}]},
        webpage_node(url, f"All {len(data)} dead AI products, A–Z", "Every tombstone in the AI graveyard, alphabetically.", lm(["graveyard.json"]), {"@type": "CollectionPage"}),
        {"@type": "ItemList", "numberOfItems": len(data), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["name"], "url": product_url(i)} for k, i in enumerate(az)]}]}
    out = list_tpl
    for k, v in {"{{TITLE}}": f"All {len(data)} Dead AI Products, A–Z | Killed by AI", "{{META_DESC}}": esc(f"Every one of the {len(data)} tombstones in the AI graveyard, alphabetically — models, apps, services, startups and hardware, each with dates, cause of death and source."),
                 "{{URL}}": url, "{{CRUMB}}": "All tombstones", "{{H1}}": f"All {len(data)} tombstones, A–Z", "{{INTRO}}": esc("Every dead AI product tracked here, alphabetically. Each page has the launch and death dates, the cause, the killer, and a source."),
                 "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    d = ROOT / "dead"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)

    killers = sorted([(k, n) for k, n in killer_counts.items() if n >= 2], key=lambda x: -x[1])
    rows = "".join(f'<a class="row" href="/killed-by/{killer_slug(k)}/"><span><b>{esc(k)}</b><small>{n} AI products killed</small></span><span class="when">{n}</span></a>' for k, n in killers)
    url = SITE_URL + "killed-by/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "By killer", "item": url}]},
        webpage_node(url, "Who kills the most AI products?", "AI product deaths by the company responsible.", lm(["graveyard.json"]), {"@type": "CollectionPage"})]}
    out = list_tpl
    for k, v in {"{{TITLE}}": "Who Kills the Most AI Products? Deaths by Company | Killed by AI", "{{META_DESC}}": esc(f"AI product shutdowns by the company responsible — {killers[0][0]} leads with {killers[0][1]}. Every killer with two or more dead products has its own page."),
                 "{{URL}}": url, "{{CRUMB}}": "By killer", "{{H1}}": "Killed by whom?", "{{INTRO}}": esc(f"Companies ranked by how many AI products they have shut down. {killers[0][0]} leads with {killers[0][1]}; every company with two or more kills has its own page listing them."),
                 "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    d = ROOT / "killed-by"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)


def render_card(item, killer_counts=None):
    killer_counts = killer_counts or {}
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
    slug = item.get("slug") or slugify(item["name"])
    death_type = item.get("deathType", "product-killed")
    new_badge = '<span class="badge-new" title="Added in the last two weeks">NEW</span>' if is_new(item) else ""
    return f'''<article class="card{" is-new" if new_badge else ""}" id="{slug}" data-type="{esc(item["type"])}" data-death-type="{death_type}" data-name="{esc(item["name"].lower())}" data-desc="{esc(item["description"].lower())}" data-killer="{esc(item["killedBy"].lower())}" data-cause="{esc(item["causeOfDeath"].lower())}" data-date-close="{esc(item["dateClose"])}" data-date-open="{esc(item["dateOpen"])}" data-added="{esc(item.get("dateAdded", ""))}" data-days="{days}">
  <header class="card-header">
    <h3 class="card-name"><a href="/dead/{slug}/">{esc(item["name"])}</a>{new_badge}</h3>
    <span class="card-lifespan">{y_open} — {y_close}</span>
  </header>
  <p class="card-description">{esc(item["description"])}</p>
  <footer class="card-footer">
    <div class="card-tags">
      <span class="tag">{esc(item["type"])}</span>
      <span class="tag">{esc(item["causeOfDeath"])}</span>
      {('<a class="tag tag-killer" href="/killed-by/' + killer_slug(item["killedBy"]) + '/">Killed by: ' + esc(item["killedBy"]) + '</a>') if killer_counts.get(item["killedBy"], 0) >= 2 else ('<span class="tag tag-killer">Killed by: ' + esc(item["killedBy"]) + '</span>')}
    </div>
    <div class="card-age">{lifespan}</div>
  </footer>
  {collateral_html}
  {link_html}
</article>'''


def temporal_coverage(items):
    """ISO 8601 interval spanning the oldest launch to the newest death."""
    return f'{min(i["dateOpen"] for i in items)}/{max(i["dateClose"] for i in items)}'


def build_jsonld(items):
    """Build an ItemList JSON-LD for structured data."""
    list_items = []
    for i, item in enumerate(items, 1):
        list_items.append({"@type": "ListItem", "position": i, "name": item["name"], "url": product_url(item)})

    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": SITE_URL + "#org",
                "name": "Killed by AI",
                "url": SITE_URL,
                "logo": SITE_URL + "og-image.png",
                "founder": PERSON_REF,
                "sameAs": ["https://github.com/mixtpatrik/killedbyai"],
            },
            {
                "@type": "Person", "@id": PERSON_ID, "name": "Patrik Rojan", "url": SITE_URL + "about/",
                "sameAs": ["https://www.linkedin.com/in/patrik-rojan/", "https://github.com/mixtpatrik"],
            },
            {
                "@type": "WebSite",
                "@id": SITE_URL + "#website",
                "publisher": ORG_REF,
                "url": SITE_URL,
                "name": "Killed by AI",
                "description": "A digital cemetery for discontinued AI models, apps, startups, and hardware.",
            },
            webpage_node(SITE_URL, "Killed by AI — The AI Graveyard", f"{len(items)} dead AI products, each with dates, cause of death, killer and source.",
                         lm(["graveyard.json", "template.html"]), {"@type": "CollectionPage"}),
            {
                "@type": "Dataset",
                "@id": SITE_URL + "api/#graveyard",
                "name": "Killed by AI Graveyard",
                "description": "An open dataset of discontinued AI products, models, startups, and hardware, tracking casualties of the artificial intelligence gold rush.",
                "url": SITE_URL,
                "keywords": "AI graveyard, killed by AI, discontinued AI, deprecated AI models, AI shutdown, dead AI products",
                "license": DATA_LICENSE,
                "isAccessibleForFree": True,
                "creator": PERSON_REF,
                "dateModified": lm(["graveyard.json"]),
                "temporalCoverage": temporal_coverage(items),
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": SITE_URL + "graveyard.json",
                },
            },
            {
                "@type": "ItemList",
                "name": "Discontinued AI Products",
                "numberOfItems": len(items),
                "itemListElement": list_items,
            },
        ],
    }



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

    sora = next((i for i in items if i.get("slug") == "openai-sora"), None)
    sora_answer = (f"OpenAI shut down the Sora app on April 26, 2026 — about $1M a day in compute against fewer than 500K users, and a collapsed $1B Disney deal. The API follows on September 24. "
                   f"Full timeline: <a href=\"{product_url(sora)}\">Sora AI shutdown</a>.") if sora else "OpenAI shut down Sora in April 2026 due to unsustainable compute costs."
    def link_for(slug, text):
        it = next((i for i in items if i.get("slug") == slug), None)
        return f'<a href="{product_url(it)}">{esc(text)}</a>' if it else esc(text)
    chatgpt_answer = ("No — ChatGPT itself is alive. But plenty of what shipped inside it is not: "
                      + ", ".join([link_for("chatgpt-plugins", "ChatGPT Plugins"), link_for("openai-gpt-store", "the GPT Store"), link_for("gpt-4o-chatgpt", "GPT-4o"),
                                   link_for("gpt-4-original", "the original GPT-4"), link_for("dall-e-gpt-in-chatgpt", "the DALL·E GPT")])
                      + '. Browse every OpenAI death on the <a href="/killed-by/openai/">OpenAI page</a>.')

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
            "q": "Is ChatGPT dead?",
            "a": chatgpt_answer
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
                    "text": re.sub(r"<[^>]+>", "", f["a"]),
                },
            }
            for f in faqs
        ],
    }

    faq_html_items = "\n".join(
        f'''<details class="faq-item">
  <summary><h3>{esc(f["q"])}</h3></summary>
  <div class="faq-answer">
    <p>{f["a"] if "<a " in f["a"] else esc(f["a"])}</p>
  </div>
</details>'''
        for f in faqs
    )

    return faq_schema, faq_html_items


def build_rss(items):
    """Build an RSS 2.0 feed sorted by most recently ADDED (so backfilled older deaths still surface)."""
    sorted_items = sorted(items, key=lambda i: (i.get("dateAdded") or i["dateClose"], i["dateClose"]), reverse=True)[:30]
    today = datetime.strptime(max(lm(["graveyard.json"]), lm(["layoffs.json"]), lm(["coming-soon.json"])), "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")

    rss_items = []
    for item in sorted_items:
        slug = slugify(item["name"])
        pub_date = datetime.strptime(item.get("dateAdded") or item["dateClose"], "%Y-%m-%d").strftime(
            "%a, %d %b %Y 00:00:00 +0000"
        )
        url = product_url(item)
        rss_items.append(
            f"""    <item>
      <title>{esc(item["name"])} — Killed by {esc(item["killedBy"])} ({item["dateClose"]})</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
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
            f'<a class="lb-row" href="/killed-by/{killer_slug(killer)}/" data-killer="{esc(killer.lower())}" title="Filter the graveyard to {esc(killer)}; open the link for the full page">'
            f'<span class="lb-name">{esc(killer)}</span>'
            f'<span class="lb-bar-wrap"><span class="lb-bar" style="width:{pct}%"></span></span>'
            f'<span class="lb-count">{count}</span>'
            f'</a>'
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
            f'<span class="bar-track"><span class="bar-fill"></span></span>'
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
    "name", "slug", "dateOpen", "dateClose", "dateAdded", "description",
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

    seen = set(); slugs = {}
    for item in data:
        name = item.get("name", "<unnamed>")
        if name in seen:
            warnings.append(f"graveyard: duplicate entry '{name}'")
        seen.add(name)
        s = item.get("slug")
        if s:
            if s in slugs:
                warnings.append(f"graveyard: slug '{s}' used by both '{slugs[s]}' and '{name}'")
            slugs[s] = name
            if s != slugify(s):
                warnings.append(f"graveyard: '{name}' slug '{s}' is not URL-safe")

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


REDIRECT_STUB = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting to {target}</title>
<link rel="canonical" href="{target}">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace("{target}" + location.search + location.hash);</script>
</head>
<body><p>This page has moved to <a href="{target}">{target}</a>.</p></body>
</html>
"""


def publish(slug, html):
    """Write a page at /slug/ and leave a redirect stub at the legacy /slug.html.

    GitHub Pages serves any .html file at both /slug and /slug.html, which is
    duplicate content we cannot fix server-side (no .htaccess, no _redirects).
    Serving the real page from a directory gives one canonical URL, and the
    stub collapses the old extension onto it.
    """
    d = ROOT / slug
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(html)
    (ROOT / f"{slug}.html").write_text(REDIRECT_STUB.format(target=f"{SITE_URL}{slug}/"))


def build_breadcrumb(name, slug):  # noqa
    """BreadcrumbList so Google shows Home > Section instead of a bare URL."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": name, "item": f"{SITE_URL}{slug}/"},
        ],
    }


def build_layoffs_jsonld(ldata):
    """Dataset + ItemList for the layoffs page."""
    total = sum(l["jobs"] for l in ldata)
    items = [
        {
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Thing",
                "name": f'{l["company"]} — {l["jobs"]:,} jobs cut',
                "url": SITE_URL + "layoffs/#" + slugify(l["company"]),
                "description": l["description"],
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Jobs cut", "value": l["jobs"]},
                    {"@type": "PropertyValue", "name": "Date announced", "value": l["date"]},
                    {"@type": "PropertyValue", "name": "Roles affected", "value": l["roles"]},
                ],
            },
        }
        for i, l in enumerate(sorted(ldata, key=lambda x: -x["jobs"]), 1)
    ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Dataset",
                "@id": SITE_URL + "api/#layoffs",
                "name": "AI-Attributed Layoffs Tracker",
                "description": (
                    f"{total:,} jobs cut across {len(ldata)} companies that explicitly cited AI, "
                    "automation, or an AI-first strategy as a reason."
                ),
                "url": SITE_URL + "layoffs/",
                "keywords": "AI layoffs, jobs killed by AI, AI job cuts, automation layoffs, AI unemployment",
                "license": DATA_LICENSE,
                "isAccessibleForFree": True,
                "dateModified": lm(["layoffs.json"]),
                "creator": PERSON_REF,
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": SITE_URL + "layoffs.json",
                },
            },
            webpage_node(SITE_URL + "layoffs/", "AI Layoffs Tracker", f"{total:,} jobs cut by AI at {len(ldata)} companies.", lm(["layoffs.json", "layoffs-template.html"]), {"@type": "CollectionPage"}),
            {"@type": "ItemList", "numberOfItems": len(ldata), "itemListElement": items},
        ],
    }


def build_coming_soon_jsonld(cs_data):
    """ItemList of scheduled shutdowns, each with its announced death date."""
    items = [
        {
            "@type": "ListItem",
            "position": i,
            "item": {
                "@type": "Thing",
                "name": c["name"],
                "url": SITE_URL + "coming-soon/#" + slugify(c["name"]),
                "description": c["description"],
                "additionalProperty": [
                    {"@type": "PropertyValue", "name": "Shutdown date", "value": c["dateShutdown"]},
                    {"@type": "PropertyValue", "name": "Announced", "value": c["dateAnnounced"]},
                    {"@type": "PropertyValue", "name": "Replacement", "value": c["replacement"]},
                    {"@type": "PropertyValue", "name": "Killed by", "value": c["killedBy"]},
                ],
            },
        }
        for i, c in enumerate(sorted(cs_data, key=lambda x: x["dateShutdown"]), 1)
    ]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Dataset",
                "@id": SITE_URL + "api/#coming-soon",
                "name": "Upcoming AI Product Shutdowns",
                "description": f"{len(cs_data)} AI products and models with publicly confirmed shutdown dates.",
                "url": SITE_URL + "coming-soon/",
                "keywords": "AI deprecation schedule, upcoming AI shutdowns, model retirement dates, AI sunset",
                "license": DATA_LICENSE,
                "isAccessibleForFree": True,
                "dateModified": lm(["coming-soon.json"]),
                "creator": PERSON_REF,
                "distribution": {
                    "@type": "DataDownload",
                    "encodingFormat": "application/json",
                    "contentUrl": SITE_URL + "coming-soon.json",
                },
            },
            webpage_node(SITE_URL + "coming-soon/", "Upcoming AI Shutdowns & Model Deprecation Dates", f"{len(cs_data)} AI products with confirmed shutdown dates.", lm(["coming-soon.json", "coming-soon-template.html"]), {"@type": "CollectionPage"}),
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f"When does {c['name']} shut down?",
                "acceptedAnswer": {"@type": "Answer", "text": f"{c['name']} is scheduled to shut down on {fmt_date(c['dateShutdown'])} (announced {fmt_date(c['dateAnnounced'])}). Replacement: {c['replacement']}."}}
                for c in sorted(cs_data, key=lambda x: x["dateShutdown"])]},
            {"@type": "ItemList", "numberOfItems": len(cs_data), "itemListElement": items},
        ],
    }


def build_funding_jsonld(funded, total_b):
    """Dataset for the funding page."""
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": SITE_URL + "api/#funding",
        "isBasedOn": GRAVEYARD_DATASET_REF,
        "name": "VC Funding Burned by Failed AI Startups",
        "description": (
            f"${total_b} billion in venture capital raised by {len(funded)} AI startups that shut down, "
            "were acqui-hired into oblivion, or ran out of money."
        ),
        "url": SITE_URL + "funding/",
        "keywords": "failed AI startups, AI startup failures, VC funding burned, AI bubble, wasted venture capital",
        "license": DATA_LICENSE,
        "isAccessibleForFree": True,
        "dateModified": lm(["graveyard.json"]),
        "creator": PERSON_REF,
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": SITE_URL + "graveyard.json",
        },
    }


def main():
    data = json.loads((ROOT / "graveyard.json").read_text())
    data.sort(key=lambda i: (i["dateClose"], i.get("dateAdded", "")), reverse=True)
    template = (ROOT / "template.html").read_text()

    from collections import Counter as _Counter
    killer_counts = _Counter(i["killedBy"] for i in data)
    cards_html = "\n".join(render_card(item, killer_counts) for item in data)
    content_updated = max(lm(["graveyard.json"]), lm(["layoffs.json"]), lm(["coming-soon.json"]))
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
              .replace("{{FOOTER_LINKS}}", footer_links())
              .replace("{{LAST_UPDATED}}", fmt_date(content_updated)))

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

    # Per-product pages (/dead/<slug>/) and per-killer pages (/killed-by/<slug>/)
    ordered = sorted(data, key=lambda i: i["dateClose"])
    prod_tpl = (ROOT / "product-template.html").read_text()
    for idx, item in enumerate(ordered):
        d = ROOT / "dead" / (item.get("slug") or slugify(item["name"])); d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_product(item, ordered, idx, prod_tpl, len(data), killer_counts))
        for old in item.get("aliases", []):   # renamed entries keep their old URL as a redirect stub
            od = ROOT / "dead" / old; od.mkdir(parents=True, exist_ok=True)
            (od / "index.html").write_text(REDIRECT_STUB.format(target=product_url(item)))
    list_tpl = (ROOT / "list-template.html").read_text()
    render_index_pages(data, killer_counts, list_tpl)
    job_pages = render_jobs_pages(json.loads((ROOT / "layoffs.json").read_text()), list_tpl) if (ROOT / "layoffs.json").exists() else []
    killer_pages = []
    for killer, n in killer_counts.items():
        if n < 2:
            continue
        d = ROOT / "killed-by" / killer_slug(killer); d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_killer_page(killer, [i for i in data if i["killedBy"] == killer], list_tpl, len(data)))
        killer_pages.append(killer)
    print(f"Built {len(ordered)} product pages and {len(killer_pages)} killer pages")
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
            f'''<article class="layoff-row" id="{slugify(l["company"])}">
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
        by_year_n = {}
        for l in layoffs:
            by_year_n[l["date"][:4]] = by_year_n.get(l["date"][:4], 0) + 1
        year_table = ("<table class=\"year-table\"><thead><tr><th>Year</th><th>Companies</th><th>Jobs cut, AI cited</th></tr></thead><tbody>"
                      + "".join(f"<tr><td>{y}</td><td>{by_year_n[y]}</td><td>{c:,}</td></tr>" for y, c in sorted(by_year.items()))
                      + f"<tr><th>Total</th><th>{len(layoffs)}</th><th>{total_jobs:,}</th></tr></tbody></table>")
        this_year = str(datetime.utcnow().year)
        largest = sorted([l for l in layoffs if l["date"].startswith(this_year)], key=lambda l: -l["jobs"])[:5]
        largest_html = "<ol class=\"largest\">" + "".join(f'<li><a href="#{slugify(l["company"])}"><b>{esc(l["company"])}</b> — {l["jobs"]:,} jobs</a> <span>{fmt_month(l["date"])}</span></li>' for l in largest) + "</ol>"
        year_2026_jobs = by_year.get(this_year, 0)

        layoffs_out = (layoffs_template
                       .replace("{{JSONLD}}", json.dumps(build_layoffs_jsonld(ldata), indent=2))
                  .replace("{{BREADCRUMB}}", json.dumps(build_breadcrumb("AI Layoffs Tracker", "layoffs"), indent=2))
                  .replace("{{ROWS}}", rows_html)
                       .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
                       .replace("{{TOTAL_COMPANIES}}", str(total_companies))
                       .replace("{{YEAR_STATS}}", year_stats)
                       .replace("{{YEAR_TABLE}}", year_table)
                       .replace("{{LARGEST_HTML}}", largest_html)
                       .replace("{{THIS_YEAR}}", this_year)
                       .replace("{{THIS_YEAR_JOBS}}", f"{year_2026_jobs:,}")
                       .replace("{{FOOTER_LINKS}}", footer_links())
                       .replace("{{LAST_UPDATED}}", fmt_date(lm(["layoffs.json"]))))
        publish("layoffs", layoffs_out)
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
            f'''<article class="fund-row" id="{item.get("slug") or slugify(item["name"])}">
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
                    .replace("{{JSONLD}}", json.dumps(build_funding_jsonld(funded, total_b), indent=2))
                    .replace("{{BREADCRUMB}}", json.dumps(build_breadcrumb("Funding Burned", "funding"), indent=2))
                    .replace("{{ROWS}}", fund_rows)
                    .replace("{{FOOTER_LINKS}}", footer_links())
                    .replace("{{TOTAL_B}}", total_b)
                    .replace("{{COUNT}}", str(len(funded)))
                    .replace("{{LAST_UPDATED}}", fmt_date(lm(["graveyard.json"]))))
        publish("funding", fund_out)
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
            days_left = (shutdown.date() - now.date()).days
            if days_left > 0:
                countdown = f"{days_left}d left"
                dead_class = ""
            elif days_left == 0:
                countdown = "Today"
                dead_class = ""
            else:
                countdown = "DEAD"
                dead_class = " dead"

            tomb = ""
            if item.get("graveyardSlug"):
                tomb = f'<a class="doom-tomb" href="/dead/{esc(item["graveyardSlug"])}/">🪦 Read the tombstone →</a>'
            cs_rows.append(
                f'''<article class="doom-card" id="{slugify(item["name"])}">
  <div class="doom-header">
    <h2 class="doom-name">{esc(item["name"])}</h2>
    <span class="doom-countdown{dead_class}" data-shutdown="{item["dateShutdown"]}">{countdown}</span>
  </div>
  <p class="doom-desc">{esc(item["description"])}</p>
  <div class="doom-meta">
    <span class="doom-tag">Killed by: {esc(item["killedBy"])}</span>
    <span>Shutdown: {item["dateShutdown"]}</span>
    <span>Replacement: {esc(item["replacement"])}</span>
    <a class="doom-source" href="{esc(item["link"])}" target="_blank" rel="noopener">Source</a>{tomb}
  </div>
</article>'''
            )

        cs_out = (cs_template
                  .replace("{{JSONLD}}", json.dumps(build_coming_soon_jsonld(cs_data), indent=2))
                  .replace("{{BREADCRUMB}}", json.dumps(build_breadcrumb("Coming Soon", "coming-soon"), indent=2))
                  .replace("{{ROWS}}", "\n".join(cs_rows))
                  .replace("{{FOOTER_LINKS}}", footer_links())
                  .replace("{{LAST_UPDATED}}", fmt_date(lm(["coming-soon.json"])))
                  .replace("{{COUNT}}", str(len(cs_sorted))))
        publish("coming-soon", cs_out)
        # RFC 5545 requires CRLF line endings; also fold lines at 75 octets so strict clients (Google Calendar) accept it
        ics_lines = []
        for line in build_ics(cs_data).replace("\r\n", "\n").split("\n"):
            enc = line.encode("utf-8")
            while len(enc) > 73:
                cut = 73
                while cut > 0 and (enc[cut] & 0xC0) == 0x80:  # don't split a UTF-8 sequence
                    cut -= 1
                ics_lines.append(enc[:cut].decode("utf-8")); enc = b" " + enc[cut:]
            ics_lines.append(enc.decode("utf-8"))
        (ROOT / "deprecations.ics").write_bytes("\r\n".join(ics_lines).encode("utf-8"))
        print(f"Built coming-soon.html with {len(cs_sorted)} entries")

    # Build sitemap — lastmod derived from git so it changes only when content does
    pages = [
        (SITE_URL, "1.0", "daily", lm(["graveyard.json", "template.html", "build.py"])),
        (SITE_URL + "layoffs/", "0.9", "weekly", lm(["layoffs.json", "layoffs-template.html"])),
        (SITE_URL + "coming-soon/", "0.8", "weekly", lm(["coming-soon.json", "coming-soon-template.html"])),
        (SITE_URL + "funding/", "0.8", "weekly", lm(["graveyard.json", "funding-template.html"])),
        (SITE_URL + "api/", "0.6", "monthly", lm(["api/index.html"])),
        (SITE_URL + "about/", "0.5", "monthly", lm(["about/index.html"])),
    ]
    mods = entry_lastmod_map()
    pages.append((SITE_URL + "jobs/", "", "", lm(["layoffs.json"])))
    for r in job_pages:
        pages.append((f"{SITE_URL}jobs/{r}/", "", "", lm(["layoffs.json"])))
    pages.append((SITE_URL + "dead/", "", "", lm(["graveyard.json"])))
    pages.append((SITE_URL + "killed-by/", "", "", lm(["graveyard.json"])))
    for item in ordered:
        pages.append((product_url(item), "", "", mods.get(item["name"]) or item.get("dateAdded") or item["dateClose"]))
    for killer in killer_pages:
        pages.append((f"{SITE_URL}killed-by/{killer_slug(killer)}/", "", "", max(mods.get(i["name"], "") for i in data if i["killedBy"] == killer) or lm(["graveyard.json"])))
    sitemap_urls = "\n".join(
        f"  <url>\n    <loc>{esc(url)}</loc>\n    <lastmod>{mod}</lastmod>\n  </url>"
        for url, prio, freq, mod in pages
    )
    sitemap_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{sitemap_urls}
</urlset>
'''
    (ROOT / "sitemap.xml").write_text(sitemap_xml)

    print(f"Built index.html with {len(data)} entries")
    print("Generated sitemap.xml, robots.txt, feed.xml")

    api_page = ROOT / "api" / "index.html"
    if api_page.exists():
        api_html = re.sub(r'"dateModified": "\d{4}-\d{2}-\d{2}"',
                          '"dateModified": "%s"' % max(lm(["graveyard.json"]), lm(["layoffs.json"]), lm(["coming-soon.json"])),
                          api_page.read_text())
        api_page.write_text(api_html)

    ldata_for_check = json.loads((ROOT / "layoffs.json").read_text()) if (ROOT / "layoffs.json").exists() else []
    cs_for_check = json.loads((ROOT / "coming-soon.json").read_text()) if (ROOT / "coming-soon.json").exists() else []
    warnings = validate(data, ldata_for_check, cs_for_check)
    if warnings:
        print(f"\n⚠️  {len(warnings)} data warning(s):")
        for w in warnings:
            print(f"   - {w}")
    else:
        print("✓ Data checks passed")
    # A scheduled death that is two weeks past its date and still has no tombstone is a content bug, not a warning.
    cutoff = (datetime.utcnow() - __import__("datetime").timedelta(days=14)).strftime("%Y-%m-%d")
    stale = [c["name"] for c in cs_for_check if c.get("dateShutdown", "") < cutoff]
    if stale:
        print(f"\n✗ BUILD FAILED: {len(stale)} coming-soon entr{'y is' if len(stale)==1 else 'ies are'} 14+ days past shutdown — migrate to graveyard.json: {', '.join(stale)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
