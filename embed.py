"""Embeddable graphics for /embed/: static SVG images (dark and light), small live iframe widgets,
and the gallery page that hands out the embed code. Called from build.py's main() once the data is loaded.

Everything here is generated from graveyard.json, layoffs.json and coming-soon.json on each build, so the
numbers in an embedded image are as fresh as the last deploy.
"""
import json
from collections import Counter
from datetime import datetime
from html import escape


# Colours follow the site: dark is the site's own palette, light keeps the same hues, darkened where text needs contrast.
# "<accent>" fills bars and large figures; "<accent>_text" is for small text in that colour.
THEMES = {
    "dark": {"bg": "#09090b", "border": "#26262a", "text": "#f4f4f5", "muted": "#a1a1aa", "dim": "#8f8f99",
             "red": "#ef4444", "orange": "#f97316", "amber": "#f59e0b",
             "red_text": "#f87171", "orange_text": "#f97316", "amber_text": "#f59e0b", "bar": ".7"},
    "light": {"bg": "#ffffff", "border": "#e4e4e7", "text": "#18181b", "muted": "#52525b", "dim": "#71717a",
              "red": "#dc2626", "orange": "#ea580c", "amber": "#d97706",
              "red_text": "#dc2626", "orange_text": "#c2410c", "amber_text": "#b45309", "bar": ".85"},
}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif"
PAD = 60   # left and right margin of every 1200x630 graphic


def esc(s):
    return escape(str(s or ""), quote=True)


def _svg(w, h, t, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>'
            f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{t["border"]}"/>'
            f'{body}</svg>')


def _head(t, title, note):
    return (f'<text x="{PAD}" y="92" font-family="{SERIF}" font-size="46" font-weight="700" fill="{t["text"]}">{esc(title)}</text>'
            f'<text x="{PAD}" y="134" font-family="{FONT}" font-size="24" fill="{t["muted"]}">{esc(note)}</text>')


def _brand(w, h, t, src="killedbyai.net"):
    """Footer of every graphic: a hairline, the wordmark on the left and the source URL on the right."""
    return (f'<rect x="{PAD}" y="{h - 84}" width="{w - 2 * PAD}" height="1" fill="{t["border"]}"/>'
            f'<text x="{PAD}" y="{h - 36}" font-family="{SERIF}" font-size="28" font-weight="700" fill="{t["text"]}">Killed by <tspan fill="{t["red"]}">AI</tspan></text>'
            f'<text x="{w - PAD}" y="{h - 38}" text-anchor="end" font-family="{FONT}" font-size="20" fill="{t["dim"]}">{esc(src)}</text>')


def counter_svg(t, value, label, sub, accent, w=1200, h=630, title="", src="killedbyai.net"):
    body = (f'<text x="{PAD - 6}" y="308" font-family="{FONT}" font-size="176" font-weight="700" fill="{t[accent]}">{esc(value)}</text>'
            f'<text x="{PAD}" y="398" font-family="{SERIF}" font-size="50" font-weight="700" fill="{t["text"]}">{esc(label)}</text>'
            f'<text x="{PAD}" y="450" font-family="{FONT}" font-size="26" fill="{t["muted"]}">{esc(sub)}</text>'
            + _brand(w, h, t, src))
    return _svg(w, h, t, body, title or f"{value} {label}")


def bars_svg(t, items, title, note, accent, w=1200, h=630, src="killedbyai.net"):
    """Vertical bar chart: items = [(label, value, value_text)]."""
    n = max(len(items), 1)
    mx = max((v for _, v, _ in items), default=1) or 1
    base, top = h - 152, 206          # the bars stand on `base`; `top` is where the tallest one ends
    gap = 14 if n > 8 else 20
    bw = (w - 2 * PAD - gap * (n - 1)) / n
    fs = 20 if n > 8 else 24
    out = [_head(t, title, note)]
    for i, (lab, v, vt) in enumerate(items):
        bh = max(2, v / mx * (base - top))
        x = PAD + i * (bw + gap)
        y = base - bh
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="{t[accent]}" fill-opacity="{t["bar"]}"/>')
        if vt:
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" fill="{t["muted"]}">{esc(vt)}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{base + 34}" text-anchor="middle" font-family="{FONT}" font-size="{fs}" fill="{t["dim"]}">{esc(lab)}</text>')
    out.append(_brand(w, h, t, src))
    return _svg(w, h, t, "".join(out), title)


