"""
CineMatch Design System (Studio Layout)
Near-black palette (#0b0b0c), restrained amber accent (#e5a93c),
1px borders, tabular numerals, eyebrow labels, and typographic poster tiles.
"""

STUDIO_CSS = """
<style>
/* Clean system font stack - zero external CDN calls */
body, [class*="css"], .stApp {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #0b0b0c;
    color: #e6edf3;
    letter-spacing: -0.01em;
}

/* Base container constraints */
.main .block-container {
    max-width: 1440px;
    padding-top: 1.5rem;
    padding-bottom: 3.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Tabular numerals for scores and metrics */
.tabular-nums {
    font-variant-numeric: tabular-nums;
}

/* Eyebrow Label */
.eyebrow {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #e5a93c;
    margin-bottom: 0.35rem;
}

/* Step Indicator (01 CHOOSE · 02 TUNE · 03 REVIEW) */
.step-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 14px;
    background: #121316;
    border: 1px solid #26282e;
    border-radius: 6px;
    margin-bottom: 1.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #8b949e;
}

.step-active {
    color: #e5a93c;
}

.step-arrow {
    color: #484f58;
}

/* Studio Ticker Strip */
.ticker-strip {
    display: flex;
    align-items: center;
    gap: 16px;
    overflow-x: auto;
    padding: 10px 16px;
    background: #121316;
    border: 1px solid #26282e;
    border-radius: 6px;
    margin-bottom: 1.5rem;
    font-size: 0.82rem;
    white-space: nowrap;
}

.ticker-label {
    color: #e5a93c;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-right: 4px;
}

.ticker-item {
    color: #c9d1d9;
    padding: 3px 8px;
    background: #18191d;
    border: 1px solid #30333b;
    border-radius: 4px;
}

/* Typographic Poster Tile */
.poster-tile {
    width: 64px;
    height: 84px;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    flex-shrink: 0;
}

.poster-letter {
    font-size: 1.8rem;
    line-height: 1;
}

.poster-year {
    font-size: 0.65rem;
    font-weight: 600;
    margin-top: 4px;
    opacity: 0.85;
}

/* Badge System */
.badge-genre {
    display: inline-block;
    background: #18191d;
    color: #c9d1d9;
    border: 1px solid #30333b;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 0.72rem;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
}

.badge-score {
    background: rgba(229, 169, 60, 0.12);
    color: #e5a93c;
    border: 1px solid rgba(229, 169, 60, 0.35);
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 0.82rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}

.evidence-quote {
    background: #121316;
    border-left: 2px solid #e5a93c;
    padding: 6px 10px;
    margin: 8px 0;
    font-size: 0.8rem;
    color: #c9d1d9;
    line-height: 1.4;
    border-radius: 0 4px 4px 0;
}

/* Inspector Panel */
.inspector-card {
    background: #121316;
    border: 1px solid #26282e;
    border-radius: 8px;
    padding: 1.2rem;
    margin-bottom: 1.2rem;
}

.imdb-link {
    color: #e5a93c;
    text-decoration: none;
    font-size: 0.78rem;
    font-weight: 600;
}
.imdb-link:hover {
    text-decoration: underline;
}

/* Streamlit Header / Clean-up */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""


def render_studio_header(page_eyebrow: str, page_title: str, subtitle: str) -> str:
    """Renders the top title block with eyebrow label and subtitle."""
    return f"""
    <div style="margin-bottom: 1.5rem;">
        <div class="eyebrow">{page_eyebrow}</div>
        <h1 style="font-size: 2.1rem; font-weight: 700; color: #ffffff; margin: 0 0 0.4rem 0;">{page_title}</h1>
        <div style="color: #8b949e; font-size: 0.95rem;">{subtitle}</div>
    </div>
    """


def render_step_bar(step_1: str, step_2: str, step_3: str, active_step: int = 1) -> str:
    """Renders the workflow step indicator: 01 Choose · 02 Tune · 03 Review."""
    cls_1 = "step-active" if active_step >= 1 else ""
    cls_2 = "step-active" if active_step >= 2 else ""
    cls_3 = "step-active" if active_step >= 3 else ""

    return f"""
    <div class="step-bar">
        <span class="{cls_1}">01 {step_1}</span>
        <span class="step-arrow">→</span>
        <span class="{cls_2}">02 {step_2}</span>
        <span class="step-arrow">→</span>
        <span class="{cls_3}">03 {step_3}</span>
    </div>
    """
