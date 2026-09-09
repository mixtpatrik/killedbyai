# Link-Earning Assets for killedbyai.net — Implementation Spec

## Why this is the lever

Both sites have zero real editorial links. The competitor's 366 ref domains are one PBN network; ours are the same network plus github.com. That means the first 10–20 genuine links (a newsletter, a docs site, a founder post-mortem, a Wikipedia external-links slot) decide the brand query. Every asset below is designed so that *linking is the natural way to use it*, not a favor.

Two honest constraints shape the designs:

- **Static host.** GitHub Pages cannot run a dynamic badge or image endpoint. Everything is pre-rendered by `build.py` at deploy time; freshness comes from adding a daily `schedule:` cron to `deploy.yml` (needed anyway for countdowns and coming-soon → dead transitions; note GitHub disables cron on repos with 60 days of no pushes).
- **Nofollow reality.** GitHub README links and Wikipedia links are `nofollow`. They still drive traffic, AI-assistant citations (already 14 referrals), and discovery, but the *followed* links that beat a PBN profile come from newsletters, blogs, docs sites, post-mortems, and showcase reciprocity. Each asset below is routed toward those.

Local data facts that changed the specs: all 128 slugs (111 + 17) are unique and none collide with existing paths; the longest name is 56 chars (OG text must auto-shrink); the graveyard has no `dateAnnounced` field; 2026 has 3–11 deaths per month (a monthly report always has content); OpenAI 24 / Google 19 / Anthropic 9 kills (killer hub pages are viable). One surprise: **"weights ai", "wsup ai", "jork ai", "hereafter ai" all have GSC impressions and none of them is in the graveyard** — Google is already routing "what happened to X" intent to the homepage for products we don't even list.

---

## Ranking (effort-to-impact)

Effort scale: S = under a day, M = 1–3 days, L = a week or more, plus recurring time where noted.

| Rank | Asset | Effort | Link type it earns | Realistic 90-day links |
|---|---|---|---|---|
| 1 | **#3 "Is X dead?" answer pages** | M | Journalist/blog citations, Wikipedia refs and external links, AI-assistant citations; also the target URL for every other asset | 5–15 domains, plus the long-tail traffic that is currently landing on the homepage |
| 2 | **#6 Attribution nudge + Built-with showcase + cite box + llms.txt** | S | Converts existing data consumers into linkers; showcase listing is reciprocal and legitimate | 3–8 domains |
| 3 | **#1 Model-status badge (shields-compatible)** | S for site-wide counter, M with watchlist + builder page | READMEs (nofollow, github.com already counted), docs sites and project homepages (followed) | 10–50 embeds, 2–6 followed domains |
| 4 | **#4 Monthly AI Deaths Report** | M build, then ~2h/month editorial + outreach | Newsletter and press links, the only asset that reliably produces *editorial* links | 1–5 domains per issue, compounding |
| 5 | **#2 Per-product tombstone OG images** | M | Amplifier: raises share CTR for #3 and #4; images get hotlinked with credit | Indirect |
| 6 | **#5 Submit-a-death with public credit** | S core, M with issue-form automation | Contributor blogs, founder post-mortems, profile READMEs | 1–3 domains now, compounding with volume |

Sequencing: week 1 ship #3 and #6 together (and add the four missing products above). Week 2 ship #1 plus the daily cron. Week 3 ship #2 and #5. First #4 issue on October 1 covering September.

---

## 1. Embeddable "AI Death Counter" badge

### URL scheme (all pre-rendered under `/badge/`)

