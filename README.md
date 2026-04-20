# Minimal pipeline for one cookie-banner dark pattern

This minimal version checks only one structural dark pattern:

- **Accept All** takes 1 click
- **Reject All** takes 2 or more clicks, or is missing entirely

## Files

- `extract_dom.py` — visits the page and extracts visible cookie-banner buttons from layer 1 and layer 2
- `dom_facts.json` — JSON facts produced by the extractor
- `json_to_facts.py` — converts JSON into Souffle `.facts`
- `click_asymmetry.dl` — Souffle rules for click-depth asymmetry

## Step 1: Extract DOM

```bash
python extract_dom.py
```

This writes:
- `dom_facts.json`
- `verdict.txt`

## Step 2: Convert JSON to Souffle facts

```bash
python json_to_facts.py
```

This writes:
- `facts/banner.facts`
- `facts/button.facts`
- `facts/belongs_to.facts`

## Step 3: Run Souffle

```bash
souffle click_asymmetry.dl -F facts -D output
```

Then inspect:

```bash
cat output/dp_click_asymmetry.csv
cat output/dp_no_reject_anywhere.csv
```