def hbars_svg(t, items, title, note, accent, w=1200, h=630, src="killedbyai.net"):
    """Horizontal ranked bars: items = [(label, value, value_text)]."""
    top, lab_w, num_w = 172, 300, 90
    n = max(len(items), 1)
    mx = max((v for _, v, _ in items), default=1) or 1
    row = min(46, (h - 84 - 16 - top) / n)
    track_w = w - 2 * PAD - lab_w - num_w
    out = [_head(t, title, note)]
    for i, (lab, v, vt) in enumerate(items):
        y = top + i * row
        lab = lab if len(lab) <= 22 else lab[:21] + "…"
        out.append(f'<text x="{PAD}" y="{y + row * 0.66:.1f}" font-family="{FONT}" font-size="24" fill="{t["text"]}">{esc(lab)}</text>')
        out.append(f'<rect x="{PAD + lab_w}" y="{y + row / 2 - 6:.1f}" width="{max(3, v / mx * track_w):.1f}" height="12" rx="2" fill="{t[accent]}" fill-opacity="{t["bar"]}"/>')
        out.append(f'<text x="{w - PAD}" y="{y + row * 0.66:.1f}" text-anchor="end" font-family="{FONT}" font-size="24" font-weight="600" fill="{t[accent + "_text"]}">{esc(vt)}</text>')
    out.append(_brand(w, h, t, src))
    return _svg(w, h, t, "".join(out), title)


