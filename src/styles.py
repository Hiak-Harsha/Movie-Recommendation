"""
CineMatch UI Design System and Custom CSS
Dark cinematic theme with gold and emerald accents, custom cards,
refined typography, pill badges, and workflow containers.
"""

CUSTOM_CSS = """
<style>
/* Base typography and smooth layout */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    letter-spacing: -0.01em;
}

/* App container constraints */
.main .block-container {
    max-width: 1240px;
    padding-top: 1.8rem;
    padding-bottom: 3.5rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* CineMatch Brand Header */
.cinematch-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.6rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(240, 246, 252, 0.1);
    margin-bottom: 1.5rem;
}

.brand-title {
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(135deg, #f5c518 0%, #e5a93c 60%, #ff8c00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}

.brand-badge {
    background: rgba(229, 169, 60, 0.15);
    color: #f5c518;
    border: 1px solid rgba(229, 169, 60, 0.35);
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Workflow Container Card */
.workflow-card {
    background: #161b22;
    border: 1px solid rgba(240, 246, 252, 0.1);
    border-radius: 10px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
}

/* Hero Section */
.hero-box {
    background: radial-gradient(circle at 10% 20%, rgba(229, 169, 60, 0.08) 0%, rgba(22, 27, 34, 0.95) 80%);
    border: 1px solid rgba(229, 169, 60, 0.25);
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
}

.hero-heading {
    font-size: 2.2rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.5rem;
    line-height: 1.2;
}

.hero-sub {
    font-size: 1.05rem;
    color: #8b949e;
    margin-bottom: 1.2rem;
    max-width: 780px;
}

/* Movie Card System */
.movie-card {
    background: #161b22;
    border: 1px solid rgba(240, 246, 252, 0.12);
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.movie-card:hover {
    border-color: rgba(229, 169, 60, 0.4);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
    transform: translateY(-2px);
}

.movie-card-title {
    font-size: 1.15rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.35rem;
    line-height: 1.35;
}

.movie-year {
    color: #8b949e;
    font-size: 0.88rem;
    font-weight: 400;
}

.genre-tag {
    display: inline-block;
    background: rgba(110, 118, 129, 0.18);
    color: #c9d1d9;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    margin-right: 5px;
    margin-bottom: 5px;
}

.score-badge-gold {
    background: rgba(229, 169, 60, 0.18);
    color: #f5c518;
    border: 1px solid rgba(229, 169, 60, 0.4);
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.88rem;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.score-badge-green {
    background: rgba(46, 160, 67, 0.18);
    color: #3fb950;
    border: 1px solid rgba(46, 160, 67, 0.35);
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
}

.evidence-box {
    background: rgba(13, 17, 23, 0.7);
    border-left: 3px solid #e5a93c;
    border-radius: 0 6px 6px 0;
    padding: 8px 12px;
    margin: 10px 0;
    font-size: 0.82rem;
    color: #c9d1d9;
    line-height: 1.45;
}

.stat-tile {
    background: #161b22;
    border: 1px solid rgba(240, 246, 252, 0.1);
    border-radius: 8px;
    padding: 1.1rem;
    text-align: center;
}

.stat-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f5c518;
    margin-bottom: 0.2rem;
}

.stat-label {
    font-size: 0.82rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #0d1117;
}
::-webkit-scrollbar-thumb {
    background: #21262d;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #30363d;
}
</style>
"""


def render_brand_header(active_page_name: str) -> str:
    """Renders the top branding header with navigation context."""
    return f"""
    <div class="cinematch-brand">
        <h1 class="brand-title">CineMatch</h1>
        <span class="brand-badge">Workspace</span>
        <span style="color: #8b949e; font-size: 0.9rem;">&nbsp;•&nbsp; {active_page_name}</span>
    </div>
    """
