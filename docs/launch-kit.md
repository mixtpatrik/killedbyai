> Generated 2026-09-09 as part of the site audit. Numbers cited were correct at generation time; re-check counts against the live site before posting.

# Killed by AI — Launch Kit

Numbers below are from the live data as of the August 23 build (111 dead, 30 layoff companies / 115,633 jobs, 17 upcoming, $4,383.7M burned). If you run the sweep in section 0 first (recommended), the graveyard becomes 116 and Coming Soon 12 — find/replace before posting.

---

## 0. Before you post anything (one day of work, non-negotiable)

HN and Reddit audit the site in the first ten minutes. These are the things they will find:

1. **Stale "Last updated: August 23, 2026."** Sixteen days old on launch day. Rebuild.
2. **Five Coming Soon entries are already dead** and still on death row: Claude 3 Haiku on Google Cloud (Aug 23), OpenAI Assistants API (Aug 26), DALL·E GPT in ChatGPT (Aug 30), Gemini Robotics-ER 1.6 Preview (Aug 31), Mistral Medium 3 & 3.1 (Aug 31). Move them to `graveyard.json`. That is 116 tombstones, 12 on the clock.
3. **Countdowns are frozen at build time** (`build.py` line 768). The Coming Soon page has said "2d left" on the Assistants API since August 23. Either compute it client-side or add a nightly `schedule:` cron to the Pages workflow. Someone will screenshot this.
4. **Google Analytics (gtag) is on the page.** Do not write "no tracking" anywhere. HN checks.
5. **Do not name, link, or allude to killedbyai.xyz anywhere, ever.** A PBN cannot buy what you are about to earn; naming it hands it relevance.
6. Prepare two chart images for r/dataisbeautiful (section 2.5) and four screenshots for Product Hunt (section 3).
7. Post everything from the person's accounts (Patrik), not a brand account. Every platform below punishes brand-voice posting.

---

## 1. Show HN

**Title (78 chars):**

```
Show HN: Killed by AI – a sourced graveyard of 111 dead AI products and models
```

Alternates (both exactly 80):
- `Show HN: Killed by AI – graveyard of 111 dead AI products, CC BY data + JSON API`
- `Show HN: Killed by AI – 111 discontinued AI products with sources and a JSON API`

**URL:** `https://killedbyai.net/`

**Body:**

```
I've been keeping a list of AI products that got shut down. It started in late March, around the Sora shutdown announcement, with 30 entries. It's now 111: 42 models, 27 services, 19 startups, 18 apps, 5 hardware devices. Every entry has a launch date, a death date, a cause of death, who killed it, and a link to the source (usually the vendor's own deprecation page or shutdown notice).

How it's counted, since this is the first thing people ask: 39 of the 111 are model retirements (GPT-4.5 Preview, Claude 3 Opus, Gemini 2.0 Flash, etc.). They're tagged deathType: model-upgrade and there's a "Hide model upgrades" toggle if you think a deprecation notice isn't a death. The other 72 are killed products, removed features, failed startups, acqui-hires and bricked hardware. Median lifespan of a retired model is 504 days; of everything else, 770.

Some things in the data that surprised me:

- Google Imagen 4.0 on the Gemini API died August 17. The pricing-page banner told developers to migrate to Gemini 2.5 Flash Image, which is scheduled to die October 2, and whose officially recommended replacement, gemini-3.1-flash-image-preview, is already retired. You can follow the migration signage and end up holding three dead model IDs.

- Stainless, the SDK generator used by OpenAI, Google, Cloudflare and Meta to produce their client libraries, was bought by Anthropic in May and the hosted product was wound down. So OpenAI's SDK generator was killed by Anthropic.

- TV Time, a 15-year-old TV-tracking app with millions of users and no AI in it, was shut down in July so its parent company could "refocus on AI products." That changed my definition of the category: it's not only AI that died, it's also what died to make room for AI. (Adobe Animate nearly went the same way after 30 years; backlash got it downgraded to maintenance mode instead.)

Also on the site: 30 companies that blamed AI for 115,633 job cuts (that's what they said, not my judgment; Klarna's 700 replaced agents are in there and so is Klarna's reversal), $4.4B of VC across 22 dead startups, and 17 products with confirmed death dates still ahead. October 23 alone takes gpt-3.5-turbo, gpt-4 and OpenAI's entire first generation of reasoning models.

Build: three JSON files, a Python script that renders HTML templates, GitHub Pages, Actions rebuilds on push. No framework. The data is CC BY 4.0 and served as-is: /graveyard.json, /layoffs.json, /coming-soon.json, plus an RSS feed. No key, no rate limit, CORS on. Code is MIT.

Corrections and missing entries are what I'd most like from this thread, with a source link. Submissions go through a prefilled GitHub issue or a PR. I'd also like to hear whether model retirements belong in the same graveyard at all, since they're 19 of the 46 deaths this year.
```

