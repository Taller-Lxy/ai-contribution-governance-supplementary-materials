#!/usr/bin/env python3
"""Reproduce the main event-window estimates from the submitted analysis sample.

Inputs:
- ../02_matched_event_window_sample/item_level_analysis_sample_text_excluded.csv

Outputs:
- reproduced_outputs/rq2_body_formal_regression_results.csv
- reproduced_outputs/rq2_body_robustness_results.csv
- reproduced_outputs/rq3_mechanism_family_results.csv

The submitted analysis sample excludes raw issue/PR bodies and raw maintainer
comment text. It keeps only the variables needed to reproduce the reported
event-window estimates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import build_formal_regression_tables as formal


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH = ROOT / "02_matched_event_window_sample" / "item_level_analysis_sample_text_excluded.csv"
OUT_DIR = ROOT / "05_reproduction_code" / "reproduced_outputs"

RQ2_OUTCOMES = [
    ("body_ai_contribution_disclosure_binary", "Coded explicit AI contribution disclosure", "full"),
    ("body_verification_evidence_binary", "Coded verification evidence", "full"),
    ("closed_without_merge", "PR closed without merge", "pr"),
]

RQ2_ROBUSTNESS_OUTCOMES = [
    ("body_ai_contribution_disclosure_binary", "AI disclosure"),
    ("body_verification_evidence_binary", "Verification evidence"),
]

RQ3_FAMILIES = {
    "post_hoc_query_burden": "事后追问负担",
    "quality_assurance_work": "质量保障审查",
    "coordination_boundary_work": "协调与边界判断",
}


def stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def result_to_rq3_row(
    result: formal.ModelResult,
    mechanism_family: str,
    outcome_kind: str,
    subset: str,
    mode: str = "primary_secondary",
) -> dict[str, Any]:
    return {
        "mode": mode,
        "mechanism_family": mechanism_family,
        "mechanism_family_cn": RQ3_FAMILIES[mechanism_family],
        "outcome_kind": outcome_kind,
        "subset": subset,
        "model_family": result.family,
        "spec": result.spec,
        "treated_x_post_coef": result.coef,
        "cluster_se": result.se,
        "t_stat": result.t,
        "p_value": result.p,
        "stars": stars(result.p),
        "n": result.n,
        "clusters": result.clusters,
        "y_mean": result.y_mean,
        "treated_pre_mean": result.treated_pre_mean,
        "treated_post_mean": result.treated_post_mean,
        "control_pre_mean": result.control_pre_mean,
        "control_post_mean": result.control_post_mean,
        "ppml_pct_effect": "" if result.pct_effect is None else result.pct_effect,
        "convergence": result.convergence,
    }


def load_sample() -> pd.DataFrame:
    if not SAMPLE_PATH.exists():
        raise SystemExit(f"Missing analysis sample: {SAMPLE_PATH}")
    df = pd.read_csv(SAMPLE_PATH, low_memory=False)
    numeric_cols = [
        "treated",
        "post",
        "treated_x_post",
        "is_pr",
        "is_bot_author",
        "closed_without_merge",
        "body_ai_contribution_disclosure_binary",
        "body_verification_evidence_binary",
        "body_coding_confidence",
        "body_coding_needs_human_review",
        "maintainer_comment_count",
    ]
    for family in RQ3_FAMILIES:
        numeric_cols.extend([f"{family}_count", f"{family}_any"])
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def run_rq2_main(sample: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for spec in ["event_fe", "event_fe_controls"]:
        for outcome, label, subset in RQ2_OUTCOMES:
            work = sample.copy()
            if subset == "pr":
                work = work[work["item_type"].astype(str) == "pr"].copy()
            work = work.dropna(subset=[outcome]).copy()
            row = formal.result_to_row(formal.fit_ols(work, outcome, spec))
            row["label"] = label
            row["subset"] = subset
            rows.append(row)
    return pd.DataFrame(rows)


def rq2_variant(sample: pd.DataFrame, variant: str, outcome: str) -> pd.DataFrame:
    if variant == "all_labeled":
        return sample.copy()
    if variant == "exclude_needs_review":
        return sample[pd.to_numeric(sample["body_coding_needs_human_review"], errors="coerce").fillna(0) == 0].copy()
    if variant == "drop_unclear":
        if outcome == "body_ai_contribution_disclosure_binary":
            return sample[sample["body_ai_contribution_disclosure"].astype(str) != "unclear"].copy()
        return sample[sample["body_verification_evidence"].astype(str) != "unclear"].copy()
    if variant == "high_confidence":
        return sample[pd.to_numeric(sample["body_coding_confidence"], errors="coerce").fillna(0) >= 0.70].copy()
    raise ValueError(f"Unknown RQ2 robustness variant: {variant}")


def run_rq2_robustness(sample: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant in ["all_labeled", "exclude_needs_review", "drop_unclear", "high_confidence"]:
        for outcome, label in RQ2_ROBUSTNESS_OUTCOMES:
            work = rq2_variant(sample, variant, outcome).dropna(subset=[outcome]).copy()
            row = formal.result_to_row(formal.fit_ols(work, outcome, "event_fe_controls"))
            row["variant"] = variant
            row["label"] = label
            rows.append(row)
    return pd.DataFrame(rows)


def run_rq3_main(sample: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    count_sample = sample.dropna(subset=["maintainer_comment_count"]).copy()
    for family in RQ3_FAMILIES:
        count_col = f"{family}_count"
        any_col = f"{family}_any"
        for subset in ["all", "pr", "issue"]:
            work = count_sample.copy()
            if subset != "all":
                work = work[work["item_type"].astype(str) == subset].copy()
            for spec in ["event_fe", "event_fe_controls"]:
                rows.append(result_to_rq3_row(formal.fit_ols(work, count_col, spec), family, "count", subset))
                rows.append(result_to_rq3_row(formal.fit_ppml(work, count_col, spec), family, "count", subset))
                rows.append(result_to_rq3_row(formal.fit_ols(work, any_col, spec), family, "any", subset))
    return pd.DataFrame(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = load_sample()
    rq2_main = run_rq2_main(sample)
    rq2_robustness = run_rq2_robustness(sample)
    rq3_main = run_rq3_main(sample)
    rq2_main.to_csv(OUT_DIR / "rq2_body_formal_regression_results.csv", index=False)
    rq2_robustness.to_csv(OUT_DIR / "rq2_body_robustness_results.csv", index=False)
    rq3_main.to_csv(OUT_DIR / "rq3_mechanism_family_results.csv", index=False)
    print(f"Wrote {OUT_DIR / 'rq2_body_formal_regression_results.csv'}")
    print(f"Wrote {OUT_DIR / 'rq2_body_robustness_results.csv'}")
    print(f"Wrote {OUT_DIR / 'rq3_mechanism_family_results.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

