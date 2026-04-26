# Dark Pattern Detection — Formal Means

Detecting missing "Reject All" buttons on cookie consent banners using a formal logic pipeline:  
**Playwright → BeautifulSoup → Soufflé Datalog**

---

## What This Project Does

Cookie consent banners are legally required (under GDPR) to offer users an equally easy way to **reject** cookies as to accept them. A common dark pattern is showing an "Accept All" button prominently while hiding or omitting the "Reject All" option — nudging users into accepting cookies they don't want.

This project automatically:
1. Visits a webpage and **extracts the cookie consent banner HTML**
2. **Parses the banner** into structured DOM facts
3. Uses **formal logic rules (Datalog)** to check whether a "Reject All" button is present
4. Outputs a violation report if the reject button is **missing**

---

## Pipeline Overview

```
Website URL
    │
    ▼  extract_dom.py        (Playwright browser automation)
extracted_cookie_banner.html
    │
    ▼  parse_dom.py          (BeautifulSoup HTML parser)
facts.dl                     (Soufflé Datalog facts + rules)
    │
    ▼  souffle facts.dl      (Datalog engine)
missing_reject.csv           (empty = compliant, non-empty = dark pattern detected)
```

---

## File Structure

```
Dark-pattern-detection-Formal-Means/
├── extract_dom.py               # Stage 1: Scrape and extract cookie banner HTML
├── parse_dom.py                 # Stage 2: Parse HTML into Datalog facts
├── facts.dl                     # Stage 3: Datalog facts + detection rules
├── extracted_cookie_banner.html # Output of Stage 1 (sample: dishoom.com)
├── missing_reject.csv           # Output of Stage 3 (empty = no dark pattern)
├── 2.txt                        # Datalog rules template (rules only, no facts)
└── README.md
```

---

## How Each File Works

### `extract_dom.py` — Cookie Banner Extractor

Uses **Playwright** (a browser automation tool) to load a real webpage in Chromium and run a JavaScript scanner to find the cookie banner.

The scanner applies a **4-stage filter** to every `<div>`, `<section>`, and `<dialog>` on the page:

| Stage | Check | Purpose |
|---|---|---|
| 1 | Accessibility / Render Layer | Must be `position: fixed/sticky/absolute` or a `dialog` role |
| 2 | Visibility | Must have non-zero width/height and not be `display:none` |
| 3 | Keyword Match | Inner text must contain `cookie`, `consent`, `privacy`, or `gdpr` |
| 4 | Button Presence | Must contain at least one `<button>`, `<a>`, or `role="button"` element |

The first element that passes all 4 filters is identified as the cookie banner. Its full `outerHTML` is saved to `extracted_cookie_banner.html`.

It also searches inside **iframes** if the banner is not found in the main DOM (common on sites using third-party cookie managers like CookieYes, OneTrust, etc.).

**Target website (current):** `https://www.dishoom.com/`  
To scan a different site, change the URL in the `__main__` block at the bottom of the file.

---

### `parse_dom.py` — DOM to Datalog Facts

Uses **BeautifulSoup** to parse the extracted banner HTML and convert it into Soufflé Datalog facts.

For every `<div>` and `<button>` element found:
- Writes an `element(id, tag)` fact
- For buttons specifically, also writes a `button_text(id, text)` fact with the button's lowercase inner text

**Example output (`facts.dl` facts section):**
```prolog
element(0, "div").
element(1, "div").
element(6, "button").
button_text(6, "customize").
element(7, "button").
button_text(7, "reject all").
element(8, "button").
button_text(8, "accept all").
```

---

### `facts.dl` — Datalog Detection Rules (Soufflé)