**HN operating rules:**
- Post Tuesday–Thursday, 8:00–9:30am ET. Not on a day with a major AI launch.
- Never share the HN link asking for votes. Vote-ring detection will bury it and flag the account.
- Be in the thread for the first three hours and answer every comment, including hostile ones, with a source.
- Expected attack lines and the answers: "deprecating a model isn't killing a product" (toggle, deathType field, the 504-vs-770 split); "killedbygoogle clone" (credited in the footer; say so plainly); "layoffs are AI-washing" (agree, that's why the field is what the company claimed; Klarna's reversal is in the data).
- If it sinks without comments, do not immediately repost. HN allows a repost of a Show HN that got no attention after a week or so; email hn@ycombinator.com and ask for the second-chance pool. Reposting on the same day gets it killed.

---

## 2. Reddit

Reread each sidebar the day you post; rules move. Post from a personal account that has comment history in that sub. One sub per day, never two of these on the same day.

### 2.1 r/artificial (Project flair)

**Rules:** Self-promotion is tolerated only under the "Project" flair, disclosed, with the poster present in comments. Bare link-drops and repeat posts get removed.

**Title:**
```
I've been logging every AI product shutdown since March. 111 so far, 46 of them this year. Some patterns from the data.
```

**Body:**
```
Disclosure: I built this. Site is killedbyai.net, data is CC BY 4.0, code is on GitHub.

What's in it: 111 discontinued AI products, models, startups and hardware, each with launch date, death date, cause of death, who killed it, and a source link. Also 30 companies that blamed AI for 115,633 job cuts, and 17 products with confirmed shutdown dates that haven't happened yet.

Things the data shows that I didn't expect:

1. The pace. 10 deaths in 2023, 25 in 2024, 25 in 2025, 46 in the first eight months of 2026. That's 5.8 a month, ~70 by December.

2. The killers are the builders. OpenAI has retired 24 of its own products and models. Google 19. Anthropic 9. Together that's 52 of 111. "Startup crushed by big tech" is a much smaller category than "big tech crushing its own back catalog."

3. Replacements die too. Google Imagen 4.0 died Aug 17 with a banner pointing to Gemini 2.5 Flash Image, which dies Oct 2, whose recommended replacement is already retired.

4. Half the burned VC wasn't lost, it was hired. Of $4.38B across 22 dead startups, $2.15B belongs to acqui-hires: Microsoft took Inflection's team ($1.5B), Amazon took Adept's ($415M), Google took Character.AI's ($150M). The products were left to die.

5. Things die to make room for AI. TV Time (15 years, millions of users, zero AI) was shut down so its parent could "refocus on AI products."

Genuinely want corrections and missing entries. If you know one, link a source and I'll add it.
```

### 2.2 r/singularity

**Rules:** Loose on links, strict on low effort. Discussion prompt required in practice; a bare URL with a title gets downvoted to zero.

**Title:**
```
Frontier models are now retired faster than the products built on them. 39 model retirements tracked, median lifespan 504 days, and it's accelerating.
```

**Body:**
```
I keep a tracker of discontinued AI products (killedbyai.net, open data). The model-retirement subset is the part relevant here.

39 of 111 deaths are model retirements. Median lifespan 504 days. The shortest: Gemini 3 Pro Preview at 111 days, GPT-5.2/5.3 API snapshots at 113 days, GPT-4.5 Preview at 137 days ($75 per million input tokens, deprecated four months after launch). Claude Opus 4.1 was retired exactly one year to the day after release; the model ID carries its own birthday.

19 of this year's 46 deaths are model retirements, up from 11 in 2025. What's coming: October 23, OpenAI removes gpt-3.5-turbo, gpt-4 and the entire first-gen o-series on one day. Azure deletes o1, o3, o4-mini and o3-pro over ~90 days, four with no named replacement. OpenAI deletes every fine-tuned model in existence for orgs on the old system. The GA voice stack (gpt-realtime, gpt-audio, all 4o audio variants) goes January 20.

The question I keep coming back to: if the frontier moves every 15 months, nothing can be built on a specific model anymore, only on the vendor. Is that acceleration, or is it lock-in dressed as acceleration?

Data: killedbyai.net/graveyard.json and /coming-soon.json, CC BY.
```

