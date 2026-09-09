# Killed by AI (.net) vs killedbyai.xyz — teardown, comparison, positioning

Data basis: 10 WebSearch calls (budget exhausted), the repo at `/home/user/killedbyai` (HEAD `af5a3f8`, 2026-09-09), and the GSC/Ahrefs/GA4 figures supplied. killedbyai.xyz was never fetched. Search summaries repeatedly conflated *our* content (the "111 products" count, `graveyard.json`, the Interview Warmup blurb) with the .xyz site; everything attributed to .xyz below appears in a snippet under the `killedbyai.xyz/` URL.

## A) Teardown of killedbyai.xyz (from snippets only)

**What can be established**

| Item | Evidence |
|---|---|
| `<title>` | "Killed by AI — A Registry of Products & Jobs Replaced by AI" |
| Meta/intro copy (three variants seen) | "The definitive registry of products, features, and jobs rendered obsolete by Artificial Intelligence." / "records products, services, and jobs retired by artificial intelligence — sourced, dated, and kept." / "tracks rising AI capabilities and catalysts before the next wave of layoffs and shutdowns." |
| Implied taxonomy | Four entity classes — **products, features, services, jobs** — plus a forward-looking **"capabilities / catalysts"** section (leading indicators before the next layoffs/shutdowns). |
| Per-entry fields | At minimum a **source** and a **date** ("sourced, dated"). Nothing else visible. |
| Tone | Archival/institutional: "registry", "definitive", "rendered obsolete", "retired", "kept". No slang, no graveyard metaphor. |
| Framing | Things killed **by** AI (jobs, features, products AI replaced). Ours is AI products that were killed (by their makers). Same brand phrase, different intent: theirs matches "jobs replaced by ai"; ours matches "ai graveyard / dead ai tools / sora shutdown". |
| Index footprint | `site:killedbyai.xyz` returned **zero** URLs; only the homepage ever surfaced. No sub-page path (products/jobs/features/about) was discoverable. |
| Third-party mentions | **None** across 10 queries: no Reddit, HN, Product Hunt, Bluesky, press, or GitHub. Consistent with Ahrefs: DR 1.3, 366 ref domains, ~100% PBN. |
| Adjacent sites surfaced | replaced-by-ai.xyz, killedbyopenai.com, aimortality.org, llmdeathcount.com, github.com/demondragong/deathbyai. |

**Cannot be determined:** entry count, full data schema, whether per-entry pages exist, search/filter/sort, API/RSS/feed, design system, mobile quality, update cadence, who runs it, whether it is a single page. Its #1 on "killedbyai" is explained by domain age (~6 months vs our 17 days) and link velocity, not by visible content depth.

**Side finding:** `mixtpatrik.github.io/killedbyai` still appears in results with our old title. The CNAME 301 is in place, but Google has not consolidated; the old URL is competing with us on our own brand query.

## B) Comparison against the repo

**They have, we lack**
1. **Jobs as first-class entries.** Their headline differentiator and the intent behind "jobs replaced by ai" (450/mo, TP 9,000) and "jobs lost to ai" (200). We have company-level layoffs only; `layoffs.json.roles` is free text ("Sales, support, traditional infrastructure") with no role index or role pages.
2. **"Features replaced by AI"** as a category. Our `feature-removed` (21 entries) means a feature cut *from* an AI product; not the same thing.
3. **"Capabilities / catalysts"** — a leading-indicator section. Our `/coming-soon/` is confirmed dates only.
4. **Authoritative SERP copy** ("definitive registry ... sourced, dated, and kept"). Our snippet reads as a hobby graveyard.
5. **#1 on the brand query** — time and links, not features.

**We have, they (visibly) lack**
- 111 dated entries with born/died/lifespan/cause/killer/type/collateral, 6 death types, a written methodology (`/about/`), CC BY 4.0.
- 111 per-product pages (`/dead/<slug>/`, built today) with "Is X dead?" + FAQPage schema, related/prev-next; 15 killer hubs (`/killed-by/<vendor>/`).
- Stats: deaths per year chart, kill leaderboard, pace of death, average lifespan; search, 5 type filters, sort, year filter, hide-upgrades toggle, hash deep-links.
- `/layoffs/` (30 companies, 115,633 jobs, source on every row, Dataset+ItemList schema), `/funding/` ($4.4B, 22 startups), `/coming-soon/` (17 countdowns), free JSON API with field docs, RSS, sitemap with git-derived lastmod, daily CI rebuild, open PR-based contribution, GA4, 404.
- Real-world signals they lack: GitHub link, ChatGPT/Perplexity citations (14 AI-assistant referrals).

