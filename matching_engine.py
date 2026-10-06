#!/usr/bin/env python3
"""
BlogReach Publisher-Advertiser Matching Engine (v2).

Ranks publisher sites for an advertiser brief using a transparent weighted
score out of 100:

  1. Niche fit          (35 pts) - exact niche match, or partial credit for a
                                   related niche.
  2. Budget fit         (25 pts) - sponsored-post rate vs the advertiser's
                                   budget band. A rate above max budget is a
                                   hard exclusion.
  3. Traffic / DA       (25 pts) - monthly traffic (range midpoint) and domain
                                   authority vs the advertiser's minimums.
  4. Content language   (10 pts) - a shared content language is a hard
                                   requirement; primary-language match scores
                                   full marks.
  5. Audience geography ( 5 pts) - bonus when audience countries overlap (or
                                   when the advertiser sets no constraint).

Hard exclusions (not just down-ranked):
  - publisher is inactive
  - publisher's per-post rate exceeds the advertiser's max budget
  - no shared content language

Every match carries a human-readable `reasons` list (explainability), and
`conflict_report()` produces helpful plain-language messages when the brief
is hard to satisfy (e.g. budget too low, no Urdu publishers in the niche).

Data: data/publishers.csv (synthetic dataset generated for this task -
see README.md).

Run the demo:  python3 matching_engine.py
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "data", "publishers.csv")

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Publisher:
    id: str
    name: str
    url: str
    niche: str
    price_pkr: int                 # sponsored post rate
    traffic_min: int               # monthly visits, range low
    traffic_max: int               # monthly visits, range high
    languages: List[str]           # primary first, e.g. ["en", "ur"]
    turnaround_days: int
    domain_authority: int
    active: bool = True

    @property
    def traffic_mid(self) -> float:
        return (self.traffic_min + self.traffic_max) / 2.0


@dataclass
class AdvertiserBrief:
    name: str
    target_niches: List[str]
    budget_min_pkr: int
    budget_max_pkr: int
    min_monthly_traffic: int
    min_domain_authority: int
    languages: List[str]                    # primary first
    target_countries: List[str] = field(default_factory=list)


@dataclass
class Match:
    publisher: Publisher
    score: float
    reasons: List[str] = field(default_factory=list)
    excluded: bool = False
    exclude_reason: str = ""


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

W_NICHE = 35.0
W_BUDGET = 25.0
W_TRAFFIC_DA = 25.0
W_LANGUAGE = 10.0
W_GEO = 5.0

# Partial credit when the publisher's niche is adjacent to a target niche.
RELATED_NICHES: Dict[str, List[str]] = {
    "technology": ["gaming", "business", "education"],
    "gaming": ["technology"],
    "finance": ["business"],
    "business": ["finance", "technology", "education"],
    "education": ["business", "technology"],
    "food": ["lifestyle", "health", "travel"],
    "health": ["food", "lifestyle"],
    "travel": ["lifestyle", "food"],
    "lifestyle": ["home", "fashion", "food", "health", "travel"],
    "fashion": ["lifestyle"],
    "home": ["lifestyle"],
    "sports": [],
}
RELATED_CREDIT = 12.0  # of the 35 niche points


def _norm(tokens: List[str]) -> List[str]:
    return [t.strip().lower() for t in tokens if t and t.strip()]


def niche_score(brief: AdvertiserBrief, pub: Publisher) -> Tuple[float, str]:
    targets = _norm(brief.target_niches)
    niche = pub.niche.strip().lower()
    if niche in targets:
        return W_NICHE, f"exact niche match ({pub.niche}) -> {W_NICHE:.0f}/{W_NICHE:.0f}"
    for t in targets:
        if niche in RELATED_NICHES.get(t, []):
            return RELATED_CREDIT, (
                f"related niche ({pub.niche} ~ {t}) -> {RELATED_CREDIT:.0f}/{W_NICHE:.0f}"
            )
    return 0.0, f"niche {pub.niche} not in target {targets} -> 0/{W_NICHE:.0f}"


def budget_score(brief: AdvertiserBrief, pub: Publisher) -> Tuple[float, str, bool]:
    rate, lo, hi = pub.price_pkr, brief.budget_min_pkr, brief.budget_max_pkr
    if rate > hi:
        return 0.0, f"rate PKR {rate:,} exceeds max budget PKR {hi:,}", True
    if lo <= rate <= hi:
        return W_BUDGET, f"rate PKR {rate:,} inside budget PKR {lo:,}-{hi:,}", False
    closeness = max(0.0, 1.0 - (lo - rate) / lo) if lo else 1.0
    pts = round(W_BUDGET * (0.5 + 0.5 * closeness), 1)
    return pts, f"rate PKR {rate:,} under budget floor PKR {lo:,} (affordable) -> {pts}", False


def traffic_da_score(brief: AdvertiserBrief, pub: Publisher) -> Tuple[float, str]:
    t_ratio = min(pub.traffic_mid / max(brief.min_monthly_traffic, 1), 2.0) / 2.0
    da_ratio = min(pub.domain_authority / max(brief.min_domain_authority, 1), 1.5) / 1.5
    pts = round(W_TRAFFIC_DA * (0.6 * t_ratio + 0.4 * da_ratio), 1)
    return pts, (
        f"traffic ~{pub.traffic_mid:,.0f}/mo (range {pub.traffic_min:,}-{pub.traffic_max:,}) "
        f"vs min {brief.min_monthly_traffic:,}; DA {pub.domain_authority} vs min "
        f"{brief.min_domain_authority} -> {pts}/{W_TRAFFIC_DA:.0f}"
    )


def language_score(brief: AdvertiserBrief, pub: Publisher) -> Tuple[float, str, bool]:
    a, p = set(_norm(brief.languages)), set(_norm(pub.languages))
    shared = a & p
    if not shared:
        return 0.0, f"no shared content language (brief: {brief.languages}, site: {pub.languages})", True
    primary = _norm(brief.languages)[:1] == _norm(pub.languages)[:1]
    pts = W_LANGUAGE if primary else round(W_LANGUAGE * 0.6, 1)
    detail = "primary language match" if primary else f"shared: {sorted(shared)}"
    return pts, f"{detail} -> {pts}/{W_LANGUAGE:.0f}", False


def geo_score(brief: AdvertiserBrief, pub: Publisher) -> Tuple[float, str]:
    # Publisher audience countries are not in the CSV; treat Pakistan as the
    # default audience for this PK marketplace.
    if not brief.target_countries:
        return W_GEO, "no geography constraint set -> full marks"
    targets = {c.strip().lower() for c in brief.target_countries}
    if "pakistan" in targets:
        return W_GEO, "Pakistan-audience marketplace -> full marks"
    return 0.0, f"marketplace audience is Pakistan; brief targets {brief.target_countries}"


def score_match(brief: AdvertiserBrief, pub: Publisher) -> Match:
    m = Match(publisher=pub, score=0.0)
    if not pub.active:
        m.excluded, m.exclude_reason = True, "publisher is inactive"
        return m
    n_pts, n_why = niche_score(brief, pub)
    b_pts, b_why, b_excl = budget_score(brief, pub)
    if b_excl:
        m.excluded, m.exclude_reason = True, b_why
        return m
    l_pts, l_why, l_excl = language_score(brief, pub)
    if l_excl:
        m.excluded, m.exclude_reason = True, l_why
        return m
    t_pts, t_why = traffic_da_score(brief, pub)
    g_pts, g_why = geo_score(brief, pub)
    m.score = round(n_pts + b_pts + t_pts + l_pts + g_pts, 1)
    m.reasons = [n_why, b_why, t_why, l_why, g_why]
    return m


def rank_publishers(brief: AdvertiserBrief,
                    publishers: List[Publisher],
                    top_n: int = 5) -> Tuple[List[Match], List[Match]]:
    scored = [score_match(brief, p) for p in publishers]
    ranked = sorted([x for x in scored if not x.excluded],
                    key=lambda x: x.score, reverse=True)[:top_n]
    excluded = [x for x in scored if x.excluded]
    return ranked, excluded


# ---------------------------------------------------------------------------
# Conflict reporting - helpful messages when the brief is hard to satisfy
# ---------------------------------------------------------------------------

def conflict_report(brief: AdvertiserBrief,
                    publishers: List[Publisher],
                    ranked: List[Match],
                    excluded: List[Match]) -> List[str]:
    """Plain-language diagnostics: why matches are few/missing and what to change."""
    notes: List[str] = []
    langs = _norm(brief.languages)
    lang_ok = [p for p in publishers if p.active and set(_norm(p.languages)) & set(langs)]

    if not ranked:
        notes.append("No publishers match your brief.")
        if lang_ok:
            cheapest = min(lang_ok, key=lambda p: p.price_pkr)
            if cheapest.price_pkr > brief.budget_max_pkr:
                notes.append(
                    f"Budget too low: the cheapest publisher supporting "
                    f"{'/'.join(langs)} charges PKR {cheapest.price_pkr:,} per post "
                    f"({cheapest.name}). Raise your max budget above "
                    f"PKR {cheapest.price_pkr:,} to get matches."
                )
        niche_any = [p for p in publishers
                     if p.active and p.niche.strip().lower() in _norm(brief.target_niches)]
        if not niche_any:
            notes.append(
                f"No publishers cover niche(s) {brief.target_niches} at all - "
                f"try a related niche such as "
                f"{sorted({r for t in _norm(brief.target_niches) for r in RELATED_NICHES.get(t, [])}) or 'technology'}."
            )
        elif not lang_ok:
            notes.append(
                f"{len(niche_any)} publisher(s) cover your niche(s) but none publish in "
                f"{'/'.join(langs)} - try English, or pick a different niche."
            )
        if lang_ok:
            top_traffic = max(lang_ok, key=lambda p: p.traffic_mid)
            if top_traffic.traffic_mid < brief.min_monthly_traffic:
                notes.append(
                    f"Traffic bar too high: the biggest { '/'.join(langs)} publisher "
                    f"({top_traffic.name}) reaches ~{top_traffic.traffic_mid:,.0f}/mo, "
                    f"below your minimum of {brief.min_monthly_traffic:,}/mo."
                )
        return notes

    if len(ranked) < 3:
        notes.append(
            f"Only {len(ranked)} publisher(s) fit your brief - results may be thin. "
            f"Consider widening the budget or lowering the traffic minimum."
        )
    over_budget = [m for m in excluded if "exceeds max budget" in m.exclude_reason]
    if over_budget:
        niche_targets = _norm(brief.target_niches)
        in_niche = [m for m in over_budget
                    if m.publisher.niche.strip().lower() in niche_targets]
        pool = in_niche or over_budget
        cheapest_locked = min(pool, key=lambda m: m.publisher.price_pkr)
        notes.append(
            f"Raising your max budget to PKR {cheapest_locked.publisher.price_pkr:,} would unlock "
            f"{cheapest_locked.publisher.name} ({cheapest_locked.publisher.niche}) "
            f"plus {len(over_budget) - 1} other(s) priced out right now."
        )
    return notes


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_publishers(path: str = DATA_PATH) -> List[Publisher]:
    pubs: List[Publisher] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pubs.append(Publisher(
                id=row["id"].strip(),
                name=row["name"].strip(),
                url=row["url"].strip(),
                niche=row["niche"].strip().lower(),
                price_pkr=int(row["price_pkr"]),
                traffic_min=int(row["traffic_min"]),
                traffic_max=int(row["traffic_max"]),
                languages=[l.strip() for l in row["language"].split("+")],
                turnaround_days=int(row["turnaround_days"]),
                domain_authority=int(row["domain_authority"]),
                active=row["active"].strip().lower() == "yes",
            ))
    return pubs


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _show(brief: AdvertiserBrief, publishers: List[Publisher], top_n: int = 3) -> None:
    ranked, excluded = rank_publishers(brief, publishers, top_n=top_n)
    print(f"\nAdvertiser: {brief.name}")
    print(f"  niches={brief.target_niches} | budget=PKR {brief.budget_min_pkr:,}-{brief.budget_max_pkr:,} | "
          f"min traffic={brief.min_monthly_traffic:,} | min DA={brief.min_domain_authority} | "
          f"lang={brief.languages}")
    if ranked:
        print("  Top matches:")
        for i, m in enumerate(ranked, 1):
            p = m.publisher
            print(f"    {i}. {p.name} ({p.url}) - score {m.score}/100 "
                  f"[PKR {p.price_pkr:,}, ~{p.traffic_mid:,.0f}/mo, DA {p.domain_authority}, {p.turnaround_days}d turnaround]")
            for r in m.reasons:
                print(f"         - {r}")
    for note in conflict_report(brief, publishers, ranked, excluded):
        print(f"  ! {note}")
    if excluded:
        print(f"  ({len(excluded)} publishers excluded by hard filters)")


def demo() -> None:
    pubs = load_publishers()
    print("=" * 78)
    print(f"BlogReach Matching Engine v2 - demo ({len(pubs)} publishers loaded)")
    print("=" * 78)
    _show(AdvertiserBrief("PhoneHub.pk (mobile retailer)",
                          ["technology"], 15000, 35000, 50000, 25, ["en", "ur"],
                          ["Pakistan"]), pubs)
    _show(AdvertiserBrief("DesiSpice Foods",
                          ["food"], 8000, 12000, 30000, 20, ["ur"],
                          ["Pakistan"]), pubs)
    # Conflict case: budget far below every English tech publisher.
    _show(AdvertiserBrief("TinyStartup (impossible brief)",
                          ["technology"], 3000, 5000, 20000, 15, ["en"],
                          ["Pakistan"]), pubs)
    print("\n" + "=" * 78 + "\ndemo complete\n" + "=" * 78)


if __name__ == "__main__":
    demo()
