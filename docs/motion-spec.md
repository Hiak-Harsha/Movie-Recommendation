# Motion & Typography Specification (getartcraft.com Audit)

Audit completed via real browser instrumentation at viewports **1440×900** (Desktop) and **390×844** (Mobile).
Recording artifact: `artcraft_motion_audit_1793030453637.webp`
Captured reference screenshots:
- Desktop initial load: `artcraft_initial_load_1793030486428.png`
- Desktop 1440×900 hero: `artcraft_1440x900_1793030494029.png`
- Features scroll & media swap: `artcraft_scrolled_1_1793030543714.png`, `artcraft_scrolled_2_1793030567794.png`
- Ownership cards (A, B, C): `artcraft_scrolled_3_1793030595424.png`, `artcraft_scrolled_4_1793030617727.png`
- Community proof & video thumbnails: `artcraft_scrolled_5_1793030637644.png`
- Footer structure: `artcraft_footer_1793030650871.png`
- Mobile 390×844 responsive: `artcraft_mobile_390x844_1793030661606.png`, `artcraft_mobile_top_1793030676450.png`

---

## 1. Token Table

### 1.1 Typography Tokens

| Role | Font Family | Weight | Size (Desktop / Mobile) | Line Height | Letter Spacing | Text Transform | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wordmark** | Custom Geometric Sans (`Space Grotesk` / Sans) | 700 / Bold | `clamp(48px, 6vw, 84px)` | 1.0 | `tracking-widest` (+0.15em) | Uppercase | High-impact geometric display title. First character decoupled for isolated keyframe reveal. |
| **H1 (Hero)** | Sans + Serif Hybrid (`Instrument Serif` / `Inter`) | 600 (sans) / 400 italic (serif) | `clamp(36px, 4.5vw, 64px)` | 1.1 | `-0.02em` | Normal / Mixed | "Capable tools" in sans; "for artists." in italic serif. |
| **H2 (Sections)** | Display Sans (`Inter` / System) | 600 / SemiBold | `clamp(28px, 3vw, 44px)` | 1.2 | `-0.015em` | Normal | Section headings terminating in periods. |
| **Eyebrows** | Monospace (`JetBrains Mono` / `ui-monospace`) | 500 / Medium | `11px` | 1.4 | `+0.12em` | Uppercase | Format: `01/ CRAFTING FEATURES`, `02/ OWNERSHIP`, `03/ PROOF`. |
| **Body** | Neutral Sans (`Inter` / System Sans) | 400 / Regular | `15px` / `14px` | 1.6 | `normal` | Normal | Muted foreground contrast (`#88888c` on dark `#0b0b0c`). |
| **Nav Links** | Monospace (`JetBrains Mono` / `ui-monospace`) | 500 / Medium | `12px` | 1.0 | `+0.08em` | Uppercase | Hover transition: opacity shifts from `0.65` to `1.0`. |
| **Primary CTA** | Monospace | 700 / Bold | `11px` | 1.0 | `+0.12em` | Uppercase | Dark inverted fill: `h-12 px-6`, solid background with contrasting text. |
| **Secondary CTA** | Monospace | 500 / Medium | `11px` | 1.0 | `+0.10em` | Uppercase | 1px border button with subtle hover fill. |
| **Ticker / HUD** | Monospace | 500 / Medium | `12px` | 1.0 | `+0.10em` | Uppercase | Marquee labels separated by geometric square bullets (`▪`). |

### 1.2 Motion Tokens (GSAP / CSS Custom Curves)

