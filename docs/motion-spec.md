# CineMatch Motion & Cinematic Interaction Specification
*Derived from Reference Audit (Gate F) and Movie-Craft Experience Architecture*

---

## 1. Cinematic Design Tokens

### 1.1 Color System
- **Background:** `#0b0b0c` (near-black auditorium base)
- **Surface / Card:** `#121316` (matte cinematic substrate)
- **Line / Border:** `#26282e` (subtle framing boundary)
- **Text (Primary):** `#f2efe6` (warm off-white projection text, ≥ 4.5:1 contrast)
- **Text (Muted):** `#9a9aa0` (subdued neutral for secondary labels)
- **Accent (Amber):** `#f5a524` (projector lamp accent for active highlights, focus rings, progress)
- **Curtain (Deep Crimson):** `#b3202a` (used sparingly, < 5% of any viewport)

### 1.2 Typography Hierarchy
- **Wordmark (`CINEMATCH`):** `Outfit` Display Sans, uppercase, variable weight 700–900, tracking `+0.15em`. Responsive auto-fit spanning width without wrapping.
- **Headlines (H1/H2):** `Outfit` / `Inter`, weight 600, line-height 1.1–1.2, letter-spacing `-0.02em`. Max line length: 18ch for headings.
- **Eyebrows & Rail Labels:** `JetBrains Mono`, weight 500, size `11px`, letter-spacing `+0.12em`, uppercase (`01/ SEARCH`, `02/ TASTE`).
- **Body & Explanations:** `Inter`, weight 400, size `15px`, line-height 1.6. Max line length: 62ch.
- **Numbers / Counters:** `JetBrains Mono` or `tabular-nums` for rock-solid ticker animations without layout reflow.

### 1.3 Motion Timing & Curves
- **Micro Interactions:** `0.20s`, `cubic-bezier(0.16, 1, 0.3, 1)`
- **Interface Shifts:** `0.40s`, `cubic-bezier(0.25, 0.1, 0.25, 1)`
- **Scene Morphs & Cross-Fades:** `0.80s`, `power3.inOut`
- **Text Mask Reveals:** `0.90s`, `expo.out`, stagger `0.035s` per character/word
- **Scroll Smoothing (Lenis):** `lerp: 0.10`, `wheelMultiplier: 0.90`, lagSmoothing disabled (`0`)

---

## 2. Pinned Stage Architecture (Scenes 00–06, Total Length: 700vh)

```
[ Story: 700vh height ]
  └─ [ Stage: position: sticky; top: 0; height: 100svh; overflow: hidden ]
       ├─ [ Background Layer: Drifting Poster Wall, Film Grain, Projector Beam ]
       ├─ [ Left Scene Rail: Pinned Numbers 00–06, Rolling Eyebrow Label ]
       ├─ [ Active Module Slot: Search, Taste, For You, Tune, Library, Closing ]
       └─ [ Floating Dock: Search / Scene Dots / Picks / Library / About Trigger ]
```

### Scene Breakdown & Choreography

| Scene # | Scroll Range | Scene Focus | Stage Visual Choreography | Live Data Endpoint |
|---|---|---|---|---|
| **00** | 0–100vh | **Hero & Wordmark** | 5-column poster wall drifts with 3D perspective (`rotateX(8deg) rotateZ(-6deg)`). Retracting 12vh letterbox bars. Wordmark letters rise from mask. | `GET /api/showcase` |
| **01** | 100–180vh | **Search** | Background wall rack-focuses (blur `0 -> 12px`, scale `1.05 -> 1.0`). Projector beam gradient flickers gently. Center search input emerges with typing placeholder. | `GET /api/search` |
| **02** | 180–300vh | **Taste Onboarding** | Posters fly into an 18-poster grid. Progress ring ticks toward 5 picks (`X of 5`). "Your picks are ready" triggers upon 5 ratings. | `GET /api/onboarding/picks`, `POST /api/me/ratings` |
| **03** | 300–440vh | **For You Shelves** | Taste grid collapses into horizontal strip; recommendation shelves slide in with staggered word-by-word reasons ("Because you liked Alien"). | `GET /api/me/shelves` |
| **04** | 440–540vh | **Tune Faders** | Three fader sliders (Novelty, Diversity, Recency) and genre chips appear. Cards re-order smoothly in response to slider position. | `GET /api/me/recommendations` |
| **05** | 540–620vh | **Tonight's Library** | Saved movies stack into ticket stubs with perforated edges. Direct action to remove (tears stub) or export session history. | `GET /api/me/watchlist` |
| **06** | 620–700vh | **Closing** | Stage releases; dimmed poster wall returns. Closing statement scrubs word opacity from `0.2` to `1.0`. Minimalist footer with About link. | `GET /api/about` |

---

## 3. Responsive Mode Switch
- **Stage Mode:** Active on viewports with width $\ge 1024\text{px}$, height $\ge 640\text{px}$, and `prefers-reduced-motion: no-preference`.
- **Stack Mode:** Automatically activated on tablet/mobile screens ($< 1024\text{px}$) or when reduced motion is toggled on. Renders scenes as natural vertical flow panels with subtle scroll-in fade. Floating dock is replaced by fixed bottom tab bar on viewports $< 768\text{px}$.