### 2.3 r/technology

**Rules:** News articles from established outlets only. Self-posts are removed. Personal sites, blogs, and "I built" links are removed on sight, and the account gets flagged. **There is no compliant way to post killedbyai.net here directly.**

**How to comply:**
- Wait for third-party coverage (section 4). When an outlet publishes, submit *their* article, from an account with history in the sub, with the outlet's headline verbatim. Do not submit your own article.
- Until then, contribute data in comments on relevant threads (the Sora API death Sept 24, the Oct 23 OpenAI retirements, any AI-layoff story). Comment template:

```
For scale: 30 companies have now explicitly blamed AI for 115,633 job cuts, 87,955 of them this year. Oracle (30,000) and Citigroup (20,000) are almost half. Klarna is in there twice: 700 agents replaced with a chatbot in 2024, then reversed by 2026 when satisfaction tanked on complex cases. Sourced list here if anyone wants the company-by-company: killedbyai.net/layoffs/
```
A comment with numbers and a link survives. A comment that is only a link does not.

### 2.4 r/programming

**Rules:** Must be about programming. Product launches and marketing pages are removed; technical write-ups and repos are fine. Link the **GitHub repo** (github.com/mixtpatrik/killedbyai), not the homepage, and make the title about the dataset and the developer problem.

**Title:**
```
A dataset of 111 discontinued AI products and 39 retired API models, as plain JSON (CC BY). The deprecation failure modes are worse than the deprecations.
```