def badge_svg(t, left_text, right_text, accent, wordmark=False):
    """Small README badge: a plain outlined label with the figure in the section colour. `wordmark` writes the
    left text as the site name, with its last word (AI) in red."""
    lw = 16 + len(left_text) * 6.9
    rw = 16 + len(right_text) * 7.1
    w = lw + rw
    left = esc(left_text)
    if wordmark:
        head, _, tail = left_text.rpartition(" ")
        left = f'{esc(head)} <tspan fill="{t["red_text"]}">{esc(tail)}</tspan>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="24" viewBox="0 0 {w:.0f} 24" role="img" aria-label="{esc(left_text)}: {esc(right_text)}">'
            f'<title>{esc(left_text)}: {esc(right_text)}</title>'
            f'<rect x=".5" y=".5" width="{w - 1:.0f}" height="23" rx="3" fill="{t["bg"]}" stroke="{t["border"]}"/>'
            f'<rect x="{lw:.0f}" y="1" width="1" height="22" fill="{t["border"]}"/>'
            f'<text x="{lw / 2:.0f}" y="16.5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" fill="{t["text"]}">{left}</text>'
            f'<text x="{lw + rw / 2:.0f}" y="16.5" text-anchor="middle" font-family="{FONT}" font-size="12" font-weight="600" fill="{t[accent + "_text"]}">{esc(right_text)}</text></svg>')


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
:root{--bg:#09090b;--border:#26262a;--line:#3f3f46;--text:#f4f4f5;--muted:#a1a1aa;--dim:#8f8f99;--red:#ef4444;--acc:#f87171}
.o{--acc:#f97316}.y{--acc:#eab308}
html.light{--bg:#ffffff;--border:#e4e4e7;--line:#a1a1aa;--text:#18181b;--muted:#52525b;--dim:#71717a;--red:#dc2626;--acc:#dc2626}
html.light .o{--acc:#c2410c}html.light .y{--acc:#a16207}
html,body{background:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;font-variant-numeric:tabular-nums;color:var(--text);line-height:1.45;font-size:14px}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
.w{background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:14px 18px 10px;min-height:100vh;display:flex;flex-direction:column;gap:6px}
.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 10px}
.top.sb{justify-content:space-between}
.big{font-size:34px;font-weight:700;line-height:1.1;color:var(--acc)}
.lbl{font-weight:600;font-size:15px}
.sub{color:var(--muted);font-size:13px}
ul{list-style:none}
li{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding:6px 0;border-top:1px solid var(--border)}
li a{color:var(--text);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
li a:hover{color:var(--acc)}
li span{color:var(--dim);font-size:13px;white-space:nowrap}
li b{color:var(--acc);font-weight:600;font-size:13px;white-space:nowrap}
.foot{margin-top:auto;display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding-top:8px;border-top:1px solid var(--border);font-size:13px;color:var(--dim)}
.foot span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.foot a{flex:none;color:var(--text);text-decoration:none;white-space:nowrap}
.foot a:hover{color:var(--acc)}
.foot a.more{text-decoration:underline;text-decoration-color:var(--line);text-underline-offset:3px}
.wm{font-family:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;font-size:15px;font-weight:700}
.wm i{font-style:normal;color:var(--red)}
.tomb h1{font-family:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;font-size:22px;font-weight:700;line-height:1.2}
.tomb .dates{font-size:13px;color:var(--dim)}
.tomb h1,.tomb p{display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}
.tomb h1{-webkit-line-clamp:2}
.tomb p{-webkit-line-clamp:3;color:var(--muted)}
"""
THEME_JS = ("<script>(function(){var p=new URLSearchParams(location.search).get('theme');"
            "if(p==='light'||(!p&&window.matchMedia&&matchMedia('(prefers-color-scheme: light)').matches))document.documentElement.className='light';})();</script>")
WORDMARK = '<span class="wm">Killed by <i>AI</i></span>'


def widget_page(title, body, canonical):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(title)}</title><meta name="robots" content="noindex, follow"><link rel="canonical" href="{canonical}">'
            f'{THEME_JS}<style>{WIDGET_CSS}</style></head><body>{body}</body></html>')


def foot(site, path=""):
    return (f'<div class="foot"><span>Data updated {datetime.utcnow().strftime("%b %-d, %Y")}</span>'
            f'<a href="{site}{path}" target="_blank" rel="noopener" aria-label="Killed by AI (opens in a new tab)">{WORDMARK} ↗</a></div>')


def build_embeds(root, site, data, ldata, cs_data, publish, site_nav, footer_links, product_url, read_template):
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
    host = site.split("//", 1)[-1].rstrip("/")

    def src(page):   # the source line printed on a graphic: the page its numbers come from
        return (host + "/" + page).rstrip("/")

    graphics = [
        {"id": "graveyard-count", "title": "AI products killed", "page": "", "accent": "red",
         "alt": f"{n_dead} AI products killed since {first_year}, tracked by Killed by AI",
         "share": f"{n_dead} AI products, models and startups have died since {first_year}. The full graveyard:",
         "svg": lambda t: counter_svg(t, str(n_dead), "AI products killed", f"Since {first_year}. Latest: {deaths[0]['name'][:42]}", "red", src=src(""))},
        {"id": "layoffs-count", "title": "Jobs cut by companies that blamed AI", "page": "layoffs/", "accent": "orange",
         "alt": f"{total_jobs:,} jobs cut by {n_companies} companies that explicitly blamed AI",
         "share": f"{total_jobs:,} jobs cut by {n_companies} companies that said AI was the reason. Every layoff, with a source:",
         "svg": lambda t: counter_svg(t, f"{total_jobs:,}", "jobs cut by companies that blamed AI", f"{n_companies} companies, each with a source", "orange", src=src("layoffs/"))},
        {"id": "funding-burned", "title": "Funding burned by dead AI companies", "page": "funding/", "accent": "amber",
         "alt": f"${total_b:.1f}B raised by {len(funded)} AI companies that died",
         "share": f"${total_b:.1f}B raised by {len(funded)} AI companies that are now dead:",
         "svg": lambda t: counter_svg(t, f"${total_b:.1f}B", "raised by AI companies that died", f"{len(funded)} companies, from self-driving cars to AI gadgets", "amber", src=src("funding/"))},
        {"id": "deaths-per-year", "title": "AI product deaths per year", "page": "", "accent": "red",
         "alt": "Bar chart of AI products killed per year: " + ", ".join(f"{y}: {v}" for y, v, _ in year_items),
         "share": "AI product deaths per year, " + ", ".join(f"{y}: {v}" for y, v, _ in year_items) + ".",
         "svg": lambda t: bars_svg(t, year_items, "AI products killed per year", f"{n_dead} deaths tracked, each with a date and a source", "red", src=src(""))},
        {"id": "layoffs-by-quarter", "title": "AI layoffs by quarter", "page": "layoffs/", "accent": "orange",
         "alt": "Bar chart of jobs cut per quarter by companies that blamed AI",
         "share": f"Jobs cut per quarter by companies that blamed AI ({total_jobs:,} in total):",
         "svg": lambda t: bars_svg(t, qi, "AI layoffs by quarter", "Jobs cut where the company itself named AI as the reason", "orange", src=src("layoffs/"))},
        {"id": "top-killers", "title": "Who killed the most AI products", "page": "killed-by/", "accent": "red",
         "alt": "Ranking of companies by AI products shut down: " + ", ".join(f"{k} {v}" for k, v in killers.most_common(8)),
         "share": "Which company has killed the most AI products? " + ", ".join(f"{k}: {v}" for k, v in killers.most_common(5)) + ".",
         "svg": lambda t: hbars_svg(t, [(k, v, str(v)) for k, v in killers.most_common(8)], "Who killed the most AI products", "Shut down by each company (Gemini counted as Google, GitHub as Microsoft, AWS as Amazon)", "red", src=src("killed-by/"))},
    ]
    img = root / "embed" / "img"
    img.mkdir(parents=True, exist_ok=True)
    for g in graphics:
        for name, t in THEMES.items():
            (img / f"{g['id']}-{name}.svg").write_text(g["svg"](t))
    for name, t in THEMES.items():
        (img / f"badge-graveyard-{name}.svg").write_text(badge_svg(t, "Killed by AI", f"{n_dead} dead", "red", wordmark=True))
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
                 f'<div class="w o"><div class="top"><div class="big">{total_jobs:,}</div><div class="lbl">jobs cut by companies that blamed AI</div></div>'
                 f'<div class="sub">{n_companies} companies. Most recent:</div><ul>{lrows}</ul>{foot(site, "layoffs/")}</div>')
    urows = "".join(f'<li data-d="{c["dateShutdown"]}"><a href="{site}coming-soon/" target="_blank" rel="noopener">{esc(c["name"])}</a><b class="cd">{c["dateShutdown"]}</b></li>' for c in upcoming[:5])
    write_widget("dying-soon", "AI shutdown countdown",
                 f'<div class="w y"><div class="top sb"><div class="lbl">Next AI shutdowns</div><div class="sub">{len(upcoming)} announced</div></div>'
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
                 f"if(e){{t.innerHTML='<div class=\"sub\">Rest in peace</div><h1>'+x(e[0])+'</h1><div class=\"dates\">'+m(e[1])+' to '+m(e[2])+"
                 f"(['Itself','Market','Reality'].indexOf(e[3])<0?' \u00b7 Killed by '+x(e[3]):'')+'</div><p>'+x(e[4])+'</p>'+"
                 f"'<div class=\"foot\"><span>killedbyai.net</span><a class=\"more\" href=\"{site}dead/'+encodeURIComponent(s)+'/\" target=\"_blank\" rel=\"noopener\">Read the tombstone ↗</a></div>';}}</script>")

    # --- gallery page ---
    def card(g, k):
        load = ' fetchpriority="high"' if k == 0 else "" if k == 1 else ' loading="lazy"'   # the first row is in view on load
        return (f'<section class="g-card" id="{g["id"]}" data-id="{g["id"]}" data-page="{g["page"]}" data-alt="{esc(g["alt"])}" data-share="{esc(g["share"])}">'
                f'<h3>{esc(g["title"])}</h3>'
                f'<a class="g-prev" href="{site}{g["page"]}"><img src="/embed/img/{g["id"]}-dark.svg" width="1200" height="630" alt="{esc(g["alt"])}"{load}></a>'
                '<div class="g-actions"><button type="button" class="b" data-act="code">Embed code</button>'
                '<button type="button" class="b" data-act="png">Download PNG</button><button type="button" class="b" data-act="svg">Download SVG</button></div>'
                '<div class="g-actions" role="group" aria-label="Share"><button type="button" class="b" data-act="x">Share on X</button><button type="button" class="b" data-act="li">LinkedIn</button>'
                '<button type="button" class="b" data-act="reddit">Reddit</button><button type="button" class="b" data-act="bsky">Bluesky</button></div>'
                '<div class="g-code" hidden></div></section>')

    widgets = [("graveyard", "Graveyard counter + latest deaths", 330), ("layoffs", "AI layoffs counter", 330), ("dying-soon", "Next AI shutdowns, live countdown", 300)]
    wcards = "".join(f'<section class="g-card" id="widget-{w}" data-widget="{w}" data-h="{h}"><h3>{esc(t)}</h3>'
                     f'<iframe src="/embed/w/{w}/" title="{esc(t)}" height="{h}" loading="lazy"></iframe>'
                     '<div class="g-actions"><button type="button" class="b" data-act="wcode">Embed code</button></div><div class="g-code" hidden></div></section>' for w, t, h in widgets)
    options = "".join(f'<option value="{i["slug"]}">{esc(i["name"])}</option>' for i in sorted(data, key=lambda i: i["name"].lower()) if i.get("slug"))
    tpl = read_template("embed-template.html")
    url = site + "embed/"
    jsonld = {"@context": "https://schema.org", "@type": "WebPage", "@id": url, "url": url,
              "name": "Embed AI graveyard charts and counters", "isPartOf": {"@type": "WebSite", "@id": site + "#website", "name": "Killed by AI", "url": site},
              "description": f"Free charts, counters and widgets to embed: {n_dead} dead AI products, {total_jobs:,} jobs cut in AI layoffs and ${total_b:.1f}B in burned funding.",
              "dateModified": today,
              "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Killed by AI", "item": site},
                                                                             {"@type": "ListItem", "position": 2, "name": "Embed & share", "item": url}]}}
    out = (tpl.replace("{{NAV}}", site_nav("/embed/", "/embed/"))
           .replace("{{JSONLD}}", json.dumps(jsonld, indent=1, ensure_ascii=False))
           .replace("{{GRAPHICS}}", "".join(card(g, k) for k, g in enumerate(graphics)))
           .replace("{{WIDGETS}}", wcards)
           .replace("{{OPTIONS}}", options)
           .replace("{{N_DEAD}}", str(n_dead))
           .replace("{{TOTAL_JOBS}}", f"{total_jobs:,}")
           .replace("{{TOTAL_B}}", f"{total_b:.1f}")
           .replace("{{FOOTER_LINKS}}", footer_links())
           .replace("{{SITE}}", site))
    publish("embed", out)
    print(f"Built embed/ with {len(graphics)} graphics, {len(widgets) + 1} widgets")