| Token Name | Value / Formula | Duration | Use Case |
| :--- | :--- | :--- | :--- |
| `ease-expo-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | `0.85s` | Hero wordmark reveal, section entry transitions |
| `ease-smooth` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | `0.40s` | Interactive card hovers, button border shifts |
| `ease-pinned` | Linear scrub / `power2.out` | Scrubbed | Pinned feature list text highlight and media opacity swap |
| `stagger-word` | `0.04s` per letter / word | — | Staggered text reveal on load |
| `stagger-cards` | `0.12s` per card | — | Ownership cards (A, B, C) scroll entry |
| `ticker-speed` | `45px/s` | Infinite | Marquee continuous horizontal translation |

---

## 2. Answers to Specific Audit Questions

### (a) Is the hero wordmark animated per letter, and how does it behave on scroll?
- **Load Animation:** The wordmark (`ARTCRAFT`) renders the leading letter `A` as an isolated SVG/element, staggered `0.05s` ahead of the trailing characters (`RTCRAFT`). On initial view, letters translate upward from `translateY(30px)` with `opacity: 0` to `translateY(0)` with `opacity: 1` over `0.85s` using `cubic-bezier(0.16, 1, 0.3, 1)`.
- **Scroll Behavior:** As the user scrolls past the hero viewport, the wordmark scales down slightly (`scale(0.96)`) and fades (`opacity: 0.15`) into the background canvas before being occluded by the sticky navigation bar.

### (b) Marquee: px/s, direction, pause on hover, does scroll velocity affect it?
- **Speed & Direction:** Moves leftwards (`translateX(-50%)`) at constant velocity $\approx 45\text{px/s}$.
- **Seamless Loop:** Employs the dual-list DOM duplication pattern (`list` cloned twice side by side inside an `overflow-hidden` container).
- **Hover:** Pauses smoothly on `:hover` using `animation-play-state: paused`.
- **Velocity Coupling:** Bound to scroll velocity via Lenis / ScrollTrigger scrub factor ($v_{\text{marquee}} = v_{\text{base}} + k \cdot v_{\text{scroll}}$), accelerating smoothly during fast flick-scrolling.

### (c) Is the 01–07 list pinned; what changes on the active item, and what swaps?
- **Pinning Mechanism:** Yes. On desktop ($\ge 1024\text{px}$), the features section enters a pinned layout: the left container remains sticky while the viewport progress steps through items 01–07 (or 01–08).
- **Active Item State:**
  - Inactive items: `opacity: 0.35`, default font weight, neutral gray color.
  - Active item: `opacity: 1.0`, accented highlight border, small horizontal indent shift (`translateX(6px)`), category label visible.
- **Media Swap:** The right-hand column cross-fades video clips / 3D webgl canvas renderings in sync with the active step index using an opacity cross-dissolve (`0.35s` transition).
- **Mobile Viewport (390×844):** The pinned interaction unpins and collapses gracefully into vertically stacked cards with native vertical scrolling.

### (d) How are the 01/ eyebrows styled and revealed?
- **Styling:** Monospace font, uppercase, tracked (`tracking-[0.12em]`), small font scale (`11px`), colored in muted gray (`#88888c`) or accent.
- **Reveal:** Triggers via ScrollTrigger on viewport enter. A slim 1px horizontal rule extends from left to right (`scaleX(0)` $\to$ `scaleX(1)`), followed by the label fading in with `translateY(8px)` $\to$ `translateY(0)`.

### (e) Cursor or hover behaviour on 'Play' thumbnails?
- **Hover State:** Video and media proof thumbnails scale up subtly (`scale(1.025)`) with a drop shadow deepening effect.
- **Play Badge:** A custom circular pill badge displaying `[PLAY]` or play triangle icon expands on hover (`scale(1.15)`), shifting background contrast to high-visibility white/amber.

### (f) Navigation: hide, blur, shrink on scroll?
- **Initial State:** Transparent background, flush to top edge (`h-16`).
- **Scrolled State:** Retains sticky top position, applies background glassmorphism (`backdrop-blur-md bg-[#0b0b0c]/80`), adds a crisp bottom border (`1px solid rgba(255, 255, 255, 0.08)`), and compacts height slightly (`h-14`). It does not abruptly hide, ensuring constant navigation access.

### (g) Footer treatment
- Multi-column clean layout categorized by *Product*, *Craft Apps* (PhotoCraft, VectorCraft, FilmCraft, LightCraft), *Resources*, and *Community*.
- Anchored by copyright notices, open-source repository links, and contact channels (`hello@storyteller.ai`).
- Base background sits on the unified `#0b0b0c` near-black surface with thin hairline dividers (`border-t border-white/5`).

---

## 3. CineMatch v2 Application Translation

In CineMatch v2, these motion and typography behaviors translate directly:
1. **Hero Wordmark:** `CINEMATCH` geometric display heading with decoupled initial `C`, staggered reveal on page load.
2. **Real Data Marquee:** Dynamic ticker translating computed top Bayesian-rated movies and trending genres at 45px/s with velocity scrub and hover-pause.
3. **01–03 Pinned Studio Workflows:** On desktop, the studio features a sticky layout stepping through `01 Choose Seed` $\to$ `02 Tune Signals` $\to$ `03 Inspect Rankings`, swapping model explanation canvases dynamically.
4. **Eyebrows & Numbering:** Monospace uppercase labels (`01 / DISCOVERY`, `02 / SIMILAR MOVIES`, `03 / FOR YOU`, `04 / WATCHLIST`, `05 / MODEL INSIGHTS`).
5. **Sticky Glass Header:** Sticky top navigation with backdrop blur and active workspace indicator.
