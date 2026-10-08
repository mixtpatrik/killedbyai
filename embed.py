"""Embeddable graphics for /embed/: static SVG images (dark and light), small live iframe widgets,
and the gallery page that hands out the embed code. Called from build.py's main() once the data is loaded.

Everything here is generated from graveyard.json, layoffs.json and coming-soon.json on each build, so the
numbers in an embedded image are as fresh as the last deploy.
"""
import json
from collections import Counter
from datetime import datetime
from html import escape


THEMES = {
    "dark": {"bg": "#09090b", "card": "#111113", "border": "#27272a", "text": "#fafafa", "muted": "#a1a1aa", "dim": "#71717a",
             "red": "#ef4444", "orange": "#f97316", "amber": "#f59e0b", "track": "#1c1c1f"},
    "light": {"bg": "#ffffff", "card": "#fafafa", "border": "#e4e4e7", "text": "#09090b", "muted": "#52525b", "dim": "#71717a",
              "red": "#dc2626", "orange": "#ea580c", "amber": "#d97706", "track": "#f4f4f5"},
}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"


def esc(s):
    return escape(str(s or ""), quote=True)


def _svg(w, h, t, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>'
            f'<rect width="{w}" height="{h}" rx="18" fill="{t["bg"]}"/>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" fill="none" stroke="{t["border"]}" stroke-width="2"/>'
            f'{body}</svg>')


def _brand(w, h, t, x=40):
    return (f'<text x="{x}" y="{h - 30}" font-family="{FONT}" font-size="20" font-weight="700" fill="{t["text"]}">💀 Killed by <tspan fill="{t["red"]}">AI</tspan></text>'
            f'<text x="{w - 40}" y="{h - 30}" text-anchor="end" font-family="{FONT}" font-size="18" fill="{t["dim"]}">killedbyai.net</text>')


def counter_svg(t, value, label, sub, accent, w=1200, h=630, title=""):
    body = (f'<rect x="0" y="0" width="{w}" height="10" rx="5" fill="{t[accent]}"/>'
            f'<text x="{w / 2}" y="285" text-anchor="middle" font-family="{MONO}" font-size="150" font-weight="900" fill="{t[accent]}" letter-spacing="-4">{esc(value)}</text>'
            f'<text x="{w / 2}" y="365" text-anchor="middle" font-family="{FONT}" font-size="44" font-weight="800" fill="{t["text"]}">{esc(label)}</text>'
            f'<text x="{w / 2}" y="420" text-anchor="middle" font-family="{FONT}" font-size="28" fill="{t["muted"]}">{esc(sub)}</text>'
            + _brand(w, h, t))
    return _svg(w, h, t, body, title or f"{value} {label}")


def bars_svg(t, items, title, note, accent, w=1200, h=630):
    """Vertical bar chart: items = [(label, value, value_text)]."""
    top, bottom, left, right = 150, 120, 60, 60
    n = max(len(items), 1)
    mx = max((v for _, v, _ in items), default=1) or 1
    slot = (w - left - right) / n
    bw = min(110, slot * 0.68)
    ch = h - top - bottom
    out = [f'<rect x="0" y="0" width="{w}" height="10" rx="5" fill="{t[accent]}"/>',
           f'<text x="{left}" y="75" font-family="{FONT}" font-size="40" font-weight="800" fill="{t["text"]}">{esc(title)}</text>',
           f'<text x="{left}" y="115" font-family="{FONT}" font-size="24" fill="{t["muted"]}">{esc(note)}</text>']
    for i, (lab, v, vt) in enumerate(items):
        bh = max(3, v / mx * (ch - 40))
        x = left + i * slot + (slot - bw) / 2
        y = top + ch - bh
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="{t[accent]}"/>')
        if vt:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-family="{MONO}" font-size="{22 if n > 8 else 28}" font-weight="800" fill="{t["text"]}">{esc(vt)}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{top + ch + 34}" text-anchor="middle" font-family="{MONO}" font-size="{18 if n > 8 else 24}" fill="{t["muted"]}">{esc(lab)}</text>')
    out.append(_brand(w, h, t))
    return _svg(w, h, t, "".join(out), title)