| URL | Shows | Colour |
|---|---|---|
| `/badge/count.svg` | `AI products killed \| 111` | red `#ef4444` |
| `/badge/layoffs.svg` | `jobs killed by AI \| 61,340` | orange |
| `/badge/funding.svg` | `VC burned \| $4.2B` | amber |
| `/badge/days-since.svg` | `days since last AI death \| 21` | red if ≤7, amber ≤30, grey otherwise |
| `/badge/killed-by/<killer-slug>.svg` | `killed by OpenAI \| 24` | red |
| `/badge/model/<slug>.svg` | `gpt-4o \| dead since 2026-04-01` / `sunsets in 43d` / `alive` | red / amber / green |
| `/badge/<slug>.svg` | `☠ OpenAI Sora \| 2024 – 2026` (tombstone badge for the product itself) | dark grey |
| `/badge/contributor/<github-user>.svg` | `gravedigger \| 7 deaths reported` (see #5) | purple |

Every `.svg` has a `.json` twin in the shields.io endpoint schema, so people who want a different style pass it through shields:

```
https://img.shields.io/endpoint?url=https://killedbyai.net/badge/model/gpt-4o.json&style=for-the-badge
```

The JSON twin is exactly: `{"schemaVersion":1,"label":"gpt-4o","message":"dead since 2026-04-01","color":"ef4444","cacheSeconds":3600}`. Fallback with no build at all: `https://img.shields.io/badge/dynamic/json?url=https://killedbyai.net/graveyard.json&query=$.length&label=AI%20products%20killed&color=ef4444` — put this in the docs as the "works today" option.

### Why developers actually add it (the utility hook)

The site-wide counter is a vanity badge; a few blogs will use it. The **model-status badge is a dependency-health badge**: any repo, tutorial, or LangChain/LlamaIndex integration pinned to a model shows its users whether that model is alive, dying (with a countdown), or dead. The pitch line: *"Your badge turns red the day the vendor kills the model."* This needs a `watchlist.json` (≈30 currently-supported models people pin: gpt-4.1, gpt-5, claude-sonnet-4, gemini-2.5-pro, llama-3.3-70b, etc., fields `name`, `vendor`, `docsUrl`). `build.py` resolves each watchlist name: in graveyard → dead; in coming-soon → countdown; else → alive. When a model dies, the maintainer moves the entry and every badge in the wild flips — no consumer action.

Second hook: the **tombstone badge for dead products**. Makers who archive a repo or startup routinely write "this project is discontinued". Offering them a dignified `[![Killed by AI](…/badge/<slug>.svg)](https://killedbyai.net/dead/<slug>/)` gives them a reason to link from the archived README, the post-mortem, and the "we're shutting down" page.

### Backlink mechanism

The image is never the link; the copy-paste snippet always wraps it: `[![alt](https://killedbyai.net/badge/model/gpt-4o.svg)](https://killedbyai.net/dead/gpt-4o/)`. README links on github.com are nofollow and github.com is already one of our ref domains, so the followed-link value comes from the same snippet being mirrored into MkDocs/Docusaurus/GitBook docs sites, project homepages, PyPI/npm READMEs mirrored to other hosts, and blog posts. Target the outreach at repos with a docs site.

### Implementation sketch

- `render_badge(label, message, color) -> str`: flat shields-style SVG, Verdana 11px, width ≈ 7 px/char + 10 px padding per side, two `<rect>` halves with a `<linearGradient>` gloss, `<title>` element for accessibility, `role="img"`, `aria-label`. About 700 bytes each.
- `render_badge_json(...)` writes the endpoint twin. `build_badges(data, cs_data, ldata, watchlist)` writes ≈ 300 files into `badge/`. Add `badge/` and `og/` to a new `.gitignore`; they are generated in CI, not committed (the deploy job already builds from `.`).
- `deploy.yml`: add `schedule: - cron: '17 6 * * *'` so `days-since` and countdown badges refresh without a push.
- `/badge/` page (`badge-template.html`): a builder with a slug dropdown, style switcher (self-hosted flat vs shields endpoint styles), live preview, and one-click copy for Markdown, HTML, reStructuredText. Link it from the nav and the API page.
- GitHub Pages sends `Cache-Control: max-age=600`; shields caches the endpoint per `cacheSeconds` (min 300). Nothing else to do.

Effort: S for counter badges, M for watchlist + builder page.

---

## 2. Per-product tombstone OG image

Today every share of a product shows the generic `og-image.png`, and product links are `#slug` anchors that share the homepage OG. This asset only pays off once per-product pages (#3) exist, so ship it right after.

### What `build.py` must generate

`og/<slug>.png` for every graveyard and coming-soon entry (≈128 files, 1200×630, ≈40 KB each), plus `og/home.png`, `og/layoffs.png`, `og/funding.png`, `og/coming-soon.png`, `og/report-YYYY-MM.png`, all regenerated each build so the numbers on them are always current (the current static PNG says "110+" forever).

### Design (house style, matches `og-image.svg`)

- Background `#09090b`, 3 px `#ef4444` top rule, `killedbyai.net` in `#52525b` bottom-centre, all as today.
- Left third: a tombstone silhouette (rounded-top rect, `#18181b` fill, `#27272a` stroke) with "R.I.P." and the lifespan (`1y 4m`) inside in mono weight.
- Right two-thirds: product name in Inter 900 with auto-shrink (start 72 px, step down until it fits 720 px wide, wrap to max 2 lines at 44 px minimum; the 56-char names need this); under it `b. 2023-03-21  —  d. 2024-02-08` in `#a1a1aa`; a red pill `Killed by Google`; a grey pill with `causeOfDeath`; if `collateral` exists, a single 20 px amber line truncated to 90 chars.
- Coming-soon variant: amber top rule, pill reads `Dies in 43 days`, date is `dateShutdown`.
- Alive variant (watchlist): green rule, "Not dead. Yet."

### Implementation sketch

- `pip install pillow` step in `deploy.yml`; vendor `fonts/Inter-Regular.ttf`, `Inter-Bold.ttf`, `Inter-Black.ttf` (OFL, redistribution allowed) because Pillow cannot use the Google Fonts CSS the site loads.
- `render_og(item, kind) -> PIL.Image`, using `ImageDraw.textlength` for the shrink-to-fit loop; write with `optimize=True`.
- Skip regeneration when a sidecar `og/.manifest.json` shows the same content hash for that slug (keeps scheduled builds fast).
- Each product page (#3) sets `og:image`, `og:image:width/height`, `og:image:alt` ("Tombstone for Google Bard, 2023–2024, killed by Google"), and `twitter:card = summary_large_image`.
- Add a "Share this tombstone" row on the product page: pre-filled post text (`Google Bard: 2023–2024. Killed by Google after 11 months. 🪦 https://killedbyai.net/dead/google-bard/`) for X, Bluesky, LinkedIn, and a copy-image button.

### Link-earning mechanism

Images are the unit of virality; a share that unfurls a specific tombstone gets clicked and re-shared where a generic card does not. Newsletters and blogs also hotlink the tombstone image with a credit line (the `killedbyai.net` watermark makes the credit self-enforcing). It also gives #4's report and #5's contributor notifications something visual to post.

Effort: M.

---

## 3. "Is [product] dead?" answer pages

This is the foundation. GSC already shows the query shapes: "is chatgpt dead", "why did wsup ai shut down", "what happened to jork ai", "hereafter ai shutting down 2026", "weights ai shutting down" (pos 65), "sora ai shutdown" (6,500/mo, KD 67). All land on a 400 KB homepage where the answer is one card among 111. Sub-pages are currently invisible in GSC because there are only four of them.

### URL and scope

- `/dead/<slug>/` for every graveyard entry (`/dead/openai-sora/`, `/dead/google-bard/`).
- Same namespace for coming-soon entries (answer: "Not yet — dies 2026-10-23, in 44 days") and for watchlist entries (answer: "No. ChatGPT is alive. But OpenAI has killed 6 things inside it: …"). The slug is the question, the page is the answer, and the URL never changes when the status does — that is what makes it safe to cite.
- Optional hubs: `/killed-by/openai/` (24 entries), `/killed-by/google/` — targets "killedbygoogle" (300/mo, KD 12) and the "companies killed by ai" cluster.
- Homepage cards: `card-name` becomes an `<a>` to the page; keep `id="slug"` so old `#slug` links still scroll. Rewrite the JSON-LD `ItemList` `url`s and the RSS `<link>`/`<guid>` to the new URLs. Sitemap lists every page with `lastmod` = `dateClose` (or today for coming-soon/watchlist).

### Page format (what makes it citable)

1. `<title>`: `Is OpenAI Sora dead? Yes — shut down by OpenAI in April 2026`. Meta description is the answer sentence.
2. `<h1>Is OpenAI Sora dead?</h1>` followed immediately by the **answer paragraph under 40 words**: "Yes. OpenAI shut down Sora on 1 April 2026, after 1 year 3 months. Cause of death: unsustainable compute costs." Dates in `<time datetime="…">`. This is the featured-snippet and AI-answer unit.
3. **Fact table** (`<table>` with `<th scope="row">`): Status, Launched, Shut down, Lifespan, Killed by, Cause, Type, Replacement (coming-soon), What users lost (`collateral`), Primary source (the `link` field, prominently, `rel="noopener"` — no nofollow; editors trust pages that cite primary sources). Add optional `dateAnnounced` to graveyard entries so the table can show Announced → Shut down.
4. H2s mirroring the GSC query shapes: "Why did OpenAI shut down Sora?" (the description), "What happened to Sora?" (timeline), "What replaced Sora?", "Other products killed by OpenAI" (same-killer list with links), "Products that died the same month".
5. **Quotable context line** for journalists, auto-generated: "According to Killed by AI, a tracker of discontinued AI products, OpenAI has retired 24 products since 2022; Sora was its 19th." This sentence is what ends up in articles, with the link.
6. **"Cite this page" box** with copy buttons for APA, MLA, BibTeX, and the pre-filled Wikipedia template:
   `{{cite web |url=https://killedbyai.net/dead/openai-sora/ |title=Is OpenAI Sora dead? |website=Killed by AI |date=2026-04-01 |access-date=2026-09-09}}`
   Frictionless citation is the single biggest driver of Wikipedia references and External-links entries; killedbygoogle.com is used exactly this way on Wikipedia talk pages and list articles. Wikipedia links are nofollow but they feed Knowledge Panels, AI answers, and downstream press.
7. JSON-LD: `BreadcrumbList` (Home › Graveyard › Sora), `FAQPage` with the one Q/A (no rich result any more, but it is the cleanest machine-readable answer), and the entry as `Thing` with `additionalProperty` plus `isPartOf` the Dataset. `dateModified` = last build.
8. Badge and OG for this product embedded at the bottom ("Embed Sora's tombstone") with the snippet — cross-links #1 and #2.

### Implementation sketch

`product-template.html` (dark theme, same nav, ≈15 KB); `build_product_page(item, kind, context)` computing lifespan, same-killer list, same-month list, killer rank; `publish_nested("dead", slug, html)` — extend `publish()` to take a parent dir and skip the legacy `.html` stub for nested pages; loop in `main()`; sitemap loop; `validate()` gains a slug-uniqueness assertion. Add the four missing products (Weights, Wsup, Jork, Hereafter) to `graveyard.json` or `coming-soon.json` with sources in the same PR.

Effort: M. This is the one asset with proven demand in our own GSC data.

---

## 4. Monthly "AI Deaths Report"

### What it is

A permanent page per month, `/report/2026-09/`, published on the 1st, plus `/report/` index and inclusion in `feed.xml`. Email delivery via Buttondown or Substack RSS-to-email — the canonical copy always lives on killedbyai.net so every quote links to us, not to a newsletter platform.

### Auto-generated sections (from `build.py`, all citable)

- Headline numbers with deltas: "5 AI products died in August 2026 (July: 11). Total: 111. Jobs cut citing AI this month: 8,000 (Meta). VC burned to date: $4.2B."
- Deaths this month: name, killer, lifespan, cause, link to `/dead/<slug>/`.
- Killer of the month, shortest-lived of the month, longest-lived of the month.
- Scheduled for next month (from `coming-soon.json`): name, date, days left, replacement.
- Layoffs this month from `layoffs.json`.
- Chart PNG `og/report-2026-09.png` (deaths per month, last 12 months) via the Pillow infra from #2, doubling as the page's OG image.
- "Use these numbers": CC BY line and a pre-written attribution sentence with the link, plus CSV download of the month's rows.

### Human section (the quotable part)

`reports/2026-09.md` with 150–300 words of editorial ("what this month tells us") written by the maintainer; `build.py` merges it. Newsletter writers quote opinions with numbers behind them; the auto table alone reads as a changelog.

### Link-earning mechanism and the labor it requires

Editors at TLDR, Ben's Bites, The Neuron, Import AI, and the TechCrunch running list of AI-attributed layoffs need dated, sourced numbers on a schedule. layoffs.fyi's entire link profile ("Roughly 120,000 tech roles cut in 2026, according to Layoffs.fyi") comes from being the citable monthly number. The report is our equivalent for product deaths. The recurring work each month: publish at a fixed time, post to Bluesky/LinkedIn/r/artificial, and send a three-line email (top three numbers + link) to a list of 20–30 newsletter editors and reporters who covered the previous month's shutdowns. Do not skip the emails; the page alone earns nothing.

Retitle `/layoffs/` while here: it is titled "Employee Graveyard" and does not contain the phrase "AI layoffs" (2,500/mo, traffic potential 49,000). Title it "AI Layoffs Tracker — Jobs Killed by AI" and keep "Employee Graveyard" as the H1 tagline.

Effort: M to build, then ~2 hours a month. Highest editorial-link yield of the six.

---

## 5. "Submit a death" flow with public credit

Today the CTA is a raw GitHub issue link and the repo has three human commits. The incentive that works for trackers is permanent, linked credit.

### Data model and rendering

- Optional `submittedBy: {"name": "…", "url": "https://…"}` on graveyard, coming-soon, and layoffs entries. `build.py` renders "Reported by Name" on the card, on `/dead/<slug>/`, and in the RSS item; the link is followed (the link *is* the reward; the maintainer reviews every submission, so spam is a non-issue). Default the URL to the contributor's GitHub profile; accept a personal site for PR authors.
- `/contributors/` page: leaderboard with ranks by accepted entries (1 Gravedigger, 5 Undertaker, 10 Grim Reaper), links to each contributor, and their personal `/badge/contributor/<user>.svg` snippet for a GitHub profile README (ties into #1).

### The flow

- `/submit/` page explaining the deal in one line: "Every accepted submission is credited on the tombstone, with a link to you, permanently."
- Path A: `.github/ISSUE_TEMPLATE/death.yml` issue form with structured fields (name, launch date, death date, killer, cause, primary source URL, your name, your URL). A small Action parses accepted issues into a PR, or the maintainer merges by hand at this volume.
- Path B: no-account form (Tally or Formspree free tier) posting to the maintainer's inbox, for journalists and founders who will not open a GitHub issue.
- On merge, the maintainer replies on the issue with the live `/dead/<slug>/` URL, the tombstone OG image, and suggested share text. Contributors post it; their audience links.

### Proactive use: founder right-of-reply

The 19 dead startups have founders who write post-mortems on LinkedIn, Medium, and HN, and those posts link to whatever documents the shutdown. Email each founder offering to correct or expand their entry and credit them. A corrected entry with the founder's own framing gets linked from the post-mortem almost every time. This is the highest-yield outreach the site can do per hour spent.

Effort: S for the field, rendering, and contributors page; M with the issue-form Action and Tally form. Compounds as volume grows.

---

## 6. Attribution nudge in API docs and footer

The API page already says "just credit killedbyai.net" in the footer. Make attribution concrete, copyable, and rewarded.

- **Attribution block at the top of `/api/`** (before endpoints): "Licence: CC BY 4.0. Attribution means a link. Copy one:" with tabs for HTML (`Data: <a href="https://killedbyai.net/">Killed by AI</a>`), Markdown, and plain text for print/newsletters.
- **"Built with this data" showcase** on `/api/`: list projects using the JSON with a link each, and a one-line form/issue link to get listed. A listing is a legitimate reciprocal link, and it is the strongest nudge here because the consumer gains something.
- **Footer on every page**: "Cite this site · Embed the counter · Submit a death · Monthly report". "Cite" opens a `<dialog>` reusing the #3 citation component.
- **Machine-readable attribution**: add `creditText`, `citation`, and `usageInfo` to every `Dataset` JSON-LD node (`"creditText": "Killed by AI (killedbyai.net), CC BY 4.0"`); add `<copyright>` to `feed.xml` and end each RSS description with "— via Killed by AI (killedbyai.net)" so feed aggregators republish the credit; add `/llms.txt` describing the datasets and the requested citation form for AI assistants (they already send referrals; make the citation string consistent).
- Do **not** change `graveyard.json` from an array to an object to embed attribution; it would break existing consumers. Ship a `meta.json` sidecar instead (`license`, `attribution`, `lastUpdated`, `counts`) — this also becomes the source for the badge JSON.

Effort: S. Mechanism: the bot-heavy Direct traffic (508 sessions, 20% engaged) is largely scrapers and data consumers who currently have no reason and no snippet to link; this gives them both.

---

## Cross-cutting build changes (one PR)

1. `deploy.yml`: `pip install pillow`; `schedule: - cron: '17 6 * * *'`.
2. `.gitignore`: `badge/`, `og/` (generated in CI only).
3. `build.py`: `render_badge`, `render_og`, `build_product_page`, `build_report`, `publish_nested`, slug-uniqueness check in `validate()`, sitemap loop over all generated pages, `submittedBy` rendering, `creditText` on datasets.
4. Data: add `dateAnnounced` (optional) and `submittedBy` (optional) to the schema docs on `/api/`; new `watchlist.json`, `meta.json`, `reports/YYYY-MM.md`.
5. Content: add Weights, Wsup, Jork, Hereafter entries; retitle `/layoffs/`.

Sources used: [Endpoint Badge — Shields.io](https://shields.io/badges/endpoint-badge), [killedbyai.xyz](https://killedbyai.xyz/) (search snippet only; no badge, API, report, or contributor credit visible in its description), [Template talk:Google LLC — killedbygoogle.com used as a Wikipedia source](https://en.wikipedia.org/wiki/Template_talk:Google_Inc.), [Layoffs.fyi — Wikipedia](https://en.wikipedia.org/wiki/Layoffs.fyi), [TechCrunch running list of 2026 layoffs citing AI](https://techcrunch.com/2026/07/06/the-running-list-major-tech-layoffs-in-2026-where-employers-cited-ai/), [Layoffs.fyi AI Layoffs Tracker](https://layoffs.fyi/ai-layoffs/).