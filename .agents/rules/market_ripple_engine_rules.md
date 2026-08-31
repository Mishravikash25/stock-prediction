# Project Rules — Market Ripple Engine

## Non-negotiable correctness constraints
- Never fabricate market data, accuracy numbers, or backtest results. If a number can't be computed from real data in this repo, mark it TODO — never invent a plausible-looking one.
- Never claim guaranteed returns or issue unexplained BUY/SELL recommendations. Every report carries a bull case, a bear case, an uncertainty section, a confidence score, and a risk label.
- All time-series splits are chronological (train < validation < test by date) — never random k-fold on time series. No feature may use information not available as of its timestamp.
- Correlation and causation are distinct. Relationship-graph edges get a `strength` score, never a causal claim, unless a cited mechanism is documented.
- Manually-seeded graph relationships are tagged `source: manual_seed`; anything the pipeline infers is tagged `source: inferred` with the method that produced it. Never present a seeded rule as an "AI discovery."
- Do not invent data-source APIs — every connector points at a real, named, currently available source, tagged Free / Freemium / Paid.
- Every stored prediction is later scored against real outcomes (1-day / 7-day / 30-day). Never exclude a losing prediction from reported metrics.

## Locked technical stack — do not substitute without asking
Backend: Python, FastAPI, SQLAlchemy, Pydantic v2, Celery + Redis (jobs/cache).
Data/ML: pandas, numpy, scikit-learn, XGBoost (primary model) with LightGBM as a documented fallback, statsmodels (trend/seasonality), SHAP (feature attribution), imbalanced-learn if class imbalance shows up in labels.
NLP: HuggingFace `transformers`, `ProsusAI/finbert` for sentiment, spaCy (`en_core_web_trf`) for NER, `sentence-transformers` for similarity/dedup. Event classification and bull/bear explanation text: an LLM call behind a strict Pydantic-validated schema, used ONLY for language generation — never for producing the numeric score itself.
Graph: Neo4j (`neo4j` Python driver) as source of truth, `networkx` for local graph algorithms, `node2vec` only for the optional advanced "inferred relationship" path.
Databases: PostgreSQL + TimescaleDB (time series), Neo4j (graph), Redis (cache/broker).
Frontend: React + TypeScript (Vite), Tailwind CSS with CSS variables for theming, `shadcn/ui` primitives, Recharts (line/bar/area charts), `react-force-graph` or Cytoscape.js (ripple map), TanStack Query (data fetching/caching), `next-themes`-style class-based dark/light toggle (see theme spec below — even outside Next.js, replicate the pattern with a `data-theme` attribute).
Testing: pytest + pytest-cov (backend/ML), Vitest + React Testing Library (frontend), Playwright for one end-to-end smoke flow.
Infra: Docker Compose (local), Nginx (reverse proxy), GitHub Actions (CI: lint, test, type-check on every PR).

## UI theme — dark and light, both required
- Implement true light/dark mode via a CSS-variable token system, not two hardcoded stylesheets. Tokens: `--bg`, `--surface`, `--surface-raised`, `--border`, `--text-primary`, `--text-muted`, `--accent-positive` (emerald), `--accent-negative` (amber/red), `--accent-info` (blue), all defined once per theme in `:root[data-theme="dark"]` and `:root[data-theme="light"]`.
- Dark theme: charcoal/near-black background (`#0B0E14`-ish), not pure black; light theme: warm off-white (`#F7F8FA`-ish), not pure white. Both keep the same accent hues, adjusted for contrast (WCAG AA minimum on text).
- Typography: Inter or IBM Plex Sans for UI text, JetBrains Mono (or similar) for numeric/tabular data in both themes.
- A persisted (localStorage) theme toggle in the nav, defaulting to system preference (`prefers-color-scheme`) on first load.
- Financial-terminal density: card-based grids, no gradients or decorative chrome, real whitespace — not a generic AI-template look.

## Engineering hygiene — this must read as a real, human-engineered repo
- No "AI-generated" tells: no boilerplate comment banners, no restating-the-obvious docstrings, no placeholder names like `data1`/`temp`/`foo`, no uniform robotic commit messages. Commits are small, scoped, and describe *why*, not just *what* (e.g. `fix: correct off-by-one in chronological split boundary`, not `update file.py`).
- No `// TODO: implement this` stubs left in delivered code — if something is genuinely out of scope, say so in the design note before writing it, not as a comment litter afterward.
- Comments explain non-obvious decisions (why chronological split, why XGBoost over a neural net here) — not what a line of code obviously does.
- README and docs are written plainly, without marketing language ("cutting-edge," "revolutionary," "leverage AI") — describe what the system does and how to run it.
- Vary function/module structure naturally across the codebase the way a real engineer would — don't produce every file from an identical template with the same section-comment skeleton.
- Use conventional commits and real branch-per-feature git history rather than one giant initial commit dumping the whole repo.
- Do not add a note, comment, or README section stating the project was built with AI assistance or by prompting an agent.

## Working style
- Before writing code for a new module, produce a short design note (schema, interfaces, key algorithm choice) and wait for review.
- Keep the knowledge graph, ML pipeline, and explanation generator as separate, independently testable modules — the explanation layer consumes model outputs, it never invents numbers.
- Every module needs unit tests before it's done. Every ML component documents its train/val/test split strategy.
- Ask before adding a new paid API, cloud service, or dependency with license implications.
