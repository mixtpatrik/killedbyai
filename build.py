#!/usr/bin/env python3
"""
Build script for Killed by AI.
Reads graveyard.json and generates index.html with:
- Pre-rendered cards in the initial HTML (for SEO indexability)
- Inline JSON data (for JS-based search/filter/sort)
- JSON-LD structured data
"""
import calendar
import json
import shutil
import html
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

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


def _lifespan_parts(days):
    years, rem = divmod(days, 365)
    months, d = divmod(rem, 30)
    if months >= 12:  # rem 360-364: round up to the next full year instead of printing "12m"
        years, months, d = years + 1, 0, 0
    return years, months, d


def format_lifespan(days):
    years, months, d = _lifespan_parts(days)
    if years and months:
        return f"{years}y {months}m"
    if years:
        return f"{years}y"
    if months and d:
        return f"{months}m {d}d"
    if months:
        return f"{months}m"
    return f"{d}d"


def format_lifespan_long(days):
    """Prose form of format_lifespan ("2 years, 5 months", "1 day") for meta descriptions and FAQ answers."""
    years, months, d = _lifespan_parts(days)
    unit = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    if years:
        return unit(years, "year") + (f", {unit(months, 'month')}" if months else "")
    if months:
        return unit(months, "month") + (f", {unit(d, 'day')}" if d else "")
    return unit(d, "day")


def lc_label(s):
    """Title Case label -> mid-sentence form, keeping acronyms (AI, API, IT, HR)."""
    return re.sub(r"[A-Za-z]+", lambda m: m[0] if len(m[0]) > 1 and m[0].isupper() else m[0].lower(), s)


def company_key(name):
    """'PayPal (2026)' -> 'PayPal': a repeat layoff at the same company is a second row, not a second company."""
    return re.sub(r"\s*\([^()]*\b(?:19|20)\d\d\)$", "", name).strip()


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
    links = [("/", "The AI graveyard"), ("/dead/", f"All {len(json.loads((ROOT / 'graveyard.json').read_text()))} tombstones A-Z"), ("/killed-by/", "By killer"),
             ("/layoffs/", "AI layoffs tracker"), ("/will-ai-take-my-job/", "Will AI take my job?"), ("/jobs/", "Jobs replaced by AI"), ("/coming-soon/", "Upcoming AI shutdowns"), ("/deprecations.ics", "Shutdown calendar (.ics)"),
             ("/funding/", "Failed AI startups"), ("/embed/", "Embed & share"), ("/api/", "JSON API"), ("/about/", "About & methodology"), ("/feed.xml", "RSS")]
    return " · ".join(f'<a href="{h}">{t}</a>' for h, t in links)


NAV_LINKS = [("/", "💀 Graveyard"), ("/layoffs/", "💼 AI Layoffs"), ("/funding/", "🔥 Funding"), ("/coming-soon/", "⏳ Dying soon"),
             ("/will-ai-take-my-job/", "🎯 Will AI take my job?"), ("/embed/", "📤 Embed & share")]


def site_nav(active, page_path=None):
    """Top nav links with the section `active` highlighted; aria-current="page" only on the section's own URL."""
    out = []
    for h, t in NAV_LINKS:
        if h == active:
            out.append(f'<a href="{h}" class="site-nav-item active" aria-current="{"page" if page_path == h else "true"}">{t}</a>')
        else:
            out.append(f'<a href="{h}" class="site-nav-item">{t}</a>')
    return "".join(out)


# killedBy values that are causes, not companies: how to say "killed by X" in running text (None = it died on its own).
KILLER_PROSE = {"Itself": None, "Market": "the market", "Reality": "reality", "Inference Bills": "inference bills",
                "Its Own Founder": "its own founder", "Its Own Parent Company": "its own parent company", "Big Tech": "Big Tech",
                "AI Coding Agents": "AI coding agents", "Foundation Models": "foundation models"}


def killed_by_clause(killer):
    """'it was killed by OpenAI' / 'it was killed by the market' / 'it collapsed on its own'."""
    if killer in KILLER_PROSE and KILLER_PROSE[killer] is None:
        return "it collapsed on its own"
    return f"it was killed by {KILLER_PROSE.get(killer, killer)}"


def killer_label(killer):
    """Heading form: 'Killed by OpenAI', 'Killed by the market', 'Killed by itself'."""
    if killer in KILLER_PROSE:
        return f"Killed by {KILLER_PROSE[killer] or 'itself'}"
    return f"Killed by {killer}"


WEBSITE_REF = {"@type": "WebSite", "@id": SITE_URL + "#website", "name": "Killed by AI", "url": SITE_URL}
ORG_REF = {"@type": "Organization", "@id": SITE_URL + "#org", "name": "Killed by AI", "url": SITE_URL}


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


def is_revived(item):
    cause = item.get("causeOfDeath", "").lower()
    return "reversed" in cause or "revived" in cause


