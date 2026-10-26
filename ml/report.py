"""
CineMatch Offline Evaluation Report Generator
Reads artifacts/eval_results.json and generates docs/eval_report.md
and updates the offline evaluation table in README.md.
"""
import json
import logging
from pathlib import Path
import re

from ml.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cinematch.ml.report")


def generate_report(eval_json_path: Path = settings.artifacts_dir / "eval_results.json") -> str:
    if not eval_json_path.exists():
        raise FileNotFoundError(f"Missing {eval_json_path}. Run: python -m ml.evaluation")

    with open(eval_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sizes = data.get("sample_sizes", {})
    rpm = data.get("rating_prediction_metrics", {})
    strat = data.get("strategy", {})
    tm = data.get("test_metrics", {})
    curves = data.get("cold_start_curves", {})
    fp = data.get("dataset_fingerprint", "unknown")

    lines = [
        "# CineMatch Offline Evaluation Benchmark Report",
        "",
        f"**Dataset Fingerprint:** `{fp}`  ",
        f"**Evaluation Protocol:** Primary Per-User Temporal Holdout (70% Train / 10% Validation / 20% Test)  ",
        f"**Evaluated At:** `{data.get('evaluated_at', 'N/A')}`  ",
        "",
        "## 1. Sample Sizes & Statistical Power",
        "",
        f"- **Total Clean Ratings Evaluated:** {sizes.get('train_ratings', 0) + sizes.get('val_ratings', 0) + sizes.get('test_ratings', 0):,}  ",
        f"- **Train Ratings (70%):** {sizes.get('train_ratings', 0):,}  ",
        f"- **Validation Ratings (10%):** {sizes.get('val_ratings', 0):,}  ",
        f"- **Held-Out Test Ratings (20%):** {sizes.get('test_ratings', 0):,}  ",
        f"- **Evaluated Test Users ($n$):** **{sizes.get('eligible_test_users', 0)}** (users with $\\ge 1$ relevant item with rating $\\ge 4.0$)  ",
        f"- **Evaluated Test Rating Pairs:** **{rpm.get('pairs_count', 0):,}**  ",
        "",
        "## 2. Collaborative Rating Prediction Error",
        "",
        f"- **Test RMSE:** `{rpm.get('test_rmse', 0.0):.4f}`  ",
        f"- **Test MAE:** `{rpm.get('test_mae', 0.0):.4f}`  ",
        f"*(Computed across {rpm.get('pairs_count', 0):,} held-out rating pairs)*",
        "",
        "## 3. Top-10 Ranking Evaluation Benchmark (with 95% Bootstrap CIs)",
        "",
        "| Model Pipeline | Test NDCG@10 (95% CI) | Test Recall@10 (95% CI) | Test HitRate@10 (95% CI) | Novelty@10 | Diversity@10 | Catalog Coverage | Evaluated Users ($n$) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for model_name, m in tm.items():
        ndcg_str = f"**{m['ndcg']['mean']:.4f}** `[{m['ndcg']['ci_lower']:.4f}, {m['ndcg']['ci_upper']:.4f}]`"
        recall_str = f"`{m['recall']['mean']:.4f}` `[{m['recall']['ci_lower']:.4f}, {m['recall']['ci_upper']:.4f}]`"
        hit_str = f"`{m['hit_rate']['mean']*100:.1f}%` `[{m['hit_rate']['ci_lower']*100:.1f}%, {m['hit_rate']['ci_upper']*100:.1f}%]`"
        nov_str = f"`{m.get('novelty', {}).get('mean', 0.0):.2f}`"
        div_str = f"`{m.get('diversity', {}).get('mean', 0.0):.2f}`"
        cov_str = f"`{m.get('catalog_coverage', 0.0)*100:.1f}%`"
        n_u = m.get("n_evaluated_users", sizes.get("eligible_test_users", 0))

        lines.append(f"| **{model_name}** | {ndcg_str} | {recall_str} | {hit_str} | {nov_str} | {div_str} | {cov_str} | {n_u} |")

    lines.extend([
        "",
        "## 4. Cold-Start Curves (Ratings Truncated to $k$)",
        "",
        "| Cold-Start Rung ($k$ ratings) | NDCG@10 Mean | HitRate@10 Mean | Pipeline Mode |",
        "| :--- | :--- | :--- | :--- |",
    ])

    for k_key, c_data in curves.items():
        k_val = c_data.get("ratings_count", 0)
        mode_str = "Popularity Baseline" if k_val == 0 else ("Content Fallback" if k_val < 5 else "Full Hybrid ALS Fold-in")
        lines.append(f"| **k = {k_val} ratings** | `{c_data.get('ndcg_mean', 0.0):.4f}` | `{c_data.get('hit_rate_mean', 0.0)*100:.1f}%` | {mode_str} |")

    lines.extend([
        "",
        "## 5. Quality Gate Verdict",
        "",
        f"- **Live Serving Strategy:** `{strat.get('selected_model', 'Popularity Baseline')}`  ",
        f"- **Hybrid Superiority Verified:** `{strat.get('is_hybrid_superior', False)}`  ",
        f"- **Rationale:** {strat.get('rationale', 'N/A')}  ",
        "",
        "> [!NOTE]",
        "> On long-tail power-law rating datasets evaluated with strict temporal holdouts, popular universally acclaimed classics remain exceptionally strong ranking candidates. CineMatch ships the quality-gate-selected strategy for default global ranking while offering full interactive personalized hybrid exploration in the studio.",
        ""
    ])

    report_content = "\n".join(lines)

    # Save to docs/eval_report.md
    docs_dir = settings.project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / "eval_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    logger.info(f"Generated {report_path}")

    # Update README.md Section 4
    readme_path = settings.project_root / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        # Find section 4
        sec4_header = "## 4. Offline Evaluation Benchmark & Quality Gate"
        sec5_header = "## 5. Studio Workspaces & UI Design"
        if sec4_header in readme_text and sec5_header in readme_text:
            before_sec4 = readme_text.split(sec4_header)[0]
            after_sec4 = readme_text.split(sec5_header)[1]

            new_sec4_content = f"""{sec4_header}

### Protocol Specifications
- **Primary Protocol:** Per-user temporal holdout (70% train / 10% validation / 20% test).
- **Statistical Power:** **{sizes.get('eligible_test_users', 0)} evaluated users** (with $\\ge 1$ relevant item with rating $\\ge 4.0$) across **{rpm.get('pairs_count', 0):,} held-out test pairs**.
- **Data Leakage Sentinel:** All IDF vocabularies, tag dictionaries, popularity priors, and user/item factors are computed strictly from pre-cutoff data.

### Test Split Results (with 95% Bootstrap Confidence Intervals)

| Recommender Pipeline | Test NDCG@10 (95% CI) | Test Recall@10 (95% CI) | Test HitRate@10 (95% CI) | Catalog Coverage | Evaluated Users ($n$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
            for model_name, m in tm.items():
                ndcg_str = f"**{m['ndcg']['mean']:.4f}** `[{m['ndcg']['ci_lower']:.4f}, {m['ndcg']['ci_upper']:.4f}]`"
                recall_str = f"`{m['recall']['mean']:.4f}` `[{m['recall']['ci_lower']:.4f}, {m['recall']['ci_upper']:.4f}]`"
                hit_str = f"`{m['hit_rate']['mean']*100:.1f}%` `[{m['hit_rate']['ci_lower']*100:.1f}%, {m['hit_rate']['ci_upper']*100:.1f}%]`"
                cov_str = f"`{m.get('catalog_coverage', 0.0)*100:.1f}%`"
                n_u = m.get("n_evaluated_users", sizes.get("eligible_test_users", 0))
                new_sec4_content += f"| **{model_name}** | {ndcg_str} | {recall_str} | {hit_str} | {cov_str} | {n_u} |\n"

            new_sec4_content += f"""
### Collaborative Rating Prediction Accuracy
- **Test RMSE:** `{rpm.get('test_rmse', 0.0):.4f}` across {rpm.get('pairs_count', 0):,} held-out test pairs
- **Test MAE:** `{rpm.get('test_mae', 0.0):.4f}` across {rpm.get('pairs_count', 0):,} held-out test pairs

### Quality Gate Outcome
- **Selected Model:** `{strat.get('selected_model', 'Popularity Baseline')}`
- **Quality Gate Rule:** If the hybrid model does not exceed the best single component on validation NDCG@10, the system ships the best single model and honestly discloses it.
- **Validation Outcome:** {strat.get('rationale', 'N/A')}

---

{sec5_header}{after_sec4}"""
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(before_sec4 + new_sec4_content)
            logger.info("Updated README.md Section 4 with script-generated evaluation table.")

    return report_content


if __name__ == "__main__":
    generate_report()
