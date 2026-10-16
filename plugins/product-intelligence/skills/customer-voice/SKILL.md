---
name: customer-voice
description: "Find and prioritize real customer complaints, requests and underserved jobs across verifiable public reviews, distinguishing sample strength from speculation and turning them into product opportunities."
---

# Customer Voice

Use for product ideas, market gaps, feature prioritization, improving a competitor, pricing complaints or target audience discovery. Extend the already installed research-methodology and fact-check skills; do not repeat them.

## Collect
1. Set product, market, geography, time window and intended decision.
2. Collect actual reviews/comments from permissible public pages, official feeds/APIs and community discussions (App Store, Play, G2, Capterra, Reddit, Hacker News, user boards). Do not bulk scrape against terms. Preserve source, exact URL, date, rating and original quote.
3. Aim for 100+ reviews across 3+ independent sources if available; never represent a smaller sample as representative. Keep praise and mixed ratings, not only complaints. Distinguish duplicates, bots, stale comments and release-version changes.
4. Make a UTF-8 reviews.csv with source,url,date,rating,text,themes. The themes column is the researcher's or model's explicit semantic coding, using exact ids from scripts/themes.json, separated by |. Use none for reviewed text with no matching theme.
5. Read each comment in context and label meaning, negation and multiple relevant issues in its original language. The script does NOT run a language model or validate a label's semantics.

## Analyze
6. When local execution is authorized, run: python3 scripts/reviews.py reviews.csv --require-annotations --out feedback.md. The helper drops unsourced/duplicate rows, checks theme IDs, groups annotated feedback and weights recency/ratings. Without local execution, apply the same steps manually and say what was actually checked.
7. Inspect unattributed/low-rating unmatched complaints manually. Rank by evidence volume, source diversity, recency, segment relevance, severity and feasibility, not only a generated numeric rank.
8. Cross-check whether a complaint was fixed in a recent changelog. Create 5-8 potential fixes with evidence, effort and differentiating value. Separate HATE (existing flaw), MISSING (specific request) and UNSERVED (new customer job).
9. For commercial positioning propose at most three evidence-grounded angles, including target segment and pricing hypothesis. Claims remain hypotheses until validated with users.

## Outputs
Save research/competitors/<slug>/reviews.csv, feedback.md and opportunities.md by default. Report sample size, sources, dates, quotes linked to originals, thin evidence and candidate opportunities. Never invent quotes, counts or demand. Do not use competitor reviewers' words as your own testimonials.

## Source
Adapted from Jake Schincariol's replica-entrepreneur: https://github.com/Jakeschincariol/replica-skill (MIT; exact pin in ../../references/UPSTREAM.md).