def product_title(item):
    name, dt, mon, yr = item["name"], item.get("deathType"), fmt_month(item["dateClose"]), item["dateClose"][:4]
    has_r = bool(item.get("replacement"))   # only promise "what replaced it" when the page has that section
    verb = {"model-upgrade": "retired", "hardware-failed": "discontinued", "acqui-hired": "acquired"}.get(dt, "shut down")
    if is_revived(item):
        cands = [f"Is {name} dead? No, shutdown reversed ({yr})", f"{name}: shutdown reversed ({yr})", f"{name} revived ({yr})"]
    else:
        cands = {
            "model-upgrade": ([f"{name} deprecated: retirement date and replacement"] if has_r else []) + [f"{name} deprecated ({mon})", f"{name} retired {mon}"],
            "feature-removed": ([f"{name} removed: what happened and what replaced it"] if has_r else []) + [f"{name} removed ({mon})", f"{name} shut down {mon}"],
            "startup-failed": [f"What happened to {name}? ({yr})", f"{name} shut down ({yr})"],
            "acqui-hired": [f"What happened to {name}? (acqui-hired {yr})", f"What happened to {name}? ({yr})", f"{name} acquired ({yr})"],
            "hardware-failed": [f"{name} discontinued: what happened", f"{name} discontinued ({mon})"],
        }.get(dt, [f"Is {name} dead? Shut down {mon} | Killed by AI", f"Is {name} dead? Shut down {mon}", f"{name} shut down {mon}"])
    # Shorter fallbacks that keep every word and date whole; never slice mid-word or mid-date ("retired Oct 20").
    cands += [f"{name} {verb} {yr}", f"{name} ({yr})", name]
    for t in cands:
        if len(t) <= 60:
            return t
    return name[:59].rsplit(" ", 1)[0].rstrip(" ,&-:(") + "…"


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
    revived = is_revived(item)
    if revived:
        auto_meta = f"{name}: killed on {fmt_date(item['dateClose'])}, then the decision was reversed. {first}"
    else:
        clause = killed_by_clause(item["killedBy"])
        auto_meta = f"{name} was shut down on {fmt_date(item['dateClose'])} after {format_lifespan_long(days)}; {clause}. {first}"
    meta = seo.get("description") or auto_meta
    if len(meta) > 155:
        meta = meta[:152].rsplit(" ", 1)[0] + "…"
    verdict = "Dead, then revived" if revived else "Dead"
    subtitle = f"{dlabel} · {item['causeOfDeath']} · shut down {fmt_date(item['dateClose'])}"
    ks = killer_slug(item["killedBy"])
    has_killer_page = killer_counts.get(item["killedBy"], 0) >= 2
    killer_html = f'<a href="/killed-by/{ks}/">{esc(item["killedBy"])}</a>' if has_killer_page else esc(item["killedBy"])
    collateral = f'<div class="collateral"><span aria-hidden="true">⚠️</span><div><strong>Collateral damage:</strong> {esc(item["collateral"])}</div></div>' if item.get("collateral") else ""
    source = f'<a class="btn btn-red" href="{esc(item["link"])}" target="_blank" rel="noopener">Source ↗</a>' if item.get("link") else ""
    # The answer states the verdict and the facts; it does not re-print the description the reader just saw.
    if revived:
        tail = (" The timeline above records the outage." if item.get("timeline")
                else " Details and the source are above." if item.get("link") else "")
        cause = lc_label(re.sub(r"\s*\((?:reversed|revived)\)", "", item["causeOfDeath"], flags=re.I))
        answer = (f"Not right now. {name} was killed on {fmt_date(item['dateClose'])} "
                  f"({cause}), but that decision was later reversed.{tail}")
    else:
        answer = (f"Yes. {name} was shut down on {fmt_date(item['dateClose'])}, {format_lifespan_long(days)} after its launch on {fmt_date(item['dateOpen'])}. "
                  f"The cause of death was {lc_label(item['causeOfDeath'])}; {killed_by_clause(item['killedBy'])}. "
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
        related_html = f'<h2>Also {esc(killer_label(item["killedBy"]).replace("Killed", "killed", 1))}{more}</h2><div class="related">{rows}</div>'
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
        "{{TITLE}}": esc(title), "{{OG_TITLE}}": esc(f"{h1} | Killed by AI" if h1 != name else f"{name} | Killed by AI"), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{SLUG}}": slug,
        "{{NAME}}": esc(name), "{{H1}}": esc(h1), "{{H1_SUB}}": h1_sub, "{{NAME_URL}}": esc(quote_plus(name)), "{{VERDICT}}": verdict, "{{SUBTITLE}}": esc(subtitle),
        "{{NAV}}": site_nav("/"),
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
    label = killer_label(killer)   # "Killed by OpenAI" / "Killed by the market" / "Killed by itself"
    if killer in KILLER_PROSE:     # a cause, not a company: no "Itself has shut down…" copy
        title = f"Self-inflicted: {n} AI products that killed themselves" if KILLER_PROSE[killer] is None else f"{label}: {n} AI products"
        who = "collapsed on their own, with no outside killer" if KILLER_PROSE[killer] is None else f"were {label[0].lower() + label[1:]}"
        lead = f"{n} AI products tracked here {who}"
        meta_lead = f"Every AI product that {'collapsed on its own' if KILLER_PROSE[killer] is None else 'was ' + label[0].lower() + label[1:]}"
    else:
        title = f"{killer}: {n} AI products it killed"
        lead = f"{killer} has shut down {n} AI products tracked here"
        meta_lead = f"Every AI product, model or startup killed by {killer}"
    if len(title) <= 45: title += " | Killed by AI"
    y0, y1 = min(i["dateClose"] for i in items)[:4], max(i["dateClose"] for i in items)[:4]
    span = f"in {y0}" if y0 == y1 else f"between {y0} and {y1}"
    meta = f"{meta_lead}: {n} deaths {span}, each with launch date, shutdown date, cause of death and source."
    from collections import Counter as _C
    type_noun = {"app": ("app", "apps"), "model": ("model", "models"), "service": ("service", "services"),
                 "startup": ("startup", "startups"), "hardware": ("hardware device", "hardware devices")}
    by_type = _C(i["type"] for i in items)
    by_year = _C(i["dateClose"][:4] for i in items)
    oldest, newest = items[-1], items[0]
    intro = (f"{lead} ("
             + ", ".join(f"{v} {type_noun.get(k, (k, k + 's'))[v != 1]}" for k, v in by_type.most_common()) + "). "
             + "By year: " + ", ".join(f"{y}: {v}" for y, v in sorted(by_year.items())) + ". "
             + f"The first was {oldest['name']} ({fmt_date(oldest['dateClose'])}); the most recent is {newest['name']} ({fmt_date(newest['dateClose'])}). "
             + f"Each tombstone links its source.")
    rows = "".join(f'<a class="row" href="{product_url(i)}"><span><b>{esc(i["name"])}</b><small>{esc(i["causeOfDeath"])} · {TYPE_LABEL.get(i["type"], i["type"])}</small></span><span class="when">{i["dateClose"]}</span></a>' for i in items)
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": "By killer", "item": SITE_URL + "killed-by/"},
            {"@type": "ListItem", "position": 3, "name": label, "item": url}]},
        {"@type": "ItemList", "name": f"AI products {label[0].lower() + label[1:]}", "numberOfItems": n,
         "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["name"], "url": product_url(i)} for k, i in enumerate(items)]}]}
    out = tpl
    for k, v in {"{{TITLE}}": esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": f'<a href="/killed-by/">By killer</a> › {esc(label)}',
                 "{{H1}}": esc(label), "{{INTRO}}": esc(intro), "{{NAV}}": site_nav("/"), "{{AFTER}}": "",
                 "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(jsonld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    return out


# ---------- Dashboards for /layoffs/ and /funding/ ----------
DASH_CSS = """
.dash{max-width:1000px;margin:1.25rem auto 0;padding:0 1.5rem}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem}
.tile{background:var(--bg-card);border:1px solid var(--border);border-radius:.625rem;padding:.875rem 1rem;display:flex;flex-direction:column;gap:.125rem;text-decoration:none;color:inherit;min-width:0}
a.tile:hover{border-color:var(--acc)}
.tile-val{font-size:1.625rem;font-weight:900;color:var(--acc);font-family:'SF Mono','Cascadia Code',monospace;line-height:1.15;letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tile-lbl{font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;font-weight:600}
.tile-sub{font-size:.8125rem;color:var(--text-dim)}
.tile.txt .tile-val{font-size:1.25rem;white-space:normal;line-height:1.25;padding:.25rem 0}
.tile.hero{background:linear-gradient(135deg,var(--acc-dim),var(--bg-card) 70%)}
.tile.hero .tile-val{font-size:2.5rem}
.dash-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.75rem;margin-top:.75rem}
.dcard{background:var(--bg-card);border:1px solid var(--border);border-radius:.625rem;padding:1rem 1.125rem;min-width:0}
.dcard.wide{grid-column:1/-1}
.dcard h2{font-size:.9375rem;font-weight:800;margin-bottom:.125rem}
.dcard .dnote{font-size:.8125rem;color:var(--text-dim);margin-bottom:.75rem}
.vbars{display:flex;align-items:flex-end;gap:.375rem;height:170px;padding-top:1.25rem}
.vbar{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;min-width:0}
.vbar-track{flex:1;width:100%;display:flex;align-items:flex-end;position:relative}
.vbar-fill{width:100%;height:var(--h);min-height:2px;background:linear-gradient(180deg,var(--acc),var(--acc2));border-radius:.25rem .25rem 0 0;position:relative}
.vbar-fill b{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);font-size:.6875rem;font-weight:700;color:var(--text);white-space:nowrap;padding-bottom:.125rem;font-family:'SF Mono','Cascadia Code',monospace}
.vbar-lbl{font-size:.6875rem;color:var(--text-dim);margin-top:.375rem;white-space:nowrap;text-align:center;line-height:1.2;font-family:'SF Mono','Cascadia Code',monospace}
.vbar.now .vbar-fill{box-shadow:0 0 0 2px var(--acc-dim)}
.vbar.now .vbar-lbl{color:var(--acc);font-weight:700}
.hbars{display:flex;flex-direction:column;gap:.5rem;list-style:none}
.hbar{display:grid;grid-template-columns:minmax(0,9.5rem) minmax(0,1fr) auto;align-items:center;gap:.625rem;font-size:.875rem;text-decoration:none;color:var(--text)}
a.hbar:hover .hbar-name{color:var(--acc)}
.hbar-name{min-width:0;line-height:1.25;overflow-wrap:break-word}
.hbar-track{display:block;height:.625rem;background:#1c1c1f;border-radius:1rem;overflow:hidden}
.hbar-fill{display:block;height:100%;width:var(--w);min-width:3px;background:linear-gradient(90deg,var(--acc2),var(--acc));border-radius:1rem}
.hbar-val{font-family:'SF Mono','Cascadia Code',monospace;font-size:.8125rem;color:var(--text-muted);text-align:right;min-width:3.5rem}
.recent{list-style:none;display:flex;flex-direction:column}
.recent li{display:flex;justify-content:space-between;gap:.75rem;padding:.5rem 0;border-bottom:1px solid var(--border);font-size:.875rem}
.recent li:last-child{border-bottom:0}
.recent a{color:var(--text);text-decoration:none;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.recent a:hover{color:var(--acc)}
.recent span{color:var(--text-dim);font-family:'SF Mono','Cascadia Code',monospace;font-size:.8125rem;white-space:nowrap}
.recent em{font-style:normal;color:var(--acc);font-weight:700}
.lctrl{max-width:1000px;margin:1.75rem auto 0;padding:0 1.5rem;display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;position:sticky;top:0;z-index:5;background:var(--bg);padding-top:.625rem;padding-bottom:.625rem;border-bottom:1px solid var(--border)}
.lctrl h2{font-size:1.125rem;font-weight:800;width:100%;margin-bottom:.125rem}
.lsearch{flex:1 1 220px;min-width:0;height:44px;background:var(--bg-card);border:1px solid var(--border);border-radius:.5rem;color:var(--text);padding:0 .875rem;font-size:16px}
.lsearch:focus{outline:none;border-color:var(--acc)}
.lsort{height:44px;background:var(--bg-card);border:1px solid var(--border);border-radius:.5rem;color:var(--text);padding:0 .625rem;font-size:.875rem}
.chips{display:flex;gap:.375rem;flex-wrap:wrap;width:100%}
.chipf{height:36px;padding:0 .875rem;border-radius:2rem;border:1px solid var(--border);background:var(--bg-card);color:var(--text-muted);font-size:.8125rem;cursor:pointer;font-family:inherit}
.chipf:hover{color:var(--text)}
.chipf.on{background:var(--acc-dim);border-color:var(--acc);color:var(--acc);font-weight:700}
.chipf small{color:var(--text-muted);margin-left:.25rem;font-weight:400}
.chipf:hover small,.chipf.on small{color:inherit}
.lcount{font-size:.8125rem;color:var(--text-dim);width:100%}
.list .empty{text-align:center;color:var(--text-dim);padding:2rem 0}
.rank{font-family:'SF Mono','Cascadia Code',monospace;color:var(--text-dim);font-size:.8125rem;margin-right:.125rem;font-weight:600}
.list.unranked .rank{display:none}
.layoff-row:target,.fund-row:target{border-color:var(--acc)}
@media(min-width:601px){.layoff-row,.fund-row{scroll-margin-top:calc(var(--lctrl-h,240px) + .75rem)}}
.to-filters{position:fixed;right:1rem;bottom:1rem;z-index:50;width:44px;height:44px;border-radius:50%;border:1px solid var(--border);background:var(--bg-card);color:var(--text);font-size:1.125rem;line-height:1;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,.45);font-family:inherit}
.to-filters:hover{border-color:var(--acc);color:var(--acc)}
.badge-new{display:inline-block;background:var(--acc);color:#09090b;font-size:.625rem;font-weight:800;padding:.0625rem .375rem;border-radius:.25rem;margin-left:.375rem;vertical-align:middle;letter-spacing:.04em}
.mchip{color:var(--text-muted);background:#1c1c1f;padding:.125rem .5rem;border-radius:.25rem;text-decoration:none}
a.mchip:hover{color:var(--acc)}
@media(max-width:700px){.dash-grid{grid-template-columns:1fr}.dcard.wide{grid-column:auto}}
@media(max-width:600px){.dash,.lctrl{padding-left:.75rem;padding-right:.75rem}.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.tile{padding:.75rem}.tile-val{font-size:1.25rem}.tile.hero .tile-val{font-size:1.5rem}.tile.txt .tile-val{font-size:1rem}.tile-sub{font-size:.75rem}.hbar{grid-template-columns:minmax(0,7rem) minmax(0,1fr) auto;font-size:.8125rem}.vbars{height:140px;gap:.25rem}.vbar-fill b{font-size:.625rem}.vbar-lbl{font-size:.625rem}.lsort{flex:1 1 100%}.lctrl{position:static}.to-filters.visible{display:flex}}
@media(max-width:380px){.vbar-fill b{display:none}}
"""

DASH_JS = """<script>
(function(){
  var list=document.querySelector('.list[data-sortable]'); if(!list) return;
  var rows=[].slice.call(list.querySelectorAll('[data-sort-row]'));
  var q=document.querySelector('.lsearch'), s=document.querySelector('.lsort'), chips=[].slice.call(document.querySelectorAll('.chipf')), cnt=document.querySelector('.lcount');
  var empty=document.createElement('p'); empty.className='empty'; empty.textContent='Nothing matches. Try another search or filter.'; empty.hidden=true; list.appendChild(empty);
  var filt='all';
  function apply(push){
    var term=(q.value||'').trim().toLowerCase(), key=s.value, n=0;
    var keyed=rows.map(function(r,i){return {r:r,i:i}});
    var parts=key.split(':'), f=parts[0], dir=parts[1]==='asc'?1:-1;
    keyed.sort(function(a,b){var x=a.r.dataset[f],y=b.r.dataset[f]; if(f==='name') return x.localeCompare(y)*dir; x=parseFloat(x)||0; y=parseFloat(y)||0; return x===y? a.i-b.i : (x-y)*dir;});
    keyed.forEach(function(o){ var r=o.r, ok=(filt==='all'||(' '+r.dataset.f+' ').indexOf(' '+filt+' ')>-1)&&(!term||r.dataset.text.indexOf(term)>-1); r.hidden=!ok; if(ok){n++;} list.insertBefore(r,empty); });
    empty.hidden=n>0; cnt.textContent='Showing '+n+' of '+rows.length;
    list.classList.toggle('unranked', key!==s.options[0].value);  // #N badges are rank by the default sort only
    if(push){ try{ var u=new URL(location.href); term?u.searchParams.set('q',term):u.searchParams.delete('q'); key!==s.options[0].value?u.searchParams.set('sort',key):u.searchParams.delete('sort'); filt!=='all'?u.searchParams.set('f',filt):u.searchParams.delete('f'); history.replaceState(null,'',u.pathname+u.search+u.hash);}catch(e){} }
  }
  chips.forEach(function(c){c.addEventListener('click',function(){filt=c.dataset.f; chips.forEach(function(x){var on=x===c; x.classList.toggle('on',on); x.setAttribute('aria-pressed',on)}); apply(true);});});
  q.addEventListener('input',function(){apply(true)}); s.addEventListener('change',function(){apply(true)});
  try{ var p=new URLSearchParams(location.search); if(p.get('q')) q.value=p.get('q'); if(p.get('sort')&&[].some.call(s.options,function(o){return o.value===p.get('sort')})) s.value=p.get('sort');
    if(p.get('f')){ chips.forEach(function(c){ if(c.dataset.f===p.get('f')){ filt=c.dataset.f; chips.forEach(function(x){x.classList.toggle('on',x===c); x.setAttribute('aria-pressed',x===c)}); } }); } }catch(e){}
  apply(false);
  // #anchor targets: keep them clear of the sticky bar, and un-filter the list if the target row is hidden
  var bar=document.querySelector('.lctrl'), root=document.documentElement;
  function barH(){ if(bar) root.style.setProperty('--lctrl-h', bar.offsetHeight+'px'); }
  barH(); if(window.ResizeObserver&&bar) new ResizeObserver(barH).observe(bar);
  function unhide(id){ var el=null; try{ el=id&&document.getElementById(decodeURIComponent(id)); }catch(e){}
    if(!el||!el.hasAttribute('data-sort-row')||!el.hidden) return null;
    q.value=''; filt='all'; chips.forEach(function(x){var on=x.dataset.f==='all'; x.classList.toggle('on',on); x.setAttribute('aria-pressed',on)}); apply(true); return el; }
  document.addEventListener('click',function(e){ var a=e.target.closest&&e.target.closest('a[href^="#"]'); if(a) unhide(a.getAttribute('href').slice(1)); });
  window.addEventListener('hashchange',function(){ var el=unhide(location.hash.slice(1)); if(el) el.scrollIntoView(); });
  if(location.hash){ var t=unhide(location.hash.slice(1)); if(t) requestAnimationFrame(function(){ t.scrollIntoView(); }); }
  // phones: the filter bar is not sticky there, so offer a way back to it from deep in the list
  if(bar){
    var btn=document.createElement('button'); btn.type='button'; btn.className='to-filters'; btn.setAttribute('aria-label','Back to filters'); btn.title='Back to filters'; btn.textContent='↑';
    btn.addEventListener('click',function(){ var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches; bar.scrollIntoView({behavior:reduce?'auto':'smooth',block:'start'}); });
    document.body.appendChild(btn);
    var tick=false; function vis(){ tick=false; btn.classList.toggle('visible', bar.getBoundingClientRect().bottom<0); }
    window.addEventListener('scroll',function(){ if(!tick){ tick=true; requestAnimationFrame(vis); } },{passive:true}); vis();
  }
})();
</script>"""


def dash_tile(val, label, sub="", href=None, hero=False, txt=False):
    tag = f'a href="{href}"' if href else "div"
    cls = "tile" + (" hero" if hero else "") + (" txt" if txt else "")
    return (f'<{tag} class="{cls}"><span class="tile-lbl">{label}</span><span class="tile-val">{val}</span>'
            + (f'<span class="tile-sub">{sub}</span>' if sub else "") + f'</{tag.split()[0]}>')


def dash_vbars(items, now_label=None):
    mx = max((v for _, v, _ in items), default=1) or 1
    return '<div class="vbars" role="img" aria-label="' + esc(", ".join(f"{l}: {d or 0}" for l, _, d in items)) + '">' + "".join(
        f'<div class="vbar{" now" if l == now_label else ""}"><div class="vbar-track"><div class="vbar-fill" style="--h:{v / mx * 100:.1f}%">'
        f'{f"<b>{d}</b>" if v else ""}</div></div><span class="vbar-lbl">{esc(l).replace(" ", "<br>")}</span></div>' for l, v, d in items) + "</div>"


def dash_hbars(items):
    mx = max((v for _, v, _, _ in items), default=1) or 1
    out = []
    for l, v, d, href in items:
        tag = f'a class="hbar" href="{href}"' if href else 'div class="hbar"'
        out.append(f'<li><{tag}><span class="hbar-name" title="{esc(l)}">{esc(l)}</span><span class="hbar-track"><span class="hbar-fill" style="--w:{v / mx * 100:.1f}%"></span></span>'
                   f'<span class="hbar-val">{d}</span></{tag.split()[0]}></li>')
    return '<ol class="hbars">' + "".join(out) + "</ol>"


def dash_card(title, note, body, wide=False):
    return f'<section class="dcard{" wide" if wide else ""}"><h2>{title}</h2>' + (f'<p class="dnote">{note}</p>' if note else "") + body + "</section>"


def dash_controls(title, placeholder, sorts, chips):
    opts = "".join(f'<option value="{v}">{esc(l)}</option>' for v, l in sorts)
    ch = "".join(f'<button type="button" class="chipf{" on" if i == 0 else ""}" data-f="{v}" aria-pressed="{"true" if i == 0 else "false"}">{esc(l)}{f"<small>{n}</small>" if n is not None else ""}</button>'
                 for i, (v, l, n) in enumerate(chips))
    return (f'<div class="lctrl" role="search"><h2 id="list">{title}</h2>'
            f'<input class="lsearch" type="search" placeholder="{esc(placeholder)}" aria-label="{esc(placeholder)}" autocomplete="off">'
            f'<select class="lsort" aria-label="Sort by">{opts}</select><div class="chips" role="group" aria-label="Filter">{ch}</div>'
            f'<p class="lcount" aria-live="polite"></p></div>')


def fmt_money_m(m):
    if m >= 1000:
        return f"${m / 1000:.1f}B".replace(".0B", "B")
    if m >= 1:
        return f"${m:,.0f}M"
    return f"${m * 1000:,.0f}K"


def fmt_k(n):
    if n >= 1000:
        return f"{n / 1000:.1f}k".replace(".0k", "k")
    return str(n)


# ---------- /will-ai-take-my-job/: the AI job risk test ----------
# Search aliases for the SOC titles people actually type ("programmer", "nurse"), comma-separated: the search
# ranks a query that equals a whole alias first, so each comma-separated phrase is one thing a person might type.
JOB_ALIASES = {
    "15-1252": "software engineer, software developer, developer, engineer, programmer, coder, backend, back end, frontend, front end, full stack, game developer, prompt engineer",
    "15-1253": "qa, tester, quality assurance, test engineer",
    "15-1251": "programmer, coder",
    "15-1254": "web developer, frontend",
    "15-1255": "ux designer, ui designer, product designer, web designer",
    "29-1141": "nurse, rn, registered nurse",
    "25-2021": "teacher, primary school teacher, elementary teacher",
    "25-2031": "teacher, high school teacher, secondary teacher",
    "23-1011": "lawyer, attorney, solicitor",
    "13-2011": "accountant, auditor, cpa",
    "27-1024": "graphic designer, designer",
    "53-3032": "truck driver, driver, trucker, lorry driver, hgv driver",
    "53-3054": "taxi driver, uber driver, lyft driver, rideshare driver",
    "53-3033": "delivery driver, van driver",
    "41-2011": "cashier, checkout",
    "41-2031": "sales, sales associate, retail sales, shop assistant, store associate",
    "35-2014": "cook, line cook",
    "35-3023": "barista",
    "47-2111": "electrician",
    "47-2152": "plumber",
    "29-1215": "doctor, physician, gp, family doctor",
    "29-1051": "pharmacist",
    "13-1071": "hr, recruiter, human resources, talent acquisition",
    "13-1161": "marketing, marketing specialist, marketer, seo, digital marketing, growth marketing, market research, social media, content creator, influencer",
    "11-2021": "marketing manager, head of marketing, cmo",
    "15-2051": "data scientist, data analyst, analytics, machine learning, ml engineer, ai engineer, data engineer",
    "15-2041": "statistician",
    "15-1211": "analyst, business analyst, systems analyst, it analyst",
    "15-1212": "cybersecurity, security analyst, infosec",
    "15-1232": "it support, help desk, tech support",
    "15-1244": "sysadmin, system administrator, devops, network admin",
    "43-6014": "secretary, admin assistant, administrative assistant, office assistant, virtual assistant, va",
    "43-6011": "executive assistant, ea, pa, personal assistant",
    "43-4171": "receptionist, front desk",
    "43-9021": "data entry, typist",
    "43-3031": "bookkeeper, accounting clerk",
    "43-3071": "bank teller, teller",
    "43-1011": "office manager, office supervisor",
    "23-2011": "paralegal, legal assistant",
    "27-3023": "journalist, reporter, news",
    "27-3043": "writer, author, copywriter, content writer, blogger, content creator",
    "27-3042": "technical writer, documentation",
    "27-3091": "translator, interpreter, localization",
    "27-3041": "editor, copy editor",
    "27-3031": "pr, public relations, communications, comms",
    "13-2052": "financial advisor, wealth manager, financial planner",
    "13-2051": "financial analyst, investment analyst, equity research",
    "41-9022": "real estate agent, realtor, estate agent",
    "11-1021": "manager, general manager, operations manager, coo",
    "11-3021": "it manager, cto, engineering manager, head of engineering",
    "11-3031": "cfo, finance manager, finance director, finance",
    "11-2022": "sales manager, head of sales",
    "41-4012": "sales rep, account executive, salesperson, b2b sales",
    "41-3091": "sales representative, saas sales, account executive, account manager",
    "13-1082": "project manager, scrum master, program manager, product manager",
    "27-1014": "animator, vfx, 3d artist, motion designer",
    "27-4021": "photographer",
    "29-1123": "physiotherapist, physical therapist",
    "31-1131": "nursing assistant, care assistant, caregiver, cna",
    "33-3051": "police officer, cop",
    "33-2011": "firefighter",
    "35-3031": "waiter, waitress, server",
    "37-2011": "janitor, cleaner",
    "49-3023": "mechanic, car mechanic, auto technician",
    "53-7062": "warehouse worker, laborer, mover",
    "13-1111": "consultant, management consultant, strategy consultant",
    "17-2051": "civil engineer",
    "17-2141": "mechanical engineer",
    "17-1011": "architect",
    "13-2072": "loan officer, mortgage advisor",
    "13-2053": "underwriter, insurance underwriter",
    "25-9045": "teaching assistant, ta, teacher assistant, teacher aide",
    "39-9011": "nanny, childcare, babysitter",
    "39-5012": "hairdresser, barber, stylist",
    "43-4051": "customer service, support agent, call center, customer support, customer success",
    "41-9041": "telemarketer, cold caller, sdr, bdr",
    "11-1011": "ceo, founder, chief executive, entrepreneur, business owner, self employed",
    "11-9032": "principal, school principal, head teacher",
    "13-1041": "compliance officer",
    "13-2041": "credit analyst, risk analyst, fraud analyst",
    "11-3121": "hr manager, people manager, head of people",
    "43-3051": "payroll",
    "11-9111": "healthcare manager, hospital administrator",
    "29-1292": "dental hygienist",
    "27-2012": "producer, director, film director",
    "27-1011": "art director, creative director",
    "21-1018": "therapist, counselor, mental health",
    "19-3033": "psychologist",
    "13-1151": "trainer, learning and development, l&d",
    "15-1242": "dba, database administrator",
    "13-1081": "logistics, supply chain",
    "27-3011": "radio dj, broadcaster, presenter",
}
POPULAR_JOBS = [["15-1252", "Software developer"], ["43-4051", "Customer service"], ["13-1161", "Marketing"], ["13-2011", "Accountant"], ["27-1024", "Graphic designer"],
                ["29-1141", "Nurse"], ["25-2031", "Teacher"], ["27-3043", "Writer"], ["13-1071", "HR / recruiter"], ["53-3032", "Truck driver"]]


def soc_role(soc):
    """Map a SOC code onto the role tags used in layoffs.json (roles.json)."""
    exact = {
        "43-4051": "customer-support", "41-9041": "sales", "27-3091": "translation", "13-1041": "compliance",
        "27-3041": "content", "27-3042": "content", "27-3043": "content", "27-3023": "content", "27-3031": "marketing", "43-9081": "content",
        "11-2011": "marketing", "11-2021": "marketing", "11-2032": "marketing", "11-2033": "marketing", "13-1161": "marketing", "41-3011": "ad-operations",
        "13-2011": "finance", "43-3031": "finance", "43-3051": "finance", "13-2051": "finance", "11-3031": "finance",
        "13-1071": "hr", "11-3121": "hr", "13-1141": "hr", "43-4161": "hr", "13-1151": "hr",
        "13-2041": "risk-fraud", "13-2061": "risk-fraud", "13-2053": "risk-fraud", "13-1031": "risk-fraud",
        "13-1111": "professional-services", "13-1081": "operations", "11-3013": "operations", "11-3071": "operations", "11-1021": "middle-management",
        "13-1082": "product", "15-1255": "product",
    }
    # Codes the prefix fallbacks below would pair with unrelated layoffs (a CEO is not middle management, a mail
    # carrier is not Oracle's operations cut, a judge is not a law-firm job): no role, so the page says "0 so far".
    exact.update(dict.fromkeys([
        "11-1011", "11-1031", "11-9013", "11-9021", "11-9031", "11-9032", "11-9033", "11-9051", "11-9071", "11-9072", "11-9081",
        "11-9131", "11-9151", "11-9161", "11-9171", "11-9179", "41-9011", "41-9012", "43-5021", "43-5031", "43-5041", "43-5051",
        "43-5052", "43-5053", "43-5111", "23-1012", "23-1021", "23-1022", "23-1023"], ""))
    if soc in exact:
        return exact[soc]
    if soc.startswith(("15-125",)):
        return "engineering"
    if soc.startswith("15-12"):
        return "it"
    if soc.startswith("23-"):
        return "legal"
    if soc.startswith("41-") and not soc.startswith(("41-2",)):
        return "sales"
    if soc.startswith("43-5"):
        return "operations"
    if soc.startswith("43-"):
        return "admin"
    if soc.startswith("11-"):
        return "middle-management"
    return ""


def render_job_risk(ldata):
    import bisect
    import csv
    roles_map = json.loads((ROOT / "roles.json").read_text())
    rows = list(csv.DictReader((ROOT / "data" / "microsoft-ai-applicability-scores.csv").open()))
    rows = [(r["SOC Code"], r["title"], float(r["ai_applicability_score"])) for r in rows]
    n = len(rows)
    scores_sorted = sorted(r[2] for r in rows)
    # share of the n occupations with a strictly lower score, rounded down: at most 99, so never "100% are less exposed"
    pct = {r[0]: 100 * bisect.bisect_left(scores_sorted, r[2]) // n for r in rows}

    def job_alias(soc):  # every postsecondary field answers to "professor" (no "teacher": the titles already say Teachers)
        a = JOB_ALIASES.get(soc, "")
        return (a + ", " if a else "") + "professor, lecturer, university lecturer, college professor, faculty, academic" if soc.startswith("25-1") else a
    by_role = {}
    for l in ldata:
        for r in l.get("roleTags", []):
            if r != "various":
                by_role.setdefault(r, []).append(l)
    role_info = {r: {"label": roles_map.get(r, r), "jobs": sum(x["jobs"] for x in ls), "n": len(ls), "page": len(ls) >= 2,
                     "top": [[x["company"], x["jobs"], fmt_month(x["date"])] for x in sorted(ls, key=lambda x: -x["jobs"])[:4]]}
                 for r, ls in by_role.items()}
    occ = [[soc, title, round(score, 3), pct[soc], soc_role(soc) if soc_role(soc) in role_info else "", job_alias(soc)]
           for soc, title, score in sorted(rows, key=lambda r: r[1])]
    missing = [s for s in list(JOB_ALIASES) + [j for j, _ in POPULAR_JOBS] if s not in pct]
    if missing:
        print(f"⚠️  job risk: aliases for unknown SOC codes {missing}")
    top = sorted(rows, key=lambda r: -r[2])
    bottom = sorted(rows, key=lambda r: r[2])

    def table(items, start=1):
        return ('<table class="rank-table"><thead><tr><th>#</th><th>Occupation</th><th>AI applicability</th><th></th></tr></thead><tbody>'
                + "".join(f'<tr><td>{start + k}</td><td>{esc(t)}</td><td><span class="mini"><span style="--w:{s / top[0][2] * 100:.0f}%"></span></span>{s:.2f}</td>'
                          f'<td><a href="#test" data-job="{soc}" rel="nofollow">Test →</a></td></tr>' for k, (soc, t, s) in enumerate(items))
                + "</tbody></table>")

    all_rows = "".join(f'<tr><td>{k + 1}</td><td>{esc(t)}</td><td>{s:.2f}</td><td><a href="#test" data-job="{soc}" rel="nofollow">Test →</a></td></tr>' for k, (soc, t, s) in enumerate(top))
    total_jobs = sum(l["jobs"] for l in ldata)
    url = SITE_URL + "will-ai-take-my-job/"
    faq = [
        ("Will AI take my job?", f"Probably not all of it, and not all at once, but some jobs are far more exposed than others. Microsoft's analysis of 200,000 real Copilot conversations found the highest AI overlap in interpreters and translators, writers, customer service representatives and sales roles, and almost none in hands-on work such as dredge operators, roofers or nursing assistants. Meanwhile {len({company_key(l['company']) for l in ldata})} companies have already cut {total_jobs:,} jobs while explicitly blaming AI. The test on this page combines both with how you work."),
        ("Which jobs are most at risk from AI?", "By Microsoft's AI applicability score, the most exposed occupations are " + ", ".join(t for _, t, _ in top[:6]) + ". Among real layoffs where employers named AI as the reason, customer support is hit hardest by far, followed by operations, software engineering and sales."),
        ("Which jobs are safest from AI?", "Jobs built on physical, on-site work in unpredictable environments score lowest: " + ", ".join(t for _, t, _ in bottom[:6]) + ". Work that needs a licence, legal accountability or in-person trust is also slower to automate."),
        ("Are young workers more at risk?", "So far, yes. Stanford's Digital Economy Lab found that by mid-2026 employment for 22- to 25-year-olds in the most AI-exposed occupations was about 19% below where it would have been had it kept pace with less-exposed jobs, mostly because of fewer hires rather than firings. Experienced workers show no comparable drop."),
        ("How accurate is this AI job risk score?", "It is an informed estimate rather than a prediction. The occupation part is Microsoft's measured overlap between AI and the tasks of each job, which its authors stress is not the same as displacement. The personal part reflects findings on early-career exposure, codified versus tacit knowledge, physical work and employer signals. Use it to see where you are exposed, and don't read it as a verdict."),
    ]
    faq_html = "".join(f'<details class="faq"><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)
    jsonld = {"@context": "https://schema.org", "@graph": [
        webpage_node(url, "Will AI Take My Job? The AI Job Risk Test", f"Free AI job risk test: score your job against {n} occupations using Microsoft's AI applicability data and {total_jobs:,} real AI layoffs.", lm(["layoffs.json", "job-risk-template.html", "data/microsoft-ai-applicability-scores.csv"])),
        {"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "Will AI take my job?", "item": url}]},
    ]}
    tpl = (ROOT / "job-risk-template.html").read_text()
    out = (tpl.replace("{{JSONLD}}", json.dumps(jsonld, indent=1))
           .replace("{{OCC_JSON}}", json.dumps(occ, separators=(",", ":")).replace("</", "<\\/"))
           .replace("{{ROLE_JSON}}", json.dumps(role_info, separators=(",", ":")).replace("</", "<\\/"))
           .replace("{{POPULAR_JSON}}", json.dumps(POPULAR_JOBS))
           .replace("{{TOP_TABLE}}", table(top[:20]))
           .replace("{{BOTTOM_TABLE}}", table(bottom[:20]))
           .replace("{{ALL_ROWS}}", all_rows)
           .replace("{{FAQ}}", faq_html)
           .replace("{{N_OCC}}", str(n))
           .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
           .replace("{{TOTAL_COMPANIES}}", str(len({company_key(l["company"]) for l in ldata})))
           .replace("{{FOOTER_LINKS}}", footer_links())
           .replace("{{LAST_UPDATED}}", fmt_date(lm(["layoffs.json"]))))
    publish("will-ai-take-my-job", out)
    print(f"Built will-ai-take-my-job/ with {n} occupations")


def render_jobs_pages(ldata, list_tpl):
    """/jobs/ and /jobs/<role>/: layoffs re-indexed by the roles AI replaced.

    A layoff's job count is the company-wide figure, so it is counted in full under every role it names:
    role figures are "jobs cut in layoffs that named this role", never "jobs in this role"."""
    roles = json.loads((ROOT / "roles.json").read_text())
    total_jobs = sum(l["jobs"] for l in ldata)
    n_companies = len({company_key(l["company"]) for l in ldata})
    this_year = str(datetime.utcnow().year)
    by_role = {}
    for l in ldata:
        for r in l.get("roleTags", ["various"]):
            by_role.setdefault(r, []).append(l)
    # rank by how many layoffs named the role (summed totals overweight whichever roles the mega-layoffs listed)
    ranked = sorted(by_role.items(), key=lambda kv: (-len(kv[1]), -sum(x["jobs"] for x in kv[1])))
    page_roles = [(r, rows) for r, rows in ranked if r != "various" and len(rows) >= 2]
    pages = [r for r, _ in page_roles]
    for r, rows in page_roles:
        label = roles.get(r, r); lc = lc_label(label); L = len(rows); jobs = sum(x["jobs"] for x in rows)
        names = list(dict.fromkeys(company_key(x["company"]) for x in sorted(rows, key=lambda x: -x["jobs"])))
        n = len(names)
        rows = sorted(rows, key=lambda x: -x["jobs"])
        url = f"{SITE_URL}jobs/{r}/"
        title = f"{label} jobs replaced by AI: {L} layoffs"

        def meta_for(k):
            who = f"{L} rounds at {names[0]}" if n == 1 else ", ".join(names[:k]) + (" and more" if k < n else "")
            return f"{L} AI-blamed layoffs named {lc} roles: {who}. {jobs:,} jobs cut in those layoffs (company-wide totals), each sourced."
        meta = next((meta_for(k) for k in range(min(n, 4), 0, -1) if len(meta_for(k)) <= 155), meta_for(1))
        if len(meta) > 155:
            meta = meta[:152].rsplit(" ", 1)[0] + "…"
        by_date = sorted(rows, key=lambda x: x["date"])
        big = rows[0]
        ytd = sum(1 for x in rows if x["date"][:4] == this_year)
        intro = (f"{L} layoffs where the company blamed AI named {lc} among the roles cut"
                 + ("" if n == L else f", all at {names[0]}" if n == 1 else f", at {n} companies") + ". "
                 + f"Together those layoffs cut {jobs:,} jobs. That is the company-wide total, not only {lc} roles, so figures for different roles overlap. "
                 + f"The largest was {company_key(big['company'])} ({big['jobs']:,} jobs, {fmt_month(big['date'])}); "
                 + f"the first was {company_key(by_date[0]['company'])} in {fmt_month(by_date[0]['date'])} and the latest {company_key(by_date[-1]['company'])} in {fmt_month(by_date[-1]['date'])}. "
                 + (f"{ytd} of the {L} came in {this_year}. " if ytd else "")
                 + "Largest first; every row links to its entry and source on the layoffs tracker.")
        rhtml = "".join(f'<a class="row" href="/layoffs/#{slugify(x["company"])}"><span><b>{esc(x["company"])}</b><small>{esc(x["roles"])}</small></span><span class="when">{x["jobs"]:,} · {x["date"][:7]}</span></a>' for x in rows)
        siblings = "".join(f'<a href="/jobs/{o}/">{esc(roles.get(o, o))} <small>{len(orows)}</small></a>' for o, orows in page_roles if o != r)
        after = f'<nav class="siblings" aria-label="Other roles"><h2>Other roles hit by AI layoffs</h2><div>{siblings}</div></nav>' if siblings else ""
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "Jobs replaced by AI", "item": SITE_URL + "jobs/"}, {"@type": "ListItem", "position": 3, "name": label, "item": url}]},
            webpage_node(url, title, meta, lm(["layoffs.json"]), {"@type": "CollectionPage"}),
            {"@type": "ItemList", "numberOfItems": L, "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": f'{x["company"]}: {x["jobs"]:,} jobs', "url": SITE_URL + "layoffs/#" + slugify(x["company"])} for k, x in enumerate(rows)]}]}
        out = list_tpl
        for k, v in {"{{TITLE}}": esc(title + " | Killed by AI") if len(title) <= 45 else esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": f'<a href="/jobs/">Jobs replaced by AI</a> › {esc(label)}',
                     "{{H1}}": f"{esc(label)}: jobs replaced by AI", "{{INTRO}}": esc(intro), "{{ROWS}}": rhtml, "{{AFTER}}": after, "{{NAV}}": site_nav("/layoffs/"),
                     "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
            out = out.replace(k, v)
        d = ROOT / "jobs" / r; d.mkdir(parents=True, exist_ok=True); (d / "index.html").write_text(out)
    # index
    url = SITE_URL + "jobs/"
    rhtml = "".join(f'<a class="row" href="/jobs/{r}/"><span><b>{esc(roles.get(r, r))}</b><small>{len({company_key(x["company"]) for x in rows})} companies · {sum(x["jobs"] for x in rows):,} jobs in those layoffs</small></span><span class="when">{len(rows)} layoffs</span></a>' for r, rows in page_roles)
    title = f"Jobs Replaced by AI: {total_jobs:,} Layoffs by Role | Killed by AI"
    meta = f"Which jobs AI is replacing: {total_jobs:,} jobs cut at {n_companies} companies that blamed AI, by role, including customer support, sales and engineering. Sourced."
    top_label = roles.get(pages[0], pages[0]) if pages else "Customer support"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "Jobs replaced by AI", "item": url}]},
        webpage_node(url, title, meta, lm(["layoffs.json"]), {"@type": "CollectionPage"}),
        {"@type": "ItemList", "numberOfItems": len(pages), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": roles.get(r, r), "url": f"{SITE_URL}jobs/{r}/"} for k, r in enumerate(pages)]}]}
    out = list_tpl
    for k, v in {"{{TITLE}}": esc(title), "{{META_DESC}}": esc(meta), "{{URL}}": url, "{{CRUMB}}": "Jobs replaced by AI",
                 "{{H1}}": "Jobs replaced by AI, by role", "{{INTRO}}": esc(f"The roles companies name when they blame layoffs on AI. {total_jobs:,} jobs across {n_companies} companies, re-indexed by the work that was replaced, most-named role first. {top_label} leads by a distance. Each layoff's job count is the company-wide total and is counted under every role it named, so role figures overlap; the per-company figures are on the layoffs tracker."),
                 "{{ROWS}}": rhtml, "{{AFTER}}": "", "{{NAV}}": site_nav("/layoffs/"), "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    d = ROOT / "jobs"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)
    return pages


def build_ics(cs_data):
    """deprecations.ics: subscribe to upcoming AI shutdowns in any calendar app."""
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
                      + "\r\nSUMMARY:" + ics_escape("🪦 Shutdown: " + c["name"]) + "\r\nDESCRIPTION:" + ics_escape(desc)
                      + "\r\nURL:" + SITE_URL + "coming-soon/#" + slugify(c["name"]) + "\r\nCATEGORIES:AI shutdown\r\nEND:VEVENT")
    return ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//Killed by AI//Upcoming AI shutdowns//EN\r\nCALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\n"
            "X-WR-CALNAME:Upcoming AI shutdowns | Killed by AI\r\nX-WR-CALDESC:Confirmed shutdown and deprecation dates for AI products and models. Source: killedbyai.net/coming-soon/\r\nREFRESH-INTERVAL;VALUE=DURATION:P1D\r\n"
            + "\r\n".join(events) + "\r\nEND:VCALENDAR\r\n")


