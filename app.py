"""BlogReach Publisher-Advertiser Matching Engine - Streamlit UI.

Run:  streamlit run app.py
"""

import csv
import io

import streamlit as st

from matching_engine import (
    AdvertiserBrief,
    conflict_report,
    load_publishers,
    rank_publishers,
)


def matches_to_csv(ranked, brief_name):
    """Export ranked matches to CSV for sharing with the buying team."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["rank", "publisher", "url", "niche", "price_pkr",
                "traffic_monthly", "domain_authority", "turnaround_days",
                "languages", "match_score", "why"])
    for i, m in enumerate(ranked, 1):
        p = m.publisher
        w.writerow([i, p.name, p.url, p.niche, p.price_pkr,
                    f"{p.traffic_mid:,.0f}", p.domain_authority,
                    p.turnaround_days, "+".join(p.languages),
                    m.score, " | ".join(m.reasons)])
    return buf.getvalue()


def budget_headroom(price_pkr, budget_max_pkr):
    """Human-readable budget-fit indicator for a publisher rate."""
    if budget_max_pkr <= 0:
        return "n/a"
    pct = price_pkr / budget_max_pkr * 100
    if pct <= 60:
        return f"PKR {price_pkr:,}/post - {pct:.0f}% of max budget (comfortable fit)"
    if pct <= 85:
        return f"PKR {price_pkr:,}/post - {pct:.0f}% of max budget (good fit)"
    return f"PKR {price_pkr:,}/post - {pct:.0f}% of max budget (tight fit)"

st.set_page_config(page_title="BlogReach Matching Engine", layout="wide")
st.title("BlogReach - Publisher-Advertiser Matching Engine")
st.caption("Enter an advertiser brief and get ranked publisher matches with explanations.")
st.markdown("Marketplace: [BlogReach.com](https://blogreach.com) — guest-posting marketplace")


@st.cache_data
def get_publishers():
    return load_publishers()


publishers = get_publishers()
niches = sorted({p.niche for p in publishers if p.active})

with st.form("brief_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Advertiser / campaign name", "PhoneHub.pk")
        target_niches = st.multiselect("Target niches", niches, default=["technology"])
        languages = st.multiselect("Content languages (primary first)",
                                   ["en", "ur"], default=["en"])
    with col2:
        budget_min = st.number_input("Min budget per post (PKR)", 0, 10_000_000, 15000, step=1000)
        budget_max = st.number_input("Max budget per post (PKR)", 0, 10_000_000, 35000, step=1000)
        min_traffic = st.number_input("Min monthly traffic", 0, 10_000_000, 50000, step=5000)
        min_da = st.slider("Min domain authority", 0, 100, 25)
    countries = st.multiselect("Target audience countries (optional)",
                               ["Pakistan", "UAE", "UK", "USA"], default=["Pakistan"])
    top_n = st.slider("How many matches to show", 1, 10, 5)
    submitted = st.form_submit_button("Find matches")

if submitted:
    if not target_niches:
        st.error("Pick at least one target niche.")
    elif not languages:
        st.error("Pick at least one content language.")
    elif budget_max < budget_min:
        st.error("Max budget must be >= min budget.")
    else:
        brief = AdvertiserBrief(
            name=name or "Untitled campaign",
            target_niches=target_niches,
            budget_min_pkr=int(budget_min),
            budget_max_pkr=int(budget_max),
            min_monthly_traffic=int(min_traffic),
            min_domain_authority=int(min_da),
            languages=languages,
            target_countries=countries,
        )
        ranked, excluded = rank_publishers(brief, publishers, top_n=top_n)

        for note in conflict_report(brief, publishers, ranked, excluded):
            st.warning(note)

        if not ranked:
            st.info("No publishers fit this brief - see the warnings above for what to change.")
        else:
            st.subheader(f"Top {len(ranked)} matches for '{brief.name}'")
            for i, m in enumerate(ranked, 1):
                p = m.publisher
                with st.container():
                    st.markdown(f"**{i}. [{p.name}]({p.url})** - `{p.niche}` - "
                                f"~{p.traffic_mid:,.0f} visits/mo - "
                                f"DA {p.domain_authority} - {p.turnaround_days}d turnaround - "
                                f"lang: {'+'.join(p.languages)}")
                    st.caption(budget_headroom(p.price_pkr, brief.budget_max_pkr))
                    st.progress(min(m.score / 100.0, 1.0), text=f"Match score: {m.score}/100")
                    with st.expander("Why this match?"):
                        for r in m.reasons:
                            st.write("- " + r)
            st.download_button(
                "Download shortlist as CSV",
                data=matches_to_csv(ranked, brief.name),
                file_name=f"blogreach-shortlist-{brief.name.lower().replace(' ', '-')}.csv",
                mime="text/csv",
            )
        if excluded:
            st.caption(f"{len(excluded)} publishers excluded by hard filters "
                       f"(inactive, over budget, or no shared language).")