This is the **formal reasoning** heart of the project. It uses [Soufflé](https://souffle-lang.github.io/), a high-performance Datalog engine, to formally verify whether the cookie banner is compliant.

**Declarations:**
```prolog
.decl element(id:number, tag:symbol)
.decl button_text(id:number, text:symbol)
```

**Rule 1 — Detect if a reject button exists:**
```prolog
.decl has_reject_button()
has_reject_button() :- 
    button_text(_, text), 
    contains("reject", text).
```
This rule fires (becomes true) if **any** button's text contains the word "reject".

**Rule 2 — Flag missing reject button (the dark pattern):**
```prolog
.decl missing_reject(message:symbol)
missing_reject("Missing reject button") :- 
    element(_, "button"),
    !has_reject_button().
```
This rule fires if there **is** at least one button on the banner but **none** of them contain "reject". This is the formal definition of the dark pattern being detected.

**Output:**
```prolog
.output missing_reject
```
Soufflé writes results to `missing_reject.csv`.

---

## Sample Run — dishoom.com

The included sample files show a real run against `https://www.dishoom.com/`.

**Banner detected:** A CookieYes-powered consent bar with three buttons — "Customize", "Reject All", "Accept All".

**Facts generated:**
```
element(6, "button") + button_text(6, "customize")
element(7, "button") + button_text(7, "reject all")   ← reject button present
element(8, "button") + button_text(8, "accept all")
```

**Result:** `missing_reject.csv` is **empty** — no dark pattern detected. dishoom.com is **compliant** ✅

---

## Installation

### Prerequisites

- Python 3.8+
- [Soufflé Datalog](https://souffle-lang.github.io/install) engine
- Chromium (installed automatically by Playwright)

### Install Python Dependencies

```bash
pip install playwright beautifulsoup4
playwright install chromium
```

### Install Soufflé

**macOS:**
```bash
brew install souffle-lang/souffle/souffle
```

**Ubuntu/Debian:**
```bash
sudo apt install souffle
```

---

## Running the Pipeline

### Step 1 — Extract the Cookie Banner

```bash
python extract_dom.py
# Output: extracted_cookie_banner.html
```

To scan a different website, edit the URL inside `extract_dom.py`:
```python
result = extract_cookie_layer("https://your-target-website.com/")
```

### Step 2 — Parse HTML into Datalog Facts

```bash
python parse_dom.py
# Output: facts.dl  (with facts prepended to the rules)
```

### Step 3 — Run Formal Verification

```bash
souffle facts.dl
# Output: missing_reject.csv
```

### Step 4 — Read the Result

```bash
cat missing_reject.csv
```

| Result | Meaning |
|---|---|
| File is **empty** | ✅ Reject button found — banner is **GDPR compliant** |
| File contains `"Missing reject button"` | ❌ No reject button — **dark pattern detected** |

---

## How to Scan a New Website (Full Example)

```bash
# 1. Edit the URL in extract_dom.py, then:
python extract_dom.py        # scrapes the site, saves banner HTML

# 2. Regenerate facts from the new banner:
python parse_dom.py          # parses HTML → facts.dl

# 3. Run the formal checker:
souffle facts.dl             # runs Datalog rules

# 4. Check the verdict:
cat missing_reject.csv       # empty = compliant, non-empty = dark pattern
```

---

## Why Formal Logic (Datalog)?

Traditional approaches to detecting dark patterns rely on regex or ML classifiers that can produce false positives and are hard to audit. Using **Datalog**:

- The detection rule is **human-readable and auditable** — exactly one rule defines what "missing reject button" means
- The reasoning is **exhaustive** — Soufflé checks all facts, not a sample
- The rules are **declarative** — you specify *what* to detect, not *how* to search for it
- False positives are **impossible by construction** — the rule only fires when buttons exist but none match "reject"

---

## Limitations

- **Keyword matching only:** Currently detects reject buttons by checking if button text `contains("reject", text)`. Buttons labelled "Decline", "No thanks", or non-English equivalents would not be detected.
- **Single banner per run:** The extractor returns the first cookie banner found. Pages with multiple consent layers are not fully handled.
- **Static snapshot:** The banner is checked at page load. Some sites inject banners after user interaction or after a delay longer than the 4-second wait.
- **No visual analysis:** Button styling (e.g., a grey reject button vs. a bright green accept button — a separate dark pattern) is not checked.

---

## License

See `LICENSE` for details.