def render_index_pages(data, killer_counts, list_tpl):
    """/dead/ (A-Z, every tombstone) and /killed-by/ (every killer with a page)."""
    az = sorted(data, key=lambda i: i["name"].lower())
    rows = "".join(f'<a class="row" href="{product_url(i)}"><span><b>{esc(i["name"])}</b><small>{esc(i["causeOfDeath"])} · {esc(killer_label(i["killedBy"]).replace("Killed", "killed", 1))}</small></span><span class="when">{i["dateClose"]}</span></a>' for i in az)
    url = SITE_URL + "dead/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "All tombstones", "item": url}]},
        webpage_node(url, f"All {len(data)} dead AI products, A-Z", "Every tombstone in the AI graveyard, alphabetically.", lm(["graveyard.json"]), {"@type": "CollectionPage"}),
        {"@type": "ItemList", "numberOfItems": len(data), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["name"], "url": product_url(i)} for k, i in enumerate(az)]}]}
    out = list_tpl
    for k, v in {"{{TITLE}}": f"All {len(data)} Dead AI Products, A-Z | Killed by AI", "{{META_DESC}}": esc(f"Every one of the {len(data)} tombstones in the AI graveyard, alphabetically: models, apps, services, startups and hardware, each with dates, cause of death and source."),
                 "{{URL}}": url, "{{CRUMB}}": "All tombstones", "{{H1}}": f"All {len(data)} tombstones, A-Z", "{{INTRO}}": esc("Every dead AI product tracked here, alphabetically. Each page has the launch and death dates, the cause, the killer, and a source."),
                 "{{NAV}}": site_nav("/"), "{{AFTER}}": "", "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
        out = out.replace(k, v)
    d = ROOT / "dead"; d.mkdir(exist_ok=True); (d / "index.html").write_text(out)

    killers = sorted([(k, n) for k, n in killer_counts.items() if n >= 2], key=lambda x: -x[1])
    rows = "".join(f'<a class="row" href="/killed-by/{killer_slug(k)}/"><span><b>{esc(k)}</b><small>{n} AI products killed{" · a cause, not a company" if k in KILLER_PROSE else ""}</small></span><span class="when">{n}</span></a>' for k, n in killers)
    url = SITE_URL + "killed-by/"
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": SITE_URL}, {"@type": "ListItem", "position": 2, "name": "By killer", "item": url}]},
        webpage_node(url, "Who kills the most AI products?", "AI product deaths by the company responsible.", lm(["graveyard.json"]), {"@type": "CollectionPage"})]}
    out = list_tpl
    for k, v in {"{{TITLE}}": "Who Kills the Most AI Products? | Killed by AI", "{{META_DESC}}": esc(f"AI product shutdowns by the company responsible. {killers[0][0]} leads with {killers[0][1]}. Every killer with two or more dead products has its own page."),
                 "{{URL}}": url, "{{CRUMB}}": "By killer", "{{H1}}": "Killed by whom?", "{{INTRO}}": esc(f"Killers ranked by how many AI products they have shut down. {killers[0][0]} leads with {killers[0][1]}; every killer with two or more kills has its own page listing them. A few are causes rather than companies: products that collapsed on their own, or were killed by the market or by reality."),
                 "{{NAV}}": site_nav("/"), "{{AFTER}}": "", "{{ROWS}}": rows, "{{FOOTER_LINKS}}": footer_links(), "{{JSONLD}}": json.dumps(ld, indent=2, ensure_ascii=False)}.items():
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
    <span class="card-lifespan">{y_open if y_open == y_close else f"{y_open}-{y_close}"}</span>
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
                "logo": {"@type": "ImageObject", "url": SITE_URL + "icon-512.png", "width": 512, "height": 512},
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
            webpage_node(SITE_URL, "Killed by AI: The AI Graveyard", f"{len(items)} dead AI products, each with dates, cause of death, killer and source.",
                         lm(["graveyard.json", "template.html"]), {"@type": "CollectionPage"}),
            {
                "@type": "Dataset",
                "@id": SITE_URL + "api/#graveyard",
                "name": "Killed by AI Graveyard",
                "description": "An open dataset of discontinued AI products, models, startups, and hardware: the casualties of the artificial intelligence gold rush.",
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
    sora_answer = (f"OpenAI shut down the Sora app on April 26, 2026: it cost about $1M a day in compute against fewer than 500K users, and a $1B Disney deal had collapsed. The API followed on September 24, 2026. "
                   f"Full timeline: <a href=\"{product_url(sora)}\">Sora AI shutdown</a>.") if sora else "OpenAI shut down Sora in April 2026 due to unsustainable compute costs."
    def link_for(slug, text):
        it = next((i for i in items if i.get("slug") == slug), None)
        return f'<a href="{product_url(it)}">{esc(text)}</a>' if it else esc(text)
    chatgpt_answer = ("No. ChatGPT itself is alive, but plenty of what shipped inside it is not: "
                      + ", ".join([link_for("chatgpt-plugins", "ChatGPT Plugins"), link_for("openai-gpt-store", "the GPT Store"), link_for("gpt-4o-chatgpt", "GPT-4o"),
                                   link_for("gpt-4-original", "the original GPT-4"), link_for("dall-e-gpt-in-chatgpt", "the DALL·E GPT")])
                      + '. Browse every OpenAI death on the <a href="/killed-by/openai/">OpenAI page</a>.')

    faqs = [
        {
            "q": "What is Killed by AI?",
            "a": f"Killed by AI is an open-source tracker of discontinued AI products, models, startups, and hardware. It currently documents {total} casualties of the artificial intelligence industry, including deprecated API models and billion-dollar startup failures."
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
            "a": f"{shortest['name']} lasted just {format_lifespan_long(shortest_days)}. {shortest['description']}"
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
      <title>{esc(item["name"])}: {esc(killer_label(item["killedBy"]))} ({item["dateClose"]})</title>
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
    <title>Killed by AI: The AI Graveyard</title>
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
    now = datetime.utcnow()
    current_year = now.year
    kills_this_year = years.get(current_year, 0)
    # Scale by elapsed days, not whole calendar months (Oct 7 is not 10/12 of the year). The floor keeps an
    # early-January rebuild from extrapolating one death into hundreds.
    days_in_year = 366 if calendar.isleap(current_year) else 365
    elapsed = max(now.timetuple().tm_yday, 31)
    per_day = kills_this_year / elapsed
    pace_per_month = round(per_day * days_in_year / 12, 1)
    projected = max(kills_this_year, round(per_day * days_in_year))
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
        s = item.get("slug") or slugify(name)   # the dead/<slug>/ directory the page is written to
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
                f"graveyard: '{name}' dies {item['dateClose']} (future); "
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

    for item in data:   # an alias dir would overwrite a live product page with a redirect stub
        for old in item.get("aliases", []):
            if old in slugs:
                warnings.append(f"graveyard: alias '{old}' of '{item.get('name')}' is used by both a live page and a redirect")

    graveyard_names = {i.get("name", "").lower() for i in data}
    for item in cs_data:
        name = item.get("name", "<unnamed>")
        if item.get("dateShutdown", "") < today:
            warnings.append(
                f"coming-soon: '{name}' died {item['dateShutdown']}; move it to graveyard.json"
            )
        if name.lower() in graveyard_names:
            warnings.append(f"coming-soon: '{name}' is already in the graveyard; remove one")
        elif not item.get("graveyardSlug") and not item.get("notInGraveyard"):
            # renamed duplicates: whole slug words in either direction ('Nano Banana' vs 'google-gemini-…-nano-banana')
            b = f"-{slugify(name)}-"
            hits = [g for g in slugs if b in f"-{g}-" or f"-{g}-" in b]
            if hits:
                warnings.append(f"coming-soon: '{name}' looks like graveyard entr{'y' if len(hits) == 1 else 'ies'} {', '.join(hits)}; "
                                f"remove one, or set graveyardSlug (related tombstone) / notInGraveyard: true")
        if item.get("graveyardSlug") and item["graveyardSlug"] not in slugs:
            warnings.append(f"coming-soon: '{name}' graveyardSlug '{item['graveyardSlug']}' matches no tombstone (would publish a 404 link)")

    layoff_keys = set(); anchors = {}
    for item in ldata:
        key = (item.get("company"), item.get("date"))
        if key in layoff_keys:
            warnings.append(
                f"layoffs: duplicate '{item.get('company')}' on {item.get('date')} (inflates the job total)"
            )
        layoff_keys.add(key)
        a = slugify(item.get("company", ""))
        if a in anchors:
            warnings.append(f"layoffs: '{anchors[a]}' and '{item.get('company')}' share the anchor #{a}; "
                            f"label the repeat with its year, e.g. '{company_key(item.get('company', ''))} ({item.get('date', '')[:4]})'")
        anchors[a] = item.get("company")

    return warnings


# Warnings that mean the published site would be wrong (duplicate pages/ids, a death in the future): fail the build.
HARD_WARNING = re.compile(r"duplicate|used by both|\(future\)|already in the graveyard|share the anchor")


RETIRED_TOMBSTONES = {  # slug -> coming-soon.json name it now redirects to
    "google-gemini-2-5-flash-image-nano-banana": 'Google Gemini 2.5 Flash Image ("Nano Banana")',
    "gemini-omni-flash-preview": "Gemini Omni Flash Preview & Veo 3.1 Previews",
    "gpt-4o-api-2024-05-13-2024-08-06": "OpenAI GPT-4, GPT-4 Turbo, GPT-3.5 Turbo, o1, o3-mini & o4-mini",
}

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
                "name": f'{l["company"]}: {l["jobs"]:,} jobs cut',
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
                    f"{total:,} jobs cut in {len(ldata)} layoffs at {len({company_key(l['company']) for l in ldata})} companies that explicitly cited AI, "
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
            webpage_node(SITE_URL + "layoffs/", "AI Layoffs Tracker", f"{total:,} jobs cut by AI at {len({company_key(l['company']) for l in ldata})} companies.", lm(["layoffs.json", "layoffs-template.html"]), {"@type": "CollectionPage"}),
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
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f"What is the shutdown date for {c['name']}?",
                "acceptedAnswer": {"@type": "Answer", "text": f"{c['name']}: scheduled shutdown on {fmt_date(c['dateShutdown'])} (announced {fmt_date(c['dateAnnounced'])}). Replacement: {c['replacement']}."}}
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
        "isBasedOn": SITE_URL + "api/",  # plain URL: a typed Dataset stub here is validated by Google as a second, incomplete Dataset
        "name": "Funding Burned by Failed AI Companies",
        "description": (
            f"${total_b} billion raised (venture, corporate and strategic funding) by {len(funded)} AI startups that shut down, "
            "were acqui-hired into oblivion, or ran out of money."
        ),
        "url": SITE_URL + "funding/",
        "keywords": "failed AI startups, AI startup failures, AI funding burned, AI bubble, failed self-driving companies, wasted venture capital",
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


def check_data(data):
    """Run validate() before anything is written, so a bad data commit fails without touching the built pages."""
    ldata = json.loads((ROOT / "layoffs.json").read_text()) if (ROOT / "layoffs.json").exists() else []
    cs_data = json.loads((ROOT / "coming-soon.json").read_text()) if (ROOT / "coming-soon.json").exists() else []
    warnings = validate(data, ldata, cs_data)
    if warnings:
        print(f"\n⚠️  {len(warnings)} data warning(s):")
        for w in warnings:
            print(f"   - {w}")
    else:
        print("✓ Data checks passed")
    hard = [w for w in warnings if HARD_WARNING.search(w)]
    if hard:
        print(f"\n✗ BUILD FAILED: {len(hard)} data error(s) would publish duplicate or premature pages; fix the data first.")
        raise SystemExit(1)
    # A scheduled death that is two weeks past its date and still has no tombstone is a content bug, not a warning.
    cutoff = (datetime.utcnow() - __import__("datetime").timedelta(days=14)).strftime("%Y-%m-%d")
    stale = [c["name"] for c in cs_data if c.get("dateShutdown", "") < cutoff]
    if stale:
        print(f"\n✗ BUILD FAILED: {len(stale)} coming-soon entr{'y is' if len(stale)==1 else 'ies are'} 14+ days past shutdown; migrate to graveyard.json: {', '.join(stale)}")
        raise SystemExit(1)


def main():
    data = json.loads((ROOT / "graveyard.json").read_text())
    data.sort(key=lambda i: (i["dateClose"], i.get("dateAdded", "")), reverse=True)
    check_data(data)
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
              .replace("{{YEAR_RANGE}}", f"{min_year}-{max_year}")
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
                  .replace("{{TOTAL_COMPANIES_LAYOFFS}}", str(len({company_key(l["company"]) for l in ldata}))))
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
    if (ROOT / "layoffs.json").exists():
        render_job_risk(json.loads((ROOT / "layoffs.json").read_text()))
    # Role pages that no longer qualify (fewer than 2 layoffs) would otherwise linger with stale numbers.
    for d in (ROOT / "jobs").iterdir() if (ROOT / "jobs").exists() else []:
        if d.is_dir() and d.name not in job_pages:
            shutil.rmtree(d)
    import embed
    embed.build_embeds(ROOT, SITE_URL, data, json.loads((ROOT / "layoffs.json").read_text()) if (ROOT / "layoffs.json").exists() else [],
                       json.loads((ROOT / "coming-soon.json").read_text()) if (ROOT / "coming-soon.json").exists() else [],
                       publish, site_nav, footer_links, product_url)
    killer_pages = []
    for killer, n in killer_counts.items():
        if n < 2:
            continue
        d = ROOT / "killed-by" / killer_slug(killer); d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_killer_page(killer, [i for i in data if i["killedBy"] == killer], list_tpl, len(data)))
        killer_pages.append(killer)
    # Tombstones published too early (the product turned out not to be dead yet) keep their URL as a redirect
    # to the matching Dying-soon card instead of 404ing or still claiming a death.
    for slug, cs_name in RETIRED_TOMBSTONES.items():
        if any(i.get("slug") == slug for i in data):
            continue
        d = ROOT / "dead" / slug; d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(REDIRECT_STUB.format(target=f"{SITE_URL}coming-soon/#{slugify(cs_name)}"))
    print(f"Built {len(ordered)} product pages and {len(killer_pages)} killer pages")
    (ROOT / "robots.txt").write_text(build_robots())
    (ROOT / "feed.xml").write_text(build_rss(data))

    # Build Employee Graveyard
    layoffs_path = ROOT / "layoffs.json"
    if layoffs_path.exists():
        layoffs = json.loads(layoffs_path.read_text())
        layoffs_template = (ROOT / "layoffs-template.html").read_text()
        roles_map = json.loads((ROOT / "roles.json").read_text())
        total_jobs = sum(l["jobs"] for l in layoffs)
        total_entries = len(layoffs)                                       # rows: "All 34 AI layoffs"
        total_companies = len({company_key(l["company"]) for l in layoffs})  # PayPal + PayPal (2026) = one company
        first_year = min(l["date"] for l in layoffs)[:4]
        layoffs_sorted = sorted(layoffs, key=lambda l: l["jobs"], reverse=True)
        max_jobs = layoffs_sorted[0]["jobs"] if layoffs_sorted else 1
        now = datetime.utcnow()
        this_year = str(now.year)

        by_role = {}
        for l in layoffs:
            for r in l.get("roleTags", []):
                by_role.setdefault(r, []).append(l)
        role_pages = {r for r, rows in by_role.items() if r != "various" and len(rows) >= 2}

        def role_chips(l):
            return " ".join(f'<a class="mchip" href="/jobs/{r}/">{esc(roles_map.get(r, r))}</a>' if r in role_pages else f'<span class="mchip">{esc(roles_map.get(r, r))}</span>'
                            for r in l.get("roleTags", []) if r != "various")

        def lrow(rank, l):
            fresh = (now - datetime.strptime(l["date"], "%Y-%m-%d")).days <= 45
            text = " ".join([l["company"], l["description"], l["roles"], " ".join(roles_map.get(r, r) for r in l.get("roleTags", []))]).lower()
            return f'''<article class="layoff-row" id="{slugify(l["company"])}" data-sort-row data-jobs="{l["jobs"]}" data-date="{l["date"].replace("-", "")}" data-name="{esc(l["company"].lower())}" data-f="{l["date"][:4]} {" ".join(l.get("roleTags", []))}" data-text="{esc(text)}">
  <div class="layoff-bar-wrap">
    <div class="layoff-bar" style="width: {l["jobs"] / max_jobs * 100:.1f}%"></div>
  </div>
  <div class="layoff-info">
    <div class="layoff-header">
      <h2 class="layoff-company"><span class="rank" title="Rank by jobs cut">#{rank}</span> {esc(l["company"])}{'<span class="badge-new">NEW</span>' if fresh else ""}</h2>
      <span class="layoff-count">{l["jobs"]:,}</span>
    </div>
    <p class="layoff-desc">{esc(l["description"])}</p>
    <div class="layoff-meta">
      <span class="layoff-date">{fmt_month(l["date"])}</span>
      {role_chips(l)}
      <a class="layoff-source" href="{esc(l["source"])}" target="_blank" rel="noopener">Source ↗</a>
    </div>
  </div>
</article>'''

        rows_html = "\n".join(lrow(k + 1, l) for k, l in enumerate(layoffs_sorted))

        by_year = {}
        by_year_n = {}
        by_year_c = {}
        for l in layoffs:
            y = l["date"][:4]
            by_year[y] = by_year.get(y, 0) + l["jobs"]
            by_year_n[y] = by_year_n.get(y, 0) + 1
            by_year_c.setdefault(y, set()).add(company_key(l["company"]))
        year_stats = " | ".join(f"{y}: {c:,}" for y, c in sorted(by_year.items()))
        year_table = ("<table class=\"year-table\"><thead><tr><th>Year</th><th>Layoffs</th><th>Jobs cut, AI cited</th></tr></thead><tbody>"
                      + "".join(f"<tr><td>{y}</td><td>{by_year_n[y]}</td><td>{c:,}</td></tr>" for y, c in sorted(by_year.items()))
                      + f"<tr><th>Total</th><th>{len(layoffs)}</th><th>{total_jobs:,}</th></tr></tbody></table>")
        largest = sorted([l for l in layoffs if l["date"].startswith(this_year)], key=lambda l: -l["jobs"])[:5]
        largest_html = "<ol class=\"largest\">" + "".join(f'<li><a href="#{slugify(l["company"])}"><b>{esc(l["company"])}</b>: {l["jobs"]:,} jobs</a> <span>{fmt_month(l["date"])}</span></li>' for l in largest) + "</ol>"
        year_2026_jobs = by_year.get(this_year, 0)

        # --- dashboard ---
        jobs_sorted = sorted(l["jobs"] for l in layoffs)
        median_jobs = jobs_sorted[len(jobs_sorted) // 2] if len(jobs_sorted) % 2 else (jobs_sorted[len(jobs_sorted) // 2 - 1] + jobs_sorted[len(jobs_sorted) // 2]) // 2
        biggest = layoffs_sorted[0]
        role_rank = sorted(((r, sum(x["jobs"] for x in rows), len(rows)) for r, rows in by_role.items() if r != "various"), key=lambda t: -t[1])
        top_role = max(role_rank, key=lambda t: (t[2], t[1]))   # most often named; its job figure is the size of those layoffs
        latest = sorted(layoffs, key=lambda l: l["date"], reverse=True)
        prev_year = str(now.year - 1)
        ytd_prev = sum(l["jobs"] for l in layoffs if l["date"][:4] == prev_year and l["date"][5:] <= now.strftime("%m-%d"))
        tiles = "".join([
            dash_tile(f"{total_jobs:,}", "Jobs cut, AI blamed", f"across {total_companies} companies since {first_year}", hero=True),
            dash_tile(f"{year_2026_jobs:,}", f"Cut in {this_year}", f"{len(by_year_c.get(this_year, ()))} companies · {prev_year}: {by_year.get(prev_year, 0):,}"),
            dash_tile(f"{biggest['jobs']:,}", "Biggest single cut", f"{esc(biggest['company'])}, {fmt_month(biggest['date'])}", href=f"#{slugify(biggest['company'])}"),
            dash_tile(f"{median_jobs:,}", "Median cut", "jobs per announcement"),
            dash_tile(esc(roles_map.get(top_role[0], top_role[0])), "Most-cited role", f"named in {top_role[2]} layoffs · {top_role[1]:,} jobs in those cuts", href=f"/jobs/{top_role[0]}/" if top_role[0] in role_pages else None, txt=True),
            dash_tile(esc(latest[0]["company"]), "Latest AI layoff", f"{latest[0]['jobs']:,} jobs · {fmt_month(latest[0]['date'])}", href=f"#{slugify(latest[0]['company'])}", txt=True),
        ])
        first_q = min(l["date"] for l in layoffs)
        qy, qq = int(first_q[:4]), (int(first_q[5:7]) - 1) // 3 + 1
        cur_q = (now.year, (now.month - 1) // 3 + 1)
        q_items = []
        while (qy, qq) <= cur_q:
            v = sum(l["jobs"] for l in layoffs if int(l["date"][:4]) == qy and (int(l["date"][5:7]) - 1) // 3 + 1 == qq)
            q_items.append((f"Q{qq} '{str(qy)[2:]}", v, fmt_k(v) if v else ""))
            qq += 1
            if qq == 5:
                qy, qq = qy + 1, 1
        now_q = f"Q{cur_q[1]} '{str(cur_q[0])[2:]}"
        peak_q = max(q_items, key=lambda t: t[1])
        cards = "".join([
            dash_card("AI layoffs by quarter", f"Jobs cut where the employer blamed AI. Peak: {peak_q[0]} with {peak_q[1]:,}. {now_q} is in progress: {q_items[-1][1]:,} so far.", dash_vbars(q_items, now_q), wide=True),
            dash_card("Biggest AI layoffs", "Top 10 single announcements", dash_hbars([(l["company"], l["jobs"], fmt_k(l["jobs"]), f"#{slugify(l['company'])}") for l in layoffs_sorted[:10]])),
            dash_card("Layoffs that named each role", "Total size of the layoffs naming each role; a layoff that names several roles counts in full under each",
                      dash_hbars([(roles_map.get(r, r), j, fmt_k(j), f"/jobs/{r}/" if r in role_pages else None) for r, j, _ in role_rank[:10]])),
            dash_card("Latest AI layoffs", "Most recent announcements first",
                      '<ul class="recent">' + "".join(f'<li><a href="#{slugify(l["company"])}">{esc(l["company"])} <em>{l["jobs"]:,}</em></a><span>{fmt_month(l["date"])}</span></li>' for l in latest[:8]) + "</ul>"),
            dash_card(f"{this_year} so far vs. {prev_year}", f"Same calendar window, Jan 1 to {now.strftime('%b %-d')}",
                      dash_hbars([(this_year, year_2026_jobs, f"{year_2026_jobs:,}", None), (prev_year, ytd_prev, f"{ytd_prev:,}", None)])
                      + f'<p class="dnote" style="margin:.75rem 0 0">{"Up" if year_2026_jobs >= ytd_prev else "Down"} {abs(year_2026_jobs - ytd_prev) / max(ytd_prev, 1) * 100:.0f}% on the same point last year. Companies citing AI in {this_year}: {len(by_year_c.get(this_year, ()))}.</p>'),
        ])
        dashboard = f'<div class="dash"><div class="tiles">{tiles}</div><div class="dash-grid">{cards}</div></div>'
        years_desc = sorted(by_year_n, reverse=True)
        controls = dash_controls(f"All {total_entries} AI layoffs", "Search company, role or reason…",
                                 [("jobs:desc", "Biggest first"), ("date:desc", "Newest first"), ("date:asc", "Oldest first"), ("name:asc", "A-Z")],
                                 [("all", "All", total_entries)] + [(y, y, by_year_n[y]) for y in years_desc]
                                 + [(r, roles_map.get(r, r), n) for r, _, n in sorted(role_rank, key=lambda t: -t[2])[:4]])

        layoffs_out = (layoffs_template
                       .replace("{{JSONLD}}", json.dumps(build_layoffs_jsonld(ldata), indent=2))
                       .replace("{{BREADCRUMB}}", json.dumps(build_breadcrumb("AI Layoffs Tracker", "layoffs"), indent=2))
                       .replace("{{DASH_CSS}}", DASH_CSS)
                       .replace("{{DASH_JS}}", DASH_JS)
                       .replace("{{DASHBOARD}}", dashboard)
                       .replace("{{CONTROLS}}", controls)
                       .replace("{{ROWS}}", rows_html)
                       .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
                       .replace("{{TOTAL_COMPANIES}}", str(total_companies))
                       .replace("{{BIGGEST}}", esc(f"{biggest['company']}'s {biggest['jobs']:,}"))
                       .replace("{{TOP_ROLE}}", esc(lc_label(roles_map.get(top_role[0], top_role[0]))))
                       .replace("{{FIRST_YEAR}}", first_year)
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

        def days_alive(i):
            return max((datetime.strptime(i["dateClose"], "%Y-%m-%d") - datetime.strptime(i["dateOpen"], "%Y-%m-%d")).days, 1)

        def burn_day(i):
            return i["fundingM"] * 1e6 / days_alive(i)

        def fmt_burn(v):
            return f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:,.0f}K"

        def frow(rank, i):
            slug = i.get("slug") or slugify(i["name"])
            yrs = days_alive(i) / 365.25
            text = " ".join([i["name"], i["description"], i.get("killedBy", ""), i.get("causeOfDeath", "")]).lower()
            killer = i.get("killedBy", "")
            return f'''<article class="fund-row" id="{slug}" data-sort-row data-fund="{i["fundingM"]}" data-date="{i["dateClose"].replace("-", "")}" data-burn="{burn_day(i):.0f}" data-life="{days_alive(i)}" data-name="{esc(i["name"].lower())}" data-f="{i.get("deathType", "")} {i["dateClose"][:4]}" data-text="{esc(text)}">
  <div class="fund-bar-wrap"><div class="fund-bar" style="width:{i["fundingM"] / max_fund * 100:.1f}%"></div></div>
  <div class="fund-info">
    <div class="fund-header">
      <h2 class="fund-name"><span class="rank" title="Rank by money raised">#{rank}</span> <a href="/dead/{slug}/">{esc(i["name"])}</a></h2>
      <span class="fund-amount">{fmt_money_m(i["fundingM"])}</span>
    </div>
    <p class="fund-desc">{esc(i["description"])}</p>
    <div class="fund-meta">
      <span class="mchip">{esc(DEATH_LABEL.get(i.get("deathType"), "Killed"))}</span>
      <span class="fund-dates">{i["dateOpen"][:4]} to {fmt_month(i["dateClose"])} · {yrs:.1f} yrs</span>
      <span class="fund-dates">{fmt_burn(burn_day(i))}/day</span>
      {f'<span class="fund-dates">Killed by {esc(killer)}</span>' if killer else ""}
      {f'<a class="fund-source" href="{esc(i["link"])}" target="_blank" rel="noopener">Source ↗</a>' if i.get("link") else ""}
    </div>
  </div>
</article>'''

        fund_rows = "\n".join(frow(k + 1, i) for k, i in enumerate(funded))

        # --- dashboard ---
        fm = sorted(i["fundingM"] for i in funded)
        median_m = fm[len(fm) // 2] if len(fm) % 2 else (fm[len(fm) // 2 - 1] + fm[len(fm) // 2]) / 2
        top = funded[0]
        fastest = max(funded, key=burn_day)
        avg_life = sum(days_alive(i) for i in funded) / len(funded) / 365.25
        this_year = str(datetime.utcnow().year)
        ytd = [i for i in funded if i["dateClose"][:4] == this_year]
        slug_of = lambda i: i.get("slug") or slugify(i["name"])
        tiles = "".join([
            dash_tile(f"${total_b}B", "Funding burned", f"raised by {len(funded)} dead AI companies", hero=True),
            dash_tile(fmt_money_m(sum(i["fundingM"] for i in ytd)), f"Died in {this_year}", f"{len(ytd)} companies so far"),
            dash_tile(fmt_money_m(top["fundingM"]), "Most expensive death", esc(top["name"]), href=f"/dead/{slug_of(top)}/"),
            dash_tile(fmt_money_m(median_m), "Median raise", "for a failed AI startup"),
            dash_tile(fmt_burn(burn_day(fastest)) + "/day", "Fastest burn", esc(fastest["name"]), href=f"/dead/{slug_of(fastest)}/"),
            dash_tile(f"{avg_life:.1f} yrs", "Average lifespan", "founding to shutdown"),
        ])
        years = sorted({i["dateClose"][:4] for i in funded})
        y_items = [(y, sum(i["fundingM"] for i in funded if i["dateClose"][:4] == y), "") for y in years]
        y_items = [(y, v, fmt_money_m(v)) for y, v, _ in y_items]
        by_death = {}
        for i in funded:
            k = i.get("deathType", "startup-failed")
            m, n = by_death.get(k, (0, 0))
            by_death[k] = (m + i["fundingM"], n + 1)
        by_killer = {}
        for i in funded:
            k = i.get("killedBy") or "Unknown"
            by_killer[k] = by_killer.get(k, 0) + i["fundingM"]
        burners = sorted(funded, key=burn_day, reverse=True)[:10]
        cards = "".join([
            dash_card("Funding burned, by year of death", "Total raised by AI companies that died that year", dash_vbars(y_items, this_year), wide=True),
            dash_card("Most expensive AI failures", "Top 10 by total funding raised", dash_hbars([(i["name"], i["fundingM"], fmt_money_m(i["fundingM"]), f"/dead/{slug_of(i)}/") for i in funded[:10]])),
            dash_card("Fastest cash burn", "Funding raised ÷ days alive", dash_hbars([(i["name"], burn_day(i), fmt_burn(burn_day(i)) + "/d", f"/dead/{slug_of(i)}/") for i in burners])),
            dash_card("How they died", "Funding lost by cause of death",
                      dash_hbars([(f"{DEATH_LABEL.get(k, k)} ({n})", m, fmt_money_m(m), None) for k, (m, n) in sorted(by_death.items(), key=lambda kv: -kv[1][0])])),
            dash_card("Who killed the money", "Funding lost, by what killed it",
                      dash_hbars([(k, m, fmt_money_m(m), f"/killed-by/{killer_slug(k)}/" if killer_counts.get(k, 0) >= 2 else None) for k, m in sorted(by_killer.items(), key=lambda kv: -kv[1])[:8]])),
        ])
        dashboard = f'<div class="dash"><div class="tiles">{tiles}</div><div class="dash-grid">{cards}</div></div>'
        controls = dash_controls(f"All {len(funded)} failed AI companies", "Search company, cause or killer…",
                                 [("fund:desc", "Most raised"), ("date:desc", "Most recent death"), ("burn:desc", "Fastest burn"), ("life:desc", "Longest-lived"), ("life:asc", "Shortest-lived"), ("name:asc", "A-Z")],
                                 [("all", "All", len(funded))] + [(k, DEATH_LABEL.get(k, k), n) for k, (m, n) in sorted(by_death.items(), key=lambda kv: -kv[1][1])]
                                 + [(y, y, sum(1 for i in funded if i["dateClose"][:4] == y)) for y in sorted(years, reverse=True)[:3]])

        fund_out = (fund_template
                    .replace("{{JSONLD}}", json.dumps(build_funding_jsonld(funded, total_b), indent=2))
                    .replace("{{BREADCRUMB}}", json.dumps(build_breadcrumb("Funding Burned", "funding"), indent=2))
                    .replace("{{DASH_CSS}}", DASH_CSS)
                    .replace("{{DASH_JS}}", DASH_JS)
                    .replace("{{DASHBOARD}}", dashboard)
                    .replace("{{CONTROLS}}", controls)
                    .replace("{{ROWS}}", fund_rows)
                    .replace("{{FOOTER_LINKS}}", footer_links())
                    .replace("{{TOTAL_B}}", total_b)
                    .replace("{{COUNT}}", str(len(funded)))
                    .replace("{{TOP1}}", esc(f"{top['name']}'s {fmt_money_m(top['fundingM'])}"))
                    .replace("{{TOP2}}", esc(f"{funded[1]['name']}'s {fmt_money_m(funded[1]['fundingM'])}"))
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
        gy_names = {(g.get("slug") or slugify(g["name"])): g["name"] for g in data}
        upcoming = [i for i in cs_sorted if i["dateShutdown"] >= now.strftime("%Y-%m-%d")] or cs_sorted
        if upcoming:
            y0, y1 = upcoming[0]["dateShutdown"][:4], upcoming[-1]["dateShutdown"][:4]
            cs_span = y0 if y0 == y1 else f"{y0}-{y1[2:]}"
            first_m, last_m = fmt_month(upcoming[0]["dateShutdown"]), fmt_month(upcoming[-1]["dateShutdown"])
            cs_range = first_m if first_m == last_m else f"{first_m} to {last_m}"
        else:
            cs_span, cs_range = str(now.year), "none scheduled"

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
            if item.get("graveyardSlug") in gy_names:   # a related tombstone (e.g. the app died, this channel still lives)
                tomb = f'<a class="doom-tomb" href="/dead/{esc(item["graveyardSlug"])}/">🪦 Related: the {esc(gy_names[item["graveyardSlug"]])} tombstone →</a>'
            cs_rows.append(
                f'''<article class="doom-card" id="{slugify(item["name"])}">
  <div class="doom-header">
    <h2 class="doom-name">{esc(item["name"])}</h2>
    <span class="doom-countdown{dead_class}" data-shutdown="{item["dateShutdown"]}">{countdown}</span>
  </div>
  <p class="doom-desc">{esc(item["description"])}</p>
  <div class="doom-meta">
    <span class="doom-tag">Killed by: {esc(item["killedBy"])}</span>
    <span>Shutdown: <time datetime="{item["dateShutdown"]}">{fmt_date(item["dateShutdown"])}</time></span>
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
                  .replace("{{YEAR_SPAN}}", cs_span)
                  .replace("{{SHUTDOWN_RANGE}}", esc(cs_range))
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

    # Build sitemap: lastmod derived from git so it changes only when content does
    pages = [
        (SITE_URL, "1.0", "daily", lm(["graveyard.json", "template.html", "build.py"])),
        (SITE_URL + "layoffs/", "0.9", "weekly", lm(["layoffs.json", "layoffs-template.html"])),
        (SITE_URL + "coming-soon/", "0.8", "weekly", lm(["coming-soon.json", "coming-soon-template.html"])),
        (SITE_URL + "funding/", "0.8", "weekly", lm(["graveyard.json", "funding-template.html"])),
        (SITE_URL + "will-ai-take-my-job/", "0.9", "weekly", lm(["layoffs.json", "job-risk-template.html", "data/microsoft-ai-applicability-scores.csv"])),
        (SITE_URL + "api/", "0.6", "monthly", lm(["api/index.html"])),
        (SITE_URL + "about/", "0.5", "monthly", lm(["about/index.html"])),
        (SITE_URL + "embed/", "0.6", "weekly", lm(["embed.py", "embed-template.html", "graveyard.json", "layoffs.json"])),
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

    # Hand-written pages: refresh the generated bits between markers so they can't drift from the rest of the site.
    fl = footer_links()
    latest = sorted(data, key=lambda i: (i.get("dateAdded") or i["dateClose"], i["dateClose"]), reverse=True)[:5]
    latest_html = ('<h2>Recently buried</h2><div class="related">'
                   + "".join(f'<a class="rel" href="{product_url(i)}"><b>{esc(i["name"])}</b><span>{fmt_month(i["dateClose"])}</span></a>' for i in latest)
                   + f'</div><p style="margin-top:1rem"><a href="/dead/">All {len(data)} tombstones, A-Z →</a></p>')
    slugs_json = json.dumps([[i.get("slug") or slugify(i["name"]), i["name"]] for i in data], ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    for rel in ("api/index.html", "about/index.html", "404.html"):
        page = ROOT / rel
        if not page.exists():
            continue
        src = page.read_text()
        out = re.sub(r"(<!--FOOTER_LINKS-->).*?(<!--/FOOTER_LINKS-->)", lambda m: m.group(1) + fl + m.group(2), src, count=1, flags=re.S)
        out = re.sub(r"(<!--LATEST-->).*?(<!--/LATEST-->)", lambda m: m.group(1) + latest_html + m.group(2), out, count=1, flags=re.S)
        out = re.sub(r'(<script type="application/json" id="tombstones">).*?(</script>)', lambda m: m.group(1) + slugs_json + m.group(2), out, count=1, flags=re.S)
        if rel == "api/index.html":
            out = re.sub(r'"dateModified": "\d{4}-\d{2}-\d{2}"',
                         '"dateModified": "%s"' % max(lm(["graveyard.json"]), lm(["layoffs.json"]), lm(["coming-soon.json"])), out)
        if out != src:   # only touch the file when something changed, so its git lastmod stays honest
            page.write_text(out)

    # A literal {{PLACEHOLDER}} in a built page means a template gained a slot no caller fills.
    leftovers = [str(p.relative_to(ROOT)) for p in ROOT.glob("**/*.html")
                 if not p.name.endswith("template.html") and ".git" not in p.parts and re.search(r"\{\{[A-Z_]+\}\}", p.read_text())]
    if leftovers:
        print(f"\n✗ BUILD FAILED: unfilled template placeholders in {', '.join(sorted(leftovers)[:10])}")
        raise SystemExit(1)



if __name__ == "__main__":
    main()