**Body (first comment, since it's a link post):**
```
Three JSON files, static, no auth: graveyard.json, layoffs.json, coming-soon.json. Schema is documented at killedbyai.net/api/. Build is a Python script that renders templates from the JSON; Actions rebuilds on push.

The reason I think this belongs here is the failure-mode data, not the count:

- xAI retired eight Grok models on May 15 and silently redirected every retired slug to grok-4.3. Bills and output quality changed with no code change and no error.
- OpenAI auto-upgraded the original gpt-4o API snapshots to GPT-5.1 on March 31. No rollback, no opt-out.
- DeepSeek killed deepseek-chat and deepseek-reasoner at 15:59 UTC on July 24 and told everyone to switch to deepseek-v4-flash with a thinking-mode flag.
- GitHub Models ran two deliberate brownouts (July 16 and 23) before the July 30 shutdown so people would notice. Arguably the most humane deprecation in the set.
- Google Imagen 4.0's shutdown banner pointed to a model that is itself scheduled to die Oct 2, whose recommended replacement is already gone.

Example:
  curl -s https://killedbyai.net/graveyard.json | jq '[.[] | select(.deathType=="model-upgrade")] | length'
  # 39

PRs welcome; every entry needs a source link.
```

### 2.5 r/dataisbeautiful

**Rules:** `[OC]` in the title. Must be an image of a visualization, not a link to a site. A top-level comment from you with **data source** and **tool** is required (AutoMod removes without it). No text-heavy infographics. Post one chart; do not post a variant the same week.

**Chart to make:** horizontal lifespan bars, one per product, launch → death, sorted by launch date, colored by deathType, with Tay (1 day) and Adobe Animate (30 years) labeled. Second chart in reserve: deaths per year 2022–2026 with 2026 marked "through Aug 23."

**Title:**
```
[OC] Lifespan of 111 AI products that have been shut down, launch to death, 2007–2026
```

**Required comment:**
```
Source: killedbyai.net/graveyard.json (CC BY 4.0), 111 entries each with launch date, shutdown date and a source link to the vendor announcement. Tool: Python + matplotlib.

Notes: 39 of the 111 are API model retirements (marked). Median lifespan 591 days overall; 504 for models, 770 for everything else. Shortest: Microsoft Tay, 1 day. Longest: Adobe Animate, 30 years (announced dead, then reprieved to maintenance mode). 25 of the 111 died in under a year.
```

---

## 3. Product Hunt

**Name:** Killed by AI
**Tagline (59 chars):** `A sourced graveyard of every AI product that didn't make it`
Alt (53): `111 dead AI products. 115,633 lost jobs. All sourced.`
**Topics:** Artificial Intelligence, Open Source, Data & Analytics, Developer Tools
**Links:** killedbyai.net, github.com/mixtpatrik/killedbyai
**Gallery:** OG image; the Kill Count Leaderboard; the Coming Soon page with live countdowns; the API docs page.

**Description:**
```
Killed by AI is a cemetery for the models, apps, and startups that didn't survive the AI gold rush. 111 tombstones so far, each with a launch date, a death date, a cause of death, who killed it, what users lost, and a source link.

Alongside the graveyard: 30 companies that blamed AI for 115,633 job cuts, $4.4B of venture funding buried with 22 startups, and a Coming Soon page counting down 17 products with confirmed death dates.

The data is CC BY 4.0 and free as plain JSON. No key, no rate limit. Add a tombstone by pull request or a one-click GitHub issue.
```

**Maker's first comment:**
```
Hi PH. I started this in March, the week Sora got its shutdown date, because I couldn't find a list of what had already been killed. Killed by Google existed for Google; nothing existed for the industry that kills more products per month than Google ever did.

What's on the site: 111 dead products with sources, 30 companies that blamed AI for layoffs, a funding page ($4.4B, roughly half of it acqui-hires where the team was bought and the product left to die), and 17 products with death dates still ahead. October 23 is the big one: gpt-3.5-turbo, gpt-4 and OpenAI's first-gen reasoning models all go the same day.

Two things I'd ask of you. If you know a death that's missing, there's a prefilled GitHub issue; I need a source link, not a memory. And if you build on the JSON (it's CC BY, three endpoints, no auth), tell me here and I'll link to it from the API page.

Not asking for anything else. I'll be in the comments all day.
```

**PH operating rules:** Launch at 12:01am PT, Tuesday–Thursday, on a day with no big AI launch. Hunt it yourself. Reply to every comment within the hour. No upvote requests anywhere, including DMs; PH downranks for it.

---

## 4. Press pitch

**Subject:** 111 dead AI products, 115,633 AI-blamed layoffs, one sourced dataset (free to use)

**Body (136 words):**
```
Hi [First name],

I run Killed by AI (killedbyai.net), a graveyard of discontinued AI products. 111 entries, each with launch date, death date, cause of death, who killed it, and a source link. Alongside it: 30 companies that blamed AI for 115,633 job cuts, $4.4B of VC buried with 22 startups, and 17 products with confirmed death dates still ahead. October 23 alone takes GPT-3.5 Turbo, GPT-4 and OpenAI's entire first-generation o-series.

Two numbers you may find useful: 46 AI products died in the first eight months of 2026, versus 25 in all of 2025. And [HOOK FROM TABLE].

Everything is CC BY 4.0 as plain JSON. Pull it, chart it, no permission needed. Happy to run any cut of the data for you within the hour.

Patrik Rojan
killedbyai.net/api/
```

**Targets.** Verify outlet and address the day you send; these beats move.

| # | Who | Why they'd care | The hook to paste in |
|---|---|---|---|
| 1 | **Brian Merchant**, Blood in the Machine | Full-time on AI and labor; the most-read skeptic of "AI-washed" layoffs | Klarna replaced 700 agents with a chatbot in 2024 and reversed by 2026. GM told 600 IT staff "learn AI or lose your job." Cloudflare cut 1,100 (20%, first mass layoff in 16 years) on record $639.8M revenue after its CEO said AI made "measurers" obsolete. |
| 2 | **Ed Zitron**, Where's Your Ed At / Better Offline | The AI-economics beat; burn rates are his genre | Sora burned ~$1M/day, peaked at ~1M users, dead at six months. Builder.ai's $445M "neural network" was 700 engineers. Yupp.ai hit 1.3M users and still died inside a year. $4.38B buried, $2.15B of it acqui-hires. |
| 3 | **TechCrunch**, byline on "The running list: major tech layoffs in 2026 where employers cited AI" (updated July 25) | They maintain the nearest competing list, at 21 companies | Our list has 30 companies and 115,633 jobs, including ones theirs lacks (Angi 350, Ticketmaster 350, Paycom 500, Chegg 600, Uber 41). Offer the diff and the JSON so their list updates itself. |
| 4 | **Alex Heath**, Sources | Product-strategy insider newsletter on OpenAI, Meta, Google | OpenAI is the deadliest killer of its own products (24). Atlas browser dead in under ten months. Meta's Llama API retired 14 months after LlamaCon. Oct 23: "one date kills three eras." |
| 5 | **Casey Newton**, Platformer | Platform accountability and consumer harm | The "collateral" field, 26 entries: Humane bricked every $699 Pin, no refunds; Moxie bricked $800 robots for autistic kids; ~800K daily GPT-4o users lost it overnight; millions of Doubao/Qwen user-built agents stopped working the day China's rules took effect. |
| 6 | **Simon Willison**, simonwillison.net | Links open datasets and API-deprecation stories to a very large developer audience | Three CC BY JSON endpoints. xAI silently redirected eight retired slugs to grok-4.3 (bills and outputs changed, no code change). GPT-4o API snapshots auto-upgraded to GPT-5.1, no rollback. DeepSeek killed deepseek-chat at 15:59 UTC July 24. |
| 7 | **Gary Marcus**, Marcus on AI | Chronicles AI overpromising; cites trackers as evidence | 46 deaths in eight months vs 25 in 2025. Four dead AI hardware products (Humane $230M, Rabbit $30M, Moxie $54M, Limitless). OpenAI for Science dismantled the same day as Sora. |
| 8 | **Jeremy Kahn**, Fortune, Eye on AI | Enterprise readership; deprecation churn is a CIO-budget problem | Amazon Bedrock Agents frozen in maintenance mode. Assistants API replaced with a full rewrite. Fine-tuning closed to new orgs and every remaining fine-tuned model deleted Oct 23. Azure retiring a whole reasoning generation in ~90 days, four models with no named replacement. |

**Link targets that aren't press but give the editorial backlinks the competitor can't buy:**
- **Data Is Plural** (Jeremy Singer-Vine's weekly dataset newsletter): submit via its form. A listing is a canonical, permanent link from a DR-60s domain to a CC BY dataset. Highest-value single link available to you.
- **Cody Ogden** (Killed by Google): you credit him in the footer. Email, ask for a "related projects" mention on the repo or site. The "Killed by" family cross-links.
- **Roger Lee** (Layoffs.fyi): propose a data exchange; his AI-attributed subset vs yours.
- **GitHub awesome lists**: `jdorfman/awesome-json-datasets`, `awesomedata/awesome-public-datasets`. PRs, with the API page as the link.
- **Newsletter submission forms**: TLDR AI, Ben's Bites, The Neuron, Hacker Newsletter, Changelog News. Submit the HN thread if it front-paged; otherwise the site.

---

## 5. Five stats (exact numbers, ready to post)

Each is under 280 characters. LinkedIn versions: same text, add one line break after the first sentence.

**1. Pace**
```
111 AI products are dead. 46 of them died in the first eight months of 2026, which is 5.8 a month and nearly double all of 2025 (25). On pace for ~70 by December. Every one sourced: killedbyai.net
```

**2. The killers**
```
The deadliest AI company is the one that ships the most. OpenAI has retired 24 of its own products and models. Google 19. Anthropic 9. Between them, 52 of 111 tombstones. "Big tech crushed a startup" is the smaller story; "big tech crushed its own catalog" is the data.
```

**3. Layoffs**
```
30 companies have blamed AI for 115,633 job cuts. 87,955 of those (76%) were announced in 2026. Oracle: 30,000. Citigroup: 20,000. Uber: 41, the first cuts it has ever pinned on AI. Company-by-company, with sources: killedbyai.net/layoffs/
```

**4. Funding**
```
$4.38B of venture capital is in the ground across 22 dead AI startups. Half of it ($2.15B) wasn't lost, it was hired: Microsoft took Inflection's team ($1.5B), Amazon took Adept's ($415M), Google took Character.AI's ($150M). The products were left to die.
```

**5. Record quarter, then the layoffs**
```
Cisco cut ~4,000 jobs one day after reporting $15.8B revenue. Cloudflare cut 1,100 (20%) on record $639.8M revenue, its first mass layoff in 16 years. BILL cut 709 (30%) the day it approved a $1B buyback. 5,809 jobs, all blamed on AI, all within weeks of record numbers.
```

**Spares:**
```
Median lifespan of a dead AI product: 591 days. Microsoft Tay: 1 day. Meta Galactica: 3 days. GPT-4.5 Preview, OpenAI's most expensive model ever at $75 per million input tokens: 137 days. 25 of the 111 didn't reach their first birthday.
```
```
October 23, 2026. One day. OpenAI retires gpt-3.5-turbo (the engine behind the original ChatGPT), gpt-4 (the model that defined 2023), its entire first generation of reasoning models, and every remaining fine-tuned model. 17 products currently have confirmed death dates: killedbyai.net/coming-soon/
```

---

## 6. Posting sequence (today is Tuesday, September 8)

The logic: fix the site, seed the slow links first (they take weeks to land), test on a small audience, fire HN as the single big shot, pitch press the same day with HN as social proof, then spread Reddit and PH across the following week so each one can cite the last. Never two launches on one day. Then ride the three dated deaths in late September, which are real news hooks nobody else has on a calendar.

| Day | Date | Action |
|---|---|---|
| 0 | Tue Sep 8 | Section 0 sweep: 5 dead Coming Soon entries → graveyard (116), rebuild, fix frozen countdowns, "Last updated" current. Verify all three JSON endpoints and CORS from a foreign origin. |
| 1 | Wed Sep 9 | Make the two r/dataisbeautiful charts and four PH screenshots. Write the PH listing and schedule it for Day 9. Verify the 8 press contacts. Send the slow-burn asks: Data Is Plural form, awesome-lists PRs, email Cody Ogden and Roger Lee. |
| 2 | Thu Sep 10 | **r/artificial** (Project flair), 9am ET. This is the dress rehearsal: small audience, real objections. Fix whatever they find that night. |
| 3 | Fri Sep 11 | No launches. Answer comments. Draft replies to the three expected HN attack lines. |
| 4–5 | Sat–Sun | Nothing public. Queue the 5 stats as an X thread and 5 LinkedIn posts (one per day, Days 6–10). |
| 6 | Mon Sep 14 | **r/dataisbeautiful** [OC] chart, 8am ET, with the required source/tool comment. LinkedIn stat 1. |
| 7 | Tue Sep 15 | **Show HN**, 8:30am ET. Post the X thread (stats 1–5) at the same time, linking the site, not the HN thread. Stay in the HN thread until 6pm. If it front-pages, send all 8 press pitches by 2pm ET with "on the HN front page now" as the opening line. If it doesn't, send them Wednesday morning with no mention of HN; the data is the pitch either way. |
| 8 | Wed Sep 16 | **r/singularity**, 9am ET. Fold the best HN objections into the post if it ran. LinkedIn stat 2. |
| 9 | Thu Sep 17 | **Product Hunt**, 12:01am PT. Maker comment live at 12:05. Post the PH link once on X and LinkedIn mid-morning. **r/programming** at 10am ET, linking the GitHub repo. LinkedIn stat 3. |
| 10 | Fri Sep 18 | One-line follow-ups to press non-responders ("Still happy to cut the data any way that helps. New: X died since I wrote."). Newsletter submission forms (TLDR AI, Ben's Bites, The Neuron, Changelog). LinkedIn stat 4. |
| 11–12 | Sat–Sun | Nothing public. Merge community PRs from the week; a visible new-tombstone commit stream is its own proof of life. |
| 13 | Mon Sep 21 | LinkedIn stat 5. If any outlet published, submit *their* article to **r/technology** today from an account with history there. If none did, skip r/technology; there is no compliant alternative. |
| 14 | Tue Sep 22 | Post a "what 3 days on death row looks like" teaser: Sora API dies in 48 hours. Send the Sora-API-death reminder to targets 2, 4 and 7 (they all covered the app shutdown in March). |

**The three dated hooks right after the window (already on your Coming Soon page; nobody else has them on a calendar):**
- **Thu Sep 24:** Sora API dies. Move it to the graveyard within the hour of the endpoint going dark, post the tombstone. This is the news-jack of the month.
- **Mon Sep 28:** davinci-002, babbage-002 and gpt-3.5-turbo-instruct die; the end of the GPT-3 base-model lineage. Second r/programming-worthy moment; comment-worthy on HN whatever thread carries it.
- **Fri Oct 2:** Nano Banana dies, exactly one year after release, with its recommended replacement already dead. Tweet the chain.

Then **October 23** is the next full campaign, and you should start pitching it on October 9: one date, three eras, every fine-tuned model deleted. Your Coming Soon page will be the only place that has been counting down to it since May.