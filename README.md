# 🪦 Killed by AI

**Killed by AI** is a free, open-source cemetery for discontinued Artificial Intelligence projects, products, and companies. As the industry moves from the hype of 2023 to the consolidation of 2026, many tools are being left in the digital dust.

[View the Live Graveyard](https://mixtpatrik.github.io/killedbyai)

---

## ⚰️ Why do AI tools die?
We track tools that have been discontinued due to:
* **Feature Absorption:** When OpenAI/Google/Apple adds a native feature that kills a third-party "wrapper" startup.
* **Model Deprecation:** When legacy models (like GPT-3.5 or Claude 2) are retired for newer versions.
* **Strategic Pivots:** When companies like OpenAI shut down consumer apps (e.g., Sora) to focus on internal AGI.
* **Acqui-hires:** When a giant (like Microsoft) hires the entire staff of a startup (like Inflection), effectively killing the product.

## 🛠️ Tech Stack
* **HTML5 / Tailwind CSS** for a minimalist "Dark Mode" aesthetic.
* **GitHub Pages** for free, lightning-fast hosting.
* **JSON-driven** for easy community contributions.

## 🤝 Contributing
Want to add a fresh tombstone?
1. Fork this repository.
2. Add a new entry to `graveyard.json` with the required fields: `name`, `dateOpen`, `dateClose`, `description`, `type`, `causeOfDeath`, `killedBy`, `link`.
3. Submit a Pull Request with a link to the official shutdown announcement.

The site is built from `graveyard.json` via `python3 build.py`, which regenerates `index.html`, `sitemap.xml`, and `robots.txt`. GitHub Actions runs the build on every push to `main`.

---
*Disclaimer: This project is not affiliated with OpenAI, Google, or the original 'Killed by Google'. It is a community-run archive.*