def hbars_svg(t, items, title, note, accent, w=1200, h=630):
    """Horizontal ranked bars: items = [(label, value, value_text)]."""
    top, left, lab_w, right = 150, 60, 330, 150
    n = max(len(items), 1)
    mx = max((v for _, v, _ in items), default=1) or 1
    row = min(48, (h - top - 90) / n)
    out = [f'<rect x="0" y="0" width="{w}" height="10" rx="5" fill="{t[accent]}"/>',
           f'<text x="{left}" y="75" font-family="{FONT}" font-size="40" font-weight="800" fill="{t["text"]}">{esc(title)}</text>',
           f'<text x="{left}" y="115" font-family="{FONT}" font-size="24" fill="{t["muted"]}">{esc(note)}</text>']
    track_w = w - left - lab_w - right
    for i, (lab, v, vt) in enumerate(items):
        y = top + i * row
        lab = lab if len(lab) <= 24 else lab[:23] + "…"
        out.append(f'<text x="{left}" y="{y + row * 0.62:.1f}" font-family="{FONT}" font-size="24" fill="{t["text"]}">{esc(lab)}</text>')
        out.append(f'<rect x="{left + lab_w}" y="{y + row * 0.3:.1f}" width="{track_w}" height="{row * 0.42:.1f}" rx="8" fill="{t["track"]}"/>')
        out.append(f'<rect x="{left + lab_w}" y="{y + row * 0.3:.1f}" width="{max(6, v / mx * track_w):.1f}" height="{row * 0.42:.1f}" rx="8" fill="{t[accent]}"/>')
        out.append(f'<text x="{w - left}" y="{y + row * 0.62:.1f}" text-anchor="end" font-family="{MONO}" font-size="24" font-weight="800" fill="{t["text"]}">{esc(vt)}</text>')
    out.append(_brand(w, h, t))
    return _svg(w, h, t, "".join(out), title)


def badge_svg(t, left_text, right_text, accent):
    lw = 14 + len(left_text) * 7.4
    rw = 14 + len(right_text) * 7.4
    w = lw + rw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="24" viewBox="0 0 {w:.0f} 24" role="img" aria-label="{esc(left_text)}: {esc(right_text)}">'
            f'<title>{esc(left_text)}: {esc(right_text)}</title>'
            f'<rect width="{w:.0f}" height="24" rx="5" fill="{t["card"]}" stroke="{t["border"]}"/>'
            f'<rect x="{lw:.0f}" width="{rw:.0f}" height="24" rx="5" fill="{t[accent]}"/><rect x="{lw:.0f}" width="6" height="24" fill="{t[accent]}"/>'
            f'<text x="{lw / 2:.0f}" y="16.5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="{t["text"]}">{esc(left_text)}</text>'
            f'<text x="{lw + rw / 2:.0f}" y="16.5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="700" fill="#ffffff">{esc(right_text)}</text></svg>')


def fmt_k(n):
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def first_sentence(s, limit=150):
    s = (s or "").strip()
    for i, ch in enumerate(s):
        if ch == "." and i > 30 and (i + 1 == len(s) or s[i + 1] == " "):
            s = s[: i + 1]
            break
    return s if len(s) <= limit else s[: limit - 1].rsplit(" ", 1)[0] + "…"


