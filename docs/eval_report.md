# CineMatch Offline Evaluation Benchmark Report

**Dataset Fingerprint:** `8aaa97d2eb36dd06`  
**Evaluation Protocol:** Primary Per-User Temporal Holdout (70% Train / 10% Validation / 20% Test)  
**Evaluated At:** `2026-10-26 16:42:24 UTC`  

## 1. Sample Sizes & Statistical Power

- **Total Clean Ratings Evaluated:** 100,836  
- **Train Ratings (70%):** 70,312  
- **Validation Ratings (10%):** 9,818  
- **Held-Out Test Ratings (20%):** 20,706  
- **Evaluated Test Users ($n$):** **591** (users with $\ge 1$ relevant item with rating $\ge 4.0$)  
- **Evaluated Test Rating Pairs:** **20,706**  

## 2. Collaborative Rating Prediction Error

- **Test RMSE:** `0.9389`  
- **Test MAE:** `0.7225`  
*(Computed across 20,706 held-out rating pairs)*

## 3. Top-10 Ranking Evaluation Benchmark (with 95% Bootstrap CIs)

| Model Pipeline | Test NDCG@10 (95% CI) | Test Recall@10 (95% CI) | Test HitRate@10 (95% CI) | Novelty@10 | Diversity@10 | Catalog Coverage | Evaluated Users ($n$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Baseline** | **0.0015** `[0.0005, 0.0026]` | `0.0007` `[0.0001, 0.0015]` | `1.4%` `[0.5%, 2.4%]` | `15.61` | `0.84` | `45.5%` | 591 |
| **Popularity Baseline** | **0.0596** `[0.0496, 0.0692]` | `0.0347` `[0.0275, 0.0410]` | `28.8%` `[24.9%, 32.1%]` | `9.17` | `0.75` | `0.5%` | 591 |
| **Content-Only** | **0.0047** `[0.0024, 0.0070]` | `0.0018` `[0.0009, 0.0028]` | `3.4%` `[1.9%, 5.1%]` | `15.33` | `0.23` | `25.9%` | 591 |
| **Item-kNN CF** | **0.0130** `[0.0097, 0.0162]` | `0.0085` `[0.0054, 0.0118]` | `9.0%` `[6.8%, 11.0%]` | `12.88` | `0.75` | `6.0%` | 591 |
| **Explicit ALS** | **0.0437** `[0.0362, 0.0500]` | `0.0254` `[0.0210, 0.0304]` | `24.2%` `[20.6%, 27.4%]` | `10.46` | `0.78` | `4.8%` | 591 |
| **CineMatch Hybrid** | **0.0418** `[0.0331, 0.0502]` | `0.0304` `[0.0235, 0.0372]` | `21.8%` `[17.9%, 24.4%]` | `11.62` | `0.59` | `3.4%` | 591 |

## 4. Cold-Start Curves (Ratings Truncated to $k$)

| Cold-Start Rung ($k$ ratings) | NDCG@10 Mean | HitRate@10 Mean | Pipeline Mode |
| :--- | :--- | :--- | :--- |
| **k = 0 ratings** | `0.0509` | `31.0%` | Popularity Baseline |
| **k = 3 ratings** | `0.0029` | `3.0%` | Content Fallback |
| **k = 5 ratings** | `0.0288` | `18.0%` | Full Hybrid ALS Fold-in |
| **k = 10 ratings** | `0.0315` | `20.0%` | Full Hybrid ALS Fold-in |
| **k = 20 ratings** | `0.0272` | `18.0%` | Full Hybrid ALS Fold-in |

## 5. Quality Gate Verdict

- **Live Serving Strategy:** `Popularity Baseline`  
- **Hybrid Superiority Verified:** `False`  
- **Rationale:** Quality Gate Notice: Single model 'Popularity Baseline' (0.0433) achieved highest validation NDCG@10 over Hybrid (0.0393). Shipping 'Popularity Baseline'.  

> [!NOTE]
> On long-tail power-law rating datasets evaluated with strict temporal holdouts, popular universally acclaimed classics remain exceptionally strong ranking candidates. CineMatch ships the quality-gate-selected strategy for default global ranking while offering full interactive personalized hybrid exploration in the studio.
