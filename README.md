# BlogReach Publisher-Advertiser Matching Engine

Takes an advertiser's requirements (niche, budget, audience/traffic needs,
preferred metrics, language) and ranks suitable publisher sites for buying
SEO guest-post placements, with a clear explanation for every match and
helpful messages when requirements conflict or cannot be met.

## Approach

Transparent weighted scoring out of 100 per publisher:

| Signal | Weight | Rule |
|---|---|---|
| Niche fit | 35 | Exact niche match; 12 pts partial credit for a related niche (e.g. gaming ~ technology) |
| Budget fit | 25 | Post rate inside the budget band; rate above max budget is a hard exclusion |
| Traffic / DA | 25 | Traffic-range midpoint and domain authority vs the brief's minimums |
| Content language | 10 | A shared language is a hard requirement; primary-language match scores full marks |
| Audience geography | 5 | Bonus for Pakistan-audience overlap (or full marks when no constraint is set) |

Hard exclusions (not just down-ranked): inactive publishers, rate above max
budget, no shared content language. Every match carries a `reasons` list so
the marketplace UI can show *why* a site was recommended. `conflict_report()`
diagnoses unsatisfiable briefs, e.g. "Budget too low: the cheapest publisher
supporting en charges PKR 9,000 per post - raise your max budget above
PKR 9,000", or how much budget unlocks the next publisher.

## Data source

`data/publishers.csv` - **44 publisher sites, fully synthetic data generated
for this task** (names, URLs use `example.com`, prices, traffic ranges, DA
figures are invented). It is a stand-in so the engine, UI, and evaluation can
be built and tested end-to-end. Production use requires replacing it with
real BlogReach marketplace listings (live rate cards, Similarweb/Moz-style
traffic and authority data).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional; fill in real values, never commit .env
```

## Usage

```bash
# CLI demo (3 briefs, including a conflict case)
python3 matching_engine.py

# Evaluation against 20 judged scenarios
python3 evaluation.py

# Web UI
streamlit run app.py
```

## Evaluation

`test_scenarios.csv` holds 20 advertiser scenarios, each with a manually
judged expected top publisher (one scenario, S16, expects no match plus a
budget warning). `evaluation.py` ranks publishers per scenario and reports:

- **Top-1 accuracy: 100%** (20/20)
- **Top-3 hit rate: 100%** (20/20)

Full per-scenario table and analysis: `evaluation_report.md`.

## Limitations

- The dataset is synthetic (`example.com` URLs, invented metrics); rankings
  reflect the invented data, not the real market.
- The 20 scenarios were judged against the same synthetic dataset the engine
  scores, so the evaluation measures ranking consistency, not real-world
  precision. Real validation needs historical BlogReach campaign data.
- Audience geography is simplified (Pakistan-audience marketplace default);
  per-publisher audience countries are not in the dataset yet.
- No persistence, auth, or rate limiting - this is a ranking prototype, not
  a production service.
---
## Built for BlogReach
SEO outreach for this project via [BlogReach](https://blogreach.com) — the guest-posting marketplace.