WIDGET_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#09090b;--card:#111113;--border:#27272a;--text:#fafafa;--muted:#a1a1aa;--dim:#8f8f99;--red:#ef4444;--orange:#f97316;--amber:#f59e0b}
html.light{--bg:#ffffff;--card:#fafafa;--border:#e4e4e7;--text:#09090b;--muted:#52525b;--dim:#71717a;--red:#dc2626;--orange:#ea580c;--amber:#d97706}
html,body{background:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--text);line-height:1.45;font-size:14px}
.w{background:var(--bg);border:1px solid var(--border);border-radius:14px;padding:16px 18px;min-height:100vh;display:flex;flex-direction:column;gap:10px}
.top{display:flex;align-items:baseline;justify-content:space-between;gap:10px}
.big{font:900 40px/1 ui-monospace,"SF Mono",Menlo,monospace;letter-spacing:-.03em;color:var(--red)}
.big.o{color:var(--orange)}.big.a{color:var(--amber)}
.lbl{font-weight:800;font-size:15px}
.sub{color:var(--muted);font-size:13px}
ul{list-style:none;display:flex;flex-direction:column}
li{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid var(--border);font-size:13.5px}
li a{color:var(--text);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
li a:hover{color:var(--red)}
li span{color:var(--dim);font:12.5px ui-monospace,"SF Mono",Menlo,monospace;white-space:nowrap}
li b{color:var(--red);font:800 12.5px ui-monospace,"SF Mono",Menlo,monospace;white-space:nowrap}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--dim);padding-top:4px}
.foot a{color:var(--text);font-weight:700;text-decoration:none}
.foot a:hover{color:var(--red)}
.tomb h1{font-size:20px;line-height:1.2;margin:2px 0 4px}
.tomb .dates{font:13px ui-monospace,"SF Mono",Menlo,monospace;color:var(--muted)}
.tomb p{font-size:13.5px;color:var(--muted)}
.tomb .kill{font-size:12.5px;color:var(--dim)}
"""
THEME_JS = ("<script>(function(){var p=new URLSearchParams(location.search).get('theme');"
            "if(p==='light'||(!p&&window.matchMedia&&matchMedia('(prefers-color-scheme: light)').matches))document.documentElement.className='light';})();</script>")


def widget_page(title, body, canonical):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="robots" content="noindex, follow"><link rel="canonical" href="{canonical}">'
            f'{THEME_JS}<style>{WIDGET_CSS}</style></head><body>{body}</body></html>')


def foot(site, path=""):
    return f'<div class="foot"><span>Data updated {datetime.utcnow().strftime("%b %-d, %Y")}</span><a href="{site}{path}" target="_blank" rel="noopener">💀 Killed by AI ↗</a></div>'


def build_embeds(root, site, data, ldata, cs_data, publish, site_nav, footer_links, product_url):
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    deaths = sorted(data, key=lambda i: i["dateClose"], reverse=True)
    n_dead = len(data)
    total_jobs = sum(l["jobs"] for l in ldata)
    n_companies = len({l["company"].split(" (")[0].strip().lower() for l in ldata})
    funded = [i for i in data if i.get("fundingM")]
    total_b = sum(i["fundingM"] for i in funded) / 1000
    years = Counter(i["dateClose"][:4] for i in data)
    year_items = [(y, years[y], str(years[y])) for y in sorted(years) if int(y) >= 2022]
    parent = {"Google Gemini": "Google", "AWS": "Amazon", "GitHub": "Microsoft", "GitHub / Microsoft": "Microsoft", "Microsoft Copilot": "Microsoft"}
    killers = Counter(parent.get(i["killedBy"], i["killedBy"]) for i in data if "/" not in i["killedBy"] or i["killedBy"] in parent)
    for k in ("Itself", "Market", "Reality"):
        killers.pop(k, None)
    q = Counter()
    for l in ldata:
        y, m = l["date"][:4], int(l["date"][5:7])
        q[(y, (m - 1) // 3 + 1)] += l["jobs"]
    if q:
        y0, q0 = min(q)
        qi, cur = [], (int(y0), q0)
        while cur <= (now.year, (now.month - 1) // 3 + 1):
            v = q.get((str(cur[0]), cur[1]), 0)
            qi.append((f"Q{cur[1]} '{str(cur[0])[2:]}", v, fmt_k(v) if v else ""))
            cur = (cur[0] + (cur[1] == 4), cur[1] % 4 + 1)
    else:
        qi = []
    upcoming = sorted([c for c in cs_data if c["dateShutdown"] >= today], key=lambda c: c["dateShutdown"])
    first_year = min(i["dateClose"][:4] for i in data)

    graphics = [
        {"id": "graveyard-count", "title": "AI products killed", "page": "", "accent": "red",
         "alt": f"{n_dead} AI products killed since {first_year}, tracked by Killed by AI",
         "share": f"{n_dead} AI products, models and startups have died since {first_year}. The full graveyard:",
         "svg": lambda t: counter_svg(t, str(n_dead), "AI products killed", f"Since {first_year}. Latest: {deaths[0]['name'][:42]}", "red")},
        {"id": "layoffs-count", "title": "Jobs cut by companies that blamed AI", "page": "layoffs/", "accent": "orange",
         "alt": f"{total_jobs:,} jobs cut by {n_companies} companies that explicitly blamed AI",
         "share": f"{total_jobs:,} jobs cut by {n_companies} companies that said AI was the reason. Every layoff, with a source:",
         "svg": lambda t: counter_svg(t, f"{total_jobs:,}", "jobs cut by companies that blamed AI", f"{n_companies} companies, each with a source", "orange")},
        {"id": "funding-burned", "title": "Funding burned by dead AI companies", "page": "funding/", "accent": "amber",
         "alt": f"${total_b:.1f}B raised by {len(funded)} AI companies that died",
         "share": f"${total_b:.1f}B raised by {len(funded)} AI companies that are now dead:",
         "svg": lambda t: counter_svg(t, f"${total_b:.1f}B", "raised by AI companies that died", f"{len(funded)} companies, from self-driving cars to AI gadgets", "amber")},
        {"id": "deaths-per-year", "title": "AI product deaths per year", "page": "", "accent": "red",
         "alt": "Bar chart of AI products killed per year: " + ", ".join(f"{y}: {v}" for y, v, _ in year_items),
         "share": "AI product deaths per year, " + ", ".join(f"{y}: {v}" for y, v, _ in year_items) + ".",
         "svg": lambda t: bars_svg(t, year_items, "AI products killed per year", f"{n_dead} deaths tracked, each with a date and a source", "red")},
        {"id": "layoffs-by-quarter", "title": "AI layoffs by quarter", "page": "layoffs/", "accent": "orange",
         "alt": "Bar chart of jobs cut per quarter by companies that blamed AI",
         "share": f"Jobs cut per quarter by companies that blamed AI ({total_jobs:,} in total):",
         "svg": lambda t: bars_svg(t, qi, "AI layoffs by quarter", "Jobs cut where the company itself named AI as the reason", "orange")},
        {"id": "top-killers", "title": "Who killed the most AI products", "page": "killed-by/", "accent": "red",
         "alt": "Ranking of companies by AI products shut down: " + ", ".join(f"{k} {v}" for k, v in killers.most_common(8)),
         "share": "Which company has killed the most AI products? " + ", ".join(f"{k}: {v}" for k, v in killers.most_common(5)) + ".",
         "svg": lambda t: hbars_svg(t, [(k, v, str(v)) for k, v in killers.most_common(8)], "Who killed the most AI products", "Shut down by each company (Gemini counted as Google, GitHub as Microsoft, AWS as Amazon)", "red")},
    ]
    img = root / "embed" / "img"
    img.mkdir(parents=True, exist_ok=True)
    for g in graphics:
        for name, t in THEMES.items():
            (img / f"{g['id']}-{name}.svg").write_text(g["svg"](t))
    for name, t in THEMES.items():
        (img / f"badge-graveyard-{name}.svg").write_text(badge_svg(t, "💀 Killed by AI", f"{n_dead} dead", "red"))
        (img / f"badge-layoffs-{name}.svg").write_text(badge_svg(t, "AI layoffs", f"{total_jobs:,} jobs", "orange"))

    # --- live iframe widgets ---
    wdir = root / "embed" / "w"

    def write_widget(slug, title, body):
        d = wdir / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(widget_page(title, body, site + "embed/"))

    latest = "".join(f'<li><a href="{product_url(i)}" target="_blank" rel="noopener">{esc(i["name"])}</a><span>{datetime.strptime(i["dateClose"], "%Y-%m-%d").strftime("%b %Y")}</span></li>' for i in deaths[:5])
    write_widget("graveyard", "AI graveyard counter",
                 f'<div class="w"><div class="top"><div class="big">{n_dead}</div><div class="lbl">AI products killed since {first_year}</div></div>'
                 f'<div class="sub">Latest deaths</div><ul>{latest}</ul>{foot(site)}</div>')
    recent_l = sorted(ldata, key=lambda l: l["date"], reverse=True)[:5]
    lrows = "".join(f'<li><a href="{site}layoffs/" target="_blank" rel="noopener">{esc(l["company"])}</a><b>{l["jobs"]:,}</b></li>' for l in recent_l)
    write_widget("layoffs", "AI layoffs counter",
                 f'<div class="w"><div class="top"><div class="big o">{total_jobs:,}</div><div class="lbl">jobs cut by companies that blamed AI</div></div>'
                 f'<div class="sub">{n_companies} companies. Most recent:</div><ul>{lrows}</ul>{foot(site, "layoffs/")}</div>')
    urows = "".join(f'<li data-d="{c["dateShutdown"]}"><a href="{site}coming-soon/" target="_blank" rel="noopener">{esc(c["name"])}</a><b class="cd">{c["dateShutdown"]}</b></li>' for c in upcoming[:5])
    write_widget("dying-soon", "AI shutdown countdown",
                 f'<div class="w"><div class="top"><div class="lbl">⏳ Next AI shutdowns</div><div class="sub">{len(upcoming)} announced</div></div>'
                 f'<ul>{urows}</ul>{foot(site, "coming-soon/")}</div>'
                 "<script>document.querySelectorAll('li[data-d]').forEach(function(li){var d=Math.ceil((new Date(li.dataset.d+'T00:00:00Z')-Date.now())/864e5);"
                 "li.querySelector('.cd').textContent=d>1?d+' days':d===1?'tomorrow':d===0?'today':'dead';});</script>")
    compact = {i["slug"]: [i["name"], i["dateOpen"], i["dateClose"], i["killedBy"], first_sentence(i["description"])] for i in data if i.get("slug")}
    compact_js = json.dumps(compact, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    write_widget("tombstone", "AI product tombstone",
                 '<div class="w tomb" id="t"><div class="sub">Pick a product on killedbyai.net/embed/</div></div>'
                 f'<script>var D={compact_js};'
                 "var s=new URLSearchParams(location.search).get('slug'),e=D[s],t=document.getElementById('t');"
                 "function m(d){return new Date(d+'T00:00:00Z').toLocaleDateString('en-US',{month:'short',year:'numeric',timeZone:'UTC'})}"
                 "function x(v){var n=document.createElement('div');n.textContent=v;return n.innerHTML}"
                 f"if(e){{t.innerHTML='<div class=\"sub\">🪦 Rest in peace</div><h1>'+x(e[0])+'</h1><div class=\"dates\">'+m(e[1])+' to '+m(e[2])+'</div><p>'+x(e[4])+'</p>'+"
                 f"(['Itself','Market','Reality'].indexOf(e[3])<0?'<div class=\"kill\">Killed by '+x(e[3])+'</div>':'')+"
                 f"'<div class=\"foot\"><span>killedbyai.net</span><a href=\"{site}dead/'+encodeURIComponent(s)+'/\" target=\"_blank\" rel=\"noopener\">Read the tombstone ↗</a></div>';}}</script>")

    # --- gallery page ---
    def card(g):
        return (f'<section class="g-card" id="{g["id"]}" data-id="{g["id"]}" data-page="{g["page"]}" data-alt="{esc(g["alt"])}" data-share="{esc(g["share"])}">'
                f'<h2>{esc(g["title"])}</h2>'
                f'<a class="g-prev" href="{site}{g["page"]}"><img src="/embed/img/{g["id"]}-dark.svg" width="1200" height="630" alt="{esc(g["alt"])}" loading="lazy"></a>'
                '<div class="g-actions"><button type="button" class="b" data-act="code">&lt;/&gt; Embed code</button>'
                '<button type="button" class="b" data-act="png">⬇ PNG</button><button type="button" class="b" data-act="svg">⬇ SVG</button>'
                '<button type="button" class="b" data-act="x">Share on X</button><button type="button" class="b" data-act="li">LinkedIn</button>'
                '<button type="button" class="b" data-act="reddit">Reddit</button><button type="button" class="b" data-act="bsky">Bluesky</button></div>'
                '<div class="g-code" hidden></div></section>')

    widgets = [("graveyard", "Graveyard counter + latest deaths", 330), ("layoffs", "AI layoffs counter", 330), ("dying-soon", "Next AI shutdowns, live countdown", 300)]
    wcards = "".join(f'<section class="g-card" id="widget-{w}" data-widget="{w}" data-h="{h}"><h2>{esc(t)}</h2>'
                     f'<iframe src="/embed/w/{w}/" title="{esc(t)}" height="{h}" loading="lazy"></iframe>'
                     '<div class="g-actions"><button type="button" class="b" data-act="wcode">&lt;/&gt; Embed code</button></div><div class="g-code" hidden></div></section>' for w, t, h in widgets)
    options = "".join(f'<option value="{i["slug"]}">{esc(i["name"])}</option>' for i in sorted(data, key=lambda i: i["name"].lower()) if i.get("slug"))
    tpl = (root / "embed-template.html").read_text()
    url = site + "embed/"
    jsonld = {"@context": "https://schema.org", "@type": "WebPage", "@id": url, "url": url,
              "name": "Embed AI graveyard charts and counters", "isPartOf": {"@type": "WebSite", "@id": site + "#website", "name": "Killed by AI", "url": site},
              "description": f"Free charts, counters and widgets to embed: {n_dead} dead AI products, {total_jobs:,} jobs cut in AI layoffs and ${total_b:.1f}B in burned funding.",
              "dateModified": today,
              "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": site},
                                                                             {"@type": "ListItem", "position": 2, "name": "Embed & share", "item": url}]}}
    out = (tpl.replace("{{NAV}}", site_nav("/embed/", "/embed/"))
           .replace("{{JSONLD}}", json.dumps(jsonld, indent=1, ensure_ascii=False))
           .replace("{{GRAPHICS}}", "".join(card(g) for g in graphics))
           .replace("{{WIDGETS}}", wcards)
           .replace("{{OPTIONS}}", options)
           .replace("{{N_DEAD}}", str(n_dead))
           .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
           .replace("{{TOTAL_B}}", f"{total_b:.1f}")
           .replace("{{FOOTER_LINKS}}", footer_links())
           .replace("{{SITE}}", site))
    publish("embed", out)
    print(f"Built embed/ with {len(graphics)} graphics, {len(widgets) + 1} widgets")