**Our weaknesses independent of them (from the code)**
- Product pages are thin: avg 43-word description, and the "Is X dead?" answer duplicates it; only 7/111 `seo` overrides; sitemap lastmod on `/dead/openai-sora/` is 2026-03-26.
- Four products GSC proves people search for are **not in the data at all**: Hereafter AI, Wsup AI, Jork AI, Weights (`grep` = 0 hits in all three JSONs). Those searchers land on the homepage and find nothing.
- Homepage phrase coverage: "dead ai tools", "ai tools that shut down", "defunct ai", "what ai got shut down" occur **0 times** on `index.html` despite ranking 11 / 13.6 / 1.7 / 4.7. H1 is "Killed by AI"; "ai graveyard" is only in title/H2/hero paragraph.
- Sub-page titles: `/funding/` is 64 chars and matches no query; `/layoffs/` is 63 chars (the brief's "Employee Graveyard" title was replaced in today's commit `30c656d`, so the GSC window predates it); `/api/` H1 is "{ API }".
- No Organization/WebSite JSON-LD with `sameAs` (only Dataset/ItemList/FAQPage/BreadcrumbList).
- Homepage is 292 KB of HTML (111 full cards, no images) — acceptable, and mobile already outranks desktop (6.0 vs 23.9), so the desktop gap is SERP competition, not UX.

## C) Positioning per page (lengths verified)

**1. Homepage `/`**
- Title (50): `Killed by AI — The AI Graveyard: 111 Dead AI Tools`
- H1: `Killed by AI: The AI Graveyard`
- Meta (149): `The AI graveyard: 111 dead AI tools and products that shut down — Sora, GPT-4o, Humane AI Pin — each with launch date, death date, killer and source.`
- Why: brand first holds "killedbyai" / "killed by ai website" (74% CTR); exact "The AI Graveyard" in title+H1 attacks the pos-55 term; "dead AI tools" and "shut down" put the pos-11/13.6 phrases on the page for the first time.

**2. `/layoffs/`**
- Title (52): `AI Layoffs Tracker 2026: 115,633 Jobs Replaced by AI`
- H1: `AI Layoffs Tracker — 115,633 Jobs Replaced by AI`
- Meta (140): `AI layoffs tracker: 115,633 jobs replaced by AI at 30 companies that blamed AI on the record. Date, roles cut and a source for every layoff.`
- Why: exact-match "ai layoffs" (2,500, TP 49k) and "jobs replaced by ai" (450) in title+H1; the number is the click hook and cuts the current 63-char title to fit.

**3. `/funding/`**
- Title (58): `Failed AI Startups: $4.4B of VC Funding Burned (2026 List)`
- H1: `Failed AI Startups: $4.4B Burned`
- Meta (150): `22 failed AI startups and the $4.4B of VC that died with them — Inflection ($1.5B), Olive AI ($902M), Builder.ai — with funding, death date and cause.`
- Why: 214 impressions, 0 clicks at pos 21.9 means the title matches nothing anyone types; "failed AI startups" is the query family, the dollar figure is the differentiator.

**4. `/coming-soon/`**
- Title (57, keep): `Upcoming AI Shutdowns & Model Deprecation Dates (2026–27)`
- H1: `Upcoming AI Shutdowns: the model deprecation calendar`
- Meta (149): `17 AI products with confirmed shutdown dates, counting down: the Sora API (Sept 24), OpenAI Assistants API, GPT-4 and the o-series (Oct 23). Sourced.`
- Why: the title already carries the right phrases; the meta names the three entries with measurable demand ("sora shutdown" 1,000, "openai assistants api deprecation" 40, GPT-4 Oct 23).

**5. `/api/`**
- Title (57): `Killed by AI API: Free JSON of Dead AI Products & Layoffs`
- H1: `Killed by AI API`
- Meta (152): `Free JSON API for the Killed by AI graveyard: 111 dead AI products, 30 AI-blamed layoffs, 17 upcoming shutdowns. No key, no rate limit, CORS, CC BY 4.0.`
- Why: replaces a meaningless "{ API }" H1; "free JSON" + "no key" is what developers search and what makes the page linkable.

All counts should stay templated (`{{COUNT}}`, `{{TOTAL_JOBS}}`) with the existing 60/65-char guard in `build.py` extended to sub-page titles.

## D) Content gaps — 6 additions, ranked by likelihood of capturing the long-tail + Sora

1. **Thicken the 111 product pages (`product-template.html`).** They exist since today but are ~80 words of unique text. Add a dated timeline block (launched → announced → shut down → API off), a `replacement` field (already exists in `coming-soon.json`; add to `graveyard.json`), "What users lost" (26/111 have `collateral`; target 100%), "Alternatives", and a second FAQ pair ("What happened to X?" / "When did X shut down?") so the FAQPage schema carries two questions. Give every entry with GSC impressions a `seo` override (7/111 today). This is the direct landing page for "is chatgpt dead", "dead gpt", "what happened to X", which currently all land on the homepage.

2. **Add the products GSC already proves demand for, then mine GSC weekly.** Hereafter AI, Wsup AI, Jork AI and Weights have impressions (pos 8, 6, 10, 65) and zero coverage. Add each with a source and ship its `/dead/` page. Institutionalize it: a weekly GSC pull of queries matching `(is|why|what happened).*(dead|shut|shutting)` becomes the entry backlog. Cheapest guaranteed traffic on the list.

3. **Sora hub before Sept 24.** Upgrade `/dead/openai-sora/` into the cluster page: a dated timeline, the API countdown pulled live from `coming-soon.json`, "what happened to my Sora videos", "Sora alternatives", the Disney-deal context, and a FAQ set covering "is sora shut down", "sora api shutdown date", "why did openai shut down sora". Link it from the homepage hero (Sora is already in the meta). When the API dies on Sept 24, merge the coming-soon entry into it rather than creating a second page. KD 67 means the head term is a stretch; the long-tail variants are winnable and the date is a news hook.

4. **"Is X dead?" status pages, including alive verdicts and future deaths.** Two extensions of the format that already works: (a) `/dying/<slug>/` pages for every `coming-soon` entry with countdown, dates, replacement and migration notes, 301'd to `/dead/<slug>/` when the date passes — this captures the future-tense queries ("weights ai shutting down", "hereafter ai shutting down 2026", "openai assistants api deprecation"); (b) a small set of honest "alive" pages for products people search as dead ("Is ChatGPT dead? No — but these 14 GPT models are", pos 28 / 11.5 / 8.5 today) that link to the relevant tombstones.

5. **Deprecation calendar + vendor timelines + ICS.** Re-render `/coming-soon/` as a month-by-month calendar, add `/killed-by/<vendor>/` sections for "upcoming" and "deprecation policy", and publish `deprecations.ics`. Developers subscribe to calendars and link to them; it is the one asset in this niche that earns editorial links on its own, and it feeds the per-vendor queries ("openai deprecations", "anthropic model retirement").

6. **Jobs replaced by AI — role index.** Normalize `layoffs.json.roles` into ~15 canonical roles (customer support, sales, recruiting, translators, copywriters, middle management, QA, operations...) and build `/jobs/` plus `/jobs/<role>/` with company count, jobs total, dates and sources per role. Targets "jobs replaced by ai" (450, TP 9,000) and "jobs lost to ai" (200), and removes the competitor's only visible differentiator using data we already hold.

## E) The 5 changes most likely to make us decisively better than killedbyai.xyz (ranked)

1. **Win the brand SERP outright.** File a Change of Address in GSC from the old `mixtpatrik.github.io` property (the 301 exists; Google has not consolidated), add Organization + WebSite JSON-LD with `sameAs` → GitHub, use the exact name "Killed by AI" everywhere, and earn 3–5 real links (Show HN timed to the Sora API death, Product Hunt, a "similar projects" mention from Killed by Google, one journalist who already covered the Sora shutdown). The competitor has zero editorial links; our position trend (39 → 4.6 in a week) says one real link plus consolidation flips #1.

2. **Ship the long-tail machine (D1 + D2 + D4).** 111 answer pages with FAQPage schema, missing entries added, future-tense pages for the 17 upcoming deaths, weekly GSC-driven backlog. Nothing in the snippets suggests .xyz has a single sub-page; this is a structural moat they cannot match with a registry table.

3. **Take "jobs replaced by AI" off their table (C2 + D6).** Retitle `/layoffs/` and add the role index. They own the phrase in a title; we own 115,633 sourced jobs behind it.

4. **Own the Sora cluster before Sept 24 (D3).** ~7,500/mo across "sora ai shutdown" + "sora shutdown" is the only high-volume demand in the niche, we already have the best-titled page for it, and the API shutdown in 15 days is a publishable event.

5. **Make the sub-pages and the hero read "definitive".** Apply the five title/H1/meta sets from C, add contextual homepage links into each sub-page (not just nav), put "sourced, dated, licensed CC BY 4.0, open JSON" in the hero as the counter to their "sourced, dated, and kept", and fix the `/api/` H1. This also gets "dead AI tools" / "ai graveyard" onto the page in H1 for the first time.

Sources: [killedbyai.xyz](https://killedbyai.xyz/), [mixtpatrik/killedbyai on GitHub](https://github.com/mixtpatrik/killedbyai), [mixtpatrik.github.io/killedbyai](https://mixtpatrik.github.io/killedbyai), [killedbyai.net](https://killedbyai.net/), [replaced-by-ai.xyz](https://replaced-by-ai.xyz/), [Killed by OpenAI](https://www.killedbyopenai.com/), [AI Companion Mortality Database](https://aimortality.org/), [LLMDeathCount.com](https://llmdeathcount.com/), [demondragong/deathbyai](https://github.com/demondragong/deathbyai), [The Register — OpenAI kills Sora](https://www.theregister.com/2026/03/25/openai_kills_sora_product_assassin)