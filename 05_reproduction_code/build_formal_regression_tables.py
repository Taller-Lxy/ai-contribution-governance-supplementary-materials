#!/usr/bin/env python3
"""Build formal item-level mechanism regression tables.

The project environment does not assume statsmodels. This script therefore
implements the small set of estimators we need directly:

- LPM / OLS with treated-event clustered standard errors.
- PPML via IRLS with treated-event clustered sandwich standard errors.

The coefficient of interest is always `treated_x_post`.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import linalg
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

TREATED_AUDIT = DATA / "early_workflow_audit_items.csv"
CONTROL_AUDIT = DATA / "control_workflow_audit_items.csv"
MATCHED = DATA / "matched_control_events_final.csv"
COMMENT_CLASS = DATA / "maintainer_comment_mechanism_classification.csv"

SAMPLE_OUT = DATA / "formal_regression_item_sample.csv"
RESULTS_OUT = DATA / "formal_regression_results.csv"
REPORT_OUT = REPORTS / "formal_regression_tables.md"

MECHANISM_COUNT_VARS = [
    "information_clarification",
    "action_request",
    "quality_correctness",
    "verification_testing",
    "integration_project_fit",
    "responsibility_provenance_ai",
    "security_risk",
    "rejection_moderation",
    "coordination_management",
    "social_acknowledgement",
    "other_nonmechanism",
    "not_maintainer_substantive",
]

MECHANISM_COUNT_COLS = {
    var: f"mech_{var}_count" for var in MECHANISM_COUNT_VARS
}


@dataclass
class ModelResult:
    outcome: str
    family: str
    spec: str
    coef: float
    se: float
    t: float
    p: float
    n: int
    clusters: int
    y_mean: float
    treated_pre_mean: float
    treated_post_mean: float
    control_pre_mean: float
    control_post_mean: float
    convergence: str = ""
    pct_effect: float | None = None


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def norm_number(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    if text.endswith(".0"):
        text = text[:-2]
    try:
        return str(int(float(text)))
    except Exception:
        return text


def clean_error_mask(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def build_event_id_map(treated: pd.DataFrame) -> Dict[Tuple[str, str, str], str]:
    keys = (
        treated[["event_repo", "event_path", "adoption_date"]]
        .drop_duplicates()
        .sort_values(["event_repo", "event_path", "adoption_date"])
    )
    out: Dict[Tuple[str, str, str], str] = {}
    for idx, row in enumerate(keys.itertuples(index=False), start=1):
        out[(row.event_repo, row.event_path, row.adoption_date)] = f"TE{idx:03d}"
    return out


def bool01(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    s = str(value).strip().lower()
    if s in {"1", "1.0", "true", "yes"}:
        return 1.0
    if s in {"0", "0.0", "false", "no"}:
        return 0.0
    try:
        return 1.0 if float(s) != 0 else 0.0
    except Exception:
        return np.nan


def prepare_audit_sample() -> pd.DataFrame:
    treated = read_csv(TREATED_AUDIT)
    control = read_csv(CONTROL_AUDIT)
    matched = read_csv(MATCHED)

    event_map = build_event_id_map(treated)
    treated = treated.copy()
    treated["group"] = "treated"
    treated["treated"] = 1
    treated["treated_event_id"] = [
        event_map.get((r.event_repo, r.event_path, r.adoption_date), "")
        for r in treated.itertuples(index=False)
    ]
    treated["treated_repo"] = treated["event_repo"]
    treated["treated_path"] = treated["event_path"]
    treated["control_repo"] = ""

    control = control.copy()
    control["group"] = "control"
    control["treated"] = 0

    keep_cols = sorted(set(treated.columns) | set(control.columns))
    for df in [treated, control]:
        for col in keep_cols:
            if col not in df.columns:
                df[col] = np.nan
    sample = pd.concat([treated[keep_cols], control[keep_cols]], ignore_index=True)
    sample = sample[clean_error_mask(sample["fetch_error"])].copy()

    sample["post"] = (sample["event_window"].astype(str) == "post").astype(int)
    sample["treated_x_post"] = sample["treated"] * sample["post"]
    sample["number_norm"] = sample["number"].map(norm_number)
    sample["analysis_event_id"] = sample["treated_event_id"].astype(str)
    sample["repo_for_scale"] = np.where(sample["treated"] == 1, sample["treated_repo"], sample["control_repo"])

    # Attach matched scale covariates. Treated covariates are constant by TE;
    # control covariates are matched by TE-control repo.
    matched_first = matched.sort_values(["treated_event_id", "match_rank"]).copy()
    treated_cov = (
        matched_first.drop_duplicates("treated_event_id")
        .set_index("treated_event_id")
        [[
            "treated_stars",
            "treated_pull_requests_total",
            "treated_issues_total",
            "treated_governance_maturity_score",
        ]]
        .rename(columns={
            "treated_stars": "repo_stars",
            "treated_pull_requests_total": "repo_pull_requests_total",
            "treated_issues_total": "repo_issues_total",
            "treated_governance_maturity_score": "repo_governance_maturity_score",
        })
    )
    control_cov = (
        matched_first.set_index(["treated_event_id", "control_repo"])
        [[
            "control_stars",
            "control_pull_requests_total",
            "control_issues_total",
            "control_governance_maturity_score",
        ]]
        .rename(columns={
            "control_stars": "repo_stars",
            "control_pull_requests_total": "repo_pull_requests_total",
            "control_issues_total": "repo_issues_total",
            "control_governance_maturity_score": "repo_governance_maturity_score",
        })
    )

    for col in ["repo_stars", "repo_pull_requests_total", "repo_issues_total", "repo_governance_maturity_score"]:
        sample[col] = np.nan
    treated_idx = sample["treated"] == 1
    for idx, row in sample[treated_idx].iterrows():
        te = row["analysis_event_id"]
        if te in treated_cov.index:
            for col in treated_cov.columns:
                sample.at[idx, col] = treated_cov.at[te, col]
    control_idx = sample["treated"] == 0
    for idx, row in sample[control_idx].iterrows():
        key = (row["analysis_event_id"], row["control_repo"])
        if key in control_cov.index:
            vals = control_cov.loc[key]
            for col in control_cov.columns:
                sample.at[idx, col] = vals[col]

    for col in [
        "body_has_ai_mention",
        "body_has_verification_language",
        "closed_without_merge",
        "is_bot_author",
    ]:
        sample[col] = sample[col].map(bool01)
    for col in [
        "body_length",
        "maintainer_comment_count",
        "clarification_comment_count",
        "first_maintainer_response_hours",
        "time_to_close_hours",
        "repo_stars",
        "repo_pull_requests_total",
        "repo_issues_total",
        "repo_governance_maturity_score",
    ]:
        sample[col] = pd.to_numeric(sample[col], errors="coerce")

    sample["is_pr"] = (sample["item_type"].astype(str) == "pr").astype(int)
    sample["log_body_length"] = np.log1p(sample["body_length"].fillna(0).clip(lower=0))
    sample["log_repo_stars"] = np.log1p(sample["repo_stars"].fillna(0).clip(lower=0))
    sample["log_repo_pr_total"] = np.log1p(sample["repo_pull_requests_total"].fillna(0).clip(lower=0))
    sample["log_repo_issue_total"] = np.log1p(sample["repo_issues_total"].fillna(0).clip(lower=0))
    sample["repo_governance_maturity_score"] = sample["repo_governance_maturity_score"].fillna(sample["repo_governance_maturity_score"].median())
    sample["is_bot_author"] = sample["is_bot_author"].fillna(0)

    sample = merge_comment_mechanism_counts(sample, event_map)
    return sample


def merge_comment_mechanism_counts(sample: pd.DataFrame, event_map: Dict[Tuple[str, str, str], str]) -> pd.DataFrame:
    comments = read_csv(COMMENT_CLASS)
    if comments.empty:
        for var in MECHANISM_COUNT_VARS:
            sample[MECHANISM_COUNT_COLS[var]] = 0
        return sample

    comments = comments.copy()
    comments["number_norm"] = comments["number"].map(norm_number)
    treated_mask = comments["group"].astype(str) == "treated"
    # Classification rows do not carry adoption_date. Use the treated audit map
    # by repo/path, which is unique in the 27-event mechanism sample.
    repo_path_to_te = {}
    for (repo, path, _date), te in event_map.items():
        repo_path_to_te[(repo, path)] = te
    comments.loc[treated_mask, "analysis_event_id"] = [
        repo_path_to_te.get((r.event_repo, r.event_path), "")
        for r in comments.loc[treated_mask].itertuples(index=False)
    ]
    comments.loc[~treated_mask, "analysis_event_id"] = comments.loc[~treated_mask, "treated_event_id"].astype(str)

    rows = []
    for row in comments.itertuples(index=False):
        labels = str(getattr(row, "mechanism_labels", "") or "")
        label_set = {x for x in labels.split(";") if x}
        base = {
            "group": getattr(row, "group"),
            "analysis_event_id": getattr(row, "analysis_event_id"),
            "event_window": getattr(row, "event_window"),
            "event_repo": getattr(row, "event_repo"),
            "item_type": getattr(row, "item_type"),
            "number_norm": getattr(row, "number_norm"),
        }
        for var in MECHANISM_COUNT_VARS:
            base[MECHANISM_COUNT_COLS[var]] = 1 if var in label_set else 0
        rows.append(base)
    item_counts = pd.DataFrame(rows)
    if item_counts.empty:
        for var in MECHANISM_COUNT_VARS:
            sample[MECHANISM_COUNT_COLS[var]] = 0
        return sample

    key_cols = ["group", "analysis_event_id", "event_window", "event_repo", "item_type", "number_norm"]
    item_counts = item_counts.groupby(key_cols, as_index=False).sum(numeric_only=True)
    sample = sample.merge(item_counts, how="left", on=key_cols)
    for var in MECHANISM_COUNT_VARS:
        col = MECHANISM_COUNT_COLS[var]
        sample[col] = sample[col].fillna(0)
    return sample


def add_dummies(frame: pd.DataFrame, col: str, prefix: str) -> pd.DataFrame:
    dummies = pd.get_dummies(frame[col].fillna("missing").astype(str), prefix=prefix, drop_first=True, dtype=float)
    return pd.concat([frame, dummies], axis=1)


def design_matrix(df: pd.DataFrame, spec: str) -> Tuple[np.ndarray, List[str]]:
    base_vars = ["treated", "post", "treated_x_post"]
    control_vars: List[str] = []
    work = df.copy()

    if spec == "event_fe_controls":
        continuous_controls = [
            "log_body_length",
            "log_repo_stars",
            "log_repo_pr_total",
            "log_repo_issue_total",
            "repo_governance_maturity_score",
        ]
        for col in continuous_controls:
            x = pd.to_numeric(work[col], errors="coerce").fillna(0)
            sd = x.std()
            work[col] = 0.0 if not np.isfinite(sd) or sd == 0 else (x - x.mean()) / sd
        control_vars = [
            "is_pr",
            "is_bot_author",
            *continuous_controls,
        ]
        work = add_dummies(work, "author_association", "assoc")
        control_vars.extend([c for c in work.columns if c.startswith("assoc_")])

    work = add_dummies(work, "analysis_event_id", "eventfe")
    fe_vars = [c for c in work.columns if c.startswith("eventfe_")]
    names = ["intercept"] + base_vars + control_vars + fe_vars
    X = np.column_stack([np.ones(len(work))] + [pd.to_numeric(work[c], errors="coerce").fillna(0).to_numpy(dtype=float) for c in names[1:]])
    if not np.isfinite(X).all():
        raise ValueError("non-finite values in regression design matrix")

    protected = {"intercept", "treated", "post", "treated_x_post"}
    keep_cols = []
    kept_names = []
    for idx, name in enumerate(names):
        col = X[:, idx]
        if name in protected or float(np.nanstd(col)) > 0:
            keep_cols.append(idx)
            kept_names.append(name)
    return X[:, keep_cols], kept_names


def matvec(X: np.ndarray, beta: np.ndarray) -> np.ndarray:
    return np.einsum("ij,j->i", X, beta, optimize=True)


def crossprod(X: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    if weights is None:
        return np.einsum("ni,nj->ij", X, X, optimize=True)
    return np.einsum("ni,n,nj->ij", X, weights, X, optimize=True)


def quad_sandwich(left: np.ndarray, middle: np.ndarray) -> np.ndarray:
    return np.einsum("ij,jk,kl->il", left, middle, left, optimize=True)


def stable_pinv(A: np.ndarray, rcond: float = 1e-12) -> np.ndarray:
    u, s, vt = linalg.svd(A, full_matrices=False, check_finite=False, lapack_driver="gesdd")
    if len(s) == 0:
        return A.T
    cutoff = rcond * max(A.shape) * float(s[0])
    s_inv = np.where(s > cutoff, 1.0 / s, 0.0)
    return np.einsum("ji,j,kj->ik", vt, s_inv, u, optimize=True)


def cluster_vcov_ols(X: np.ndarray, resid: np.ndarray, clusters: np.ndarray) -> np.ndarray:
    xtx_inv = stable_pinv(crossprod(X))
    meat = np.zeros((X.shape[1], X.shape[1]))
    unique_clusters = np.unique(clusters)
    for g in unique_clusters:
        idx = clusters == g
        Xg = X[idx]
        ug = resid[idx]
        sg = np.einsum("ni,n->i", Xg, ug, optimize=True)
        meat += np.outer(sg, sg)
    n, k = X.shape
    g = len(unique_clusters)
    factor = (g / (g - 1)) * ((n - 1) / max(n - k, 1)) if g > 1 else 1.0
    return factor * quad_sandwich(xtx_inv, meat)


def fit_ols(df: pd.DataFrame, outcome: str, spec: str, transform_log: bool = False) -> ModelResult:
    d = df.copy()
    y_raw = pd.to_numeric(d[outcome], errors="coerce")
    if transform_log:
        y_raw = np.log1p(y_raw.where(y_raw >= 0))
    d["_y"] = y_raw
    d = d[np.isfinite(d["_y"])].copy()
    X, names = design_matrix(d, spec)
    # design_matrix only drops rows for X finiteness; X is currently all rows.
    y = d["_y"].to_numpy(dtype=float)
    clusters = d["analysis_event_id"].astype(str).to_numpy()
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - matvec(X, beta)
    vcov = cluster_vcov_ols(X, resid, clusters)
    idx = names.index("treated_x_post")
    se = math.sqrt(max(vcov[idx, idx], 0))
    tval = beta[idx] / se if se else np.nan
    dfree = max(len(np.unique(clusters)) - 1, 1)
    p = float(2 * stats.t.sf(abs(tval), dfree)) if np.isfinite(tval) else np.nan
    means = cell_means(d, "_y")
    return ModelResult(
        outcome=outcome,
        family="log_ols" if transform_log else "ols_lpm",
        spec=spec,
        coef=float(beta[idx]),
        se=float(se),
        t=float(tval),
        p=p,
        n=len(d),
        clusters=len(np.unique(clusters)),
        y_mean=float(np.nanmean(y)),
        **means,
    )


def fit_ppml(df: pd.DataFrame, outcome: str, spec: str) -> ModelResult:
    d = df.copy()
    d["_y"] = pd.to_numeric(d[outcome], errors="coerce")
    d = d[np.isfinite(d["_y"]) & (d["_y"] >= 0)].copy()
    X, names = design_matrix(d, spec)
    y = d["_y"].to_numpy(dtype=float)
    clusters = d["analysis_event_id"].astype(str).to_numpy()
    beta = np.zeros(X.shape[1])
    beta[0] = math.log(max(y.mean(), 1e-6))
    converged = False
    for _ in range(100):
        eta = np.clip(matvec(X, beta), -20, 20)
        mu = np.exp(eta)
        z = eta + (y - mu) / np.maximum(mu, 1e-8)
        sw = np.sqrt(np.maximum(mu, 1e-8))
        beta_new = np.linalg.lstsq(X * sw[:, None], z * sw, rcond=None)[0]
        if np.max(np.abs(beta_new - beta)) < 1e-8:
            beta = beta_new
            converged = True
            break
        beta = beta_new

    eta = np.clip(matvec(X, beta), -20, 20)
    mu = np.exp(eta)
    bread = stable_pinv(crossprod(X, mu))
    meat = np.zeros((X.shape[1], X.shape[1]))
    unique_clusters = np.unique(clusters)
    score = X * (y - mu)[:, None]
    for g in unique_clusters:
        sg = score[clusters == g].sum(axis=0)[:, None]
        meat += sg @ sg.T
    n, k = X.shape
    g = len(unique_clusters)
    factor = (g / (g - 1)) * ((n - 1) / max(n - k, 1)) if g > 1 else 1.0
    vcov = factor * quad_sandwich(bread, meat)
    idx = names.index("treated_x_post")
    se = math.sqrt(max(vcov[idx, idx], 0))
    tval = beta[idx] / se if se else np.nan
    dfree = max(len(unique_clusters) - 1, 1)
    p = float(2 * stats.t.sf(abs(tval), dfree)) if np.isfinite(tval) else np.nan
    means = cell_means(d, "_y")
    return ModelResult(
        outcome=outcome,
        family="ppml",
        spec=spec,
        coef=float(beta[idx]),
        se=float(se),
        t=float(tval),
        p=p,
        n=len(d),
        clusters=len(unique_clusters),
        y_mean=float(np.nanmean(y)),
        convergence="converged" if converged else "max_iter",
        pct_effect=float(math.exp(beta[idx]) - 1),
        **means,
    )


def cell_means(d: pd.DataFrame, y_col: str) -> Dict[str, float]:
    def m(treated: int, post: int) -> float:
        vals = d.loc[(d["treated"] == treated) & (d["post"] == post), y_col]
        return float(vals.mean()) if len(vals) else np.nan

    return {
        "treated_pre_mean": m(1, 0),
        "treated_post_mean": m(1, 1),
        "control_pre_mean": m(0, 0),
        "control_post_mean": m(0, 1),
    }


def stars(p: float) -> str:
    if not np.isfinite(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def result_to_row(r: ModelResult) -> Dict[str, Any]:
    return {
        "outcome": r.outcome,
        "family": r.family,
        "spec": r.spec,
        "treated_x_post_coef": f"{r.coef:.6f}",
        "cluster_se": f"{r.se:.6f}",
        "t_stat": f"{r.t:.4f}",
        "p_value": f"{r.p:.6f}",
        "stars": stars(r.p),
        "n": r.n,
        "clusters": r.clusters,
        "y_mean": f"{r.y_mean:.6f}",
        "treated_pre_mean": f"{r.treated_pre_mean:.6f}",
        "treated_post_mean": f"{r.treated_post_mean:.6f}",
        "control_pre_mean": f"{r.control_pre_mean:.6f}",
        "control_post_mean": f"{r.control_post_mean:.6f}",
        "ppml_pct_effect": "" if r.pct_effect is None else f"{r.pct_effect:.6f}",
        "convergence": r.convergence,
    }


def format_coef(r: pd.Series, digits: int = 4) -> str:
    coef = float(r["treated_x_post_coef"])
    se = float(r["cluster_se"])
    star = str(r["stars"]) if not pd.isna(r["stars"]) else ""
    return f"{coef:.{digits}f}{star} ({se:.{digits}f})"


def write_report(results: pd.DataFrame) -> None:
    lines = [
        "# Formal Regression Tables",
        "",
        "Coefficient of interest is `Treated x Post`. Standard errors are clustered by treated-event stratum (`TE001`-`TE027`).",
        "",
        "Specs:",
        "",
        "- `event_fe`: treated indicator, post indicator, `Treated x Post`, and treated-event fixed effects.",
        "- `event_fe_controls`: `event_fe` plus item type, bot-author flag, body length, author association dummies, log stars, log PR total, log issue total, and governance maturity.",
        "",
        "Significance: `* p<0.10`, `** p<0.05`, `*** p<0.01`.",
        "",
    ]
    labels = {
        "body_has_ai_mention": "AI mention in body",
        "body_has_verification_language": "Verification language in body",
        "closed_without_merge": "PR closed without merge",
        "maintainer_comment_count": "Maintainer comments",
        "clarification_comment_count": "Clarification comments",
        "mech_information_clarification_count": "Information-clarification comments",
        "mech_action_request_count": "Action-request comments",
        "mech_quality_correctness_count": "Quality/correctness comments",
        "mech_verification_testing_count": "Verification/testing comments",
        "mech_integration_project_fit_count": "Integration/project-fit comments",
        "mech_responsibility_provenance_ai_count": "AI provenance/responsibility comments",
        "mech_security_risk_count": "Security-risk comments",
        "mech_rejection_moderation_count": "Rejection/moderation comments",
        "mech_coordination_management_count": "Coordination/management comments",
        "mech_social_acknowledgement_count": "Social-acknowledgement comments",
        "mech_other_nonmechanism_count": "Other non-mechanism comments",
        "mech_not_maintainer_substantive_count": "Non-substantive maintainer comments",
        "first_maintainer_response_hours": "Log first response hours",
        "time_to_close_hours": "Log close hours",
    }
    families = [
        ("ols_lpm", "## Table R1. LPM / OLS Item-Level Effects"),
        ("ppml", "## Table R2. PPML Count Effects"),
        ("log_ols", "## Table R3. Log-Duration OLS Effects"),
    ]
    for family, title in families:
        sub = results[results["family"] == family].copy()
        if sub.empty:
            continue
        lines.extend([title, "", "| Outcome | Event FE | Event FE + controls | N (controlled) | Clusters |", "|---|---:|---:|---:|---:|"])
        for outcome in sub["outcome"].drop_duplicates():
            r0 = sub[(sub["outcome"] == outcome) & (sub["spec"] == "event_fe")]
            r1 = sub[(sub["outcome"] == outcome) & (sub["spec"] == "event_fe_controls")]
            c0 = format_coef(r0.iloc[0]) if len(r0) else ""
            c1 = format_coef(r1.iloc[0]) if len(r1) else ""
            n = int(r1.iloc[0]["n"]) if len(r1) else (int(r0.iloc[0]["n"]) if len(r0) else 0)
            g = int(r1.iloc[0]["clusters"]) if len(r1) else (int(r0.iloc[0]["clusters"]) if len(r0) else 0)
            lines.append(f"| {labels.get(outcome, outcome)} | {c0} | {c1} | {n} | {g} |")
        lines.append("")
    lines.extend([
        "## Reading The Coefficients",
        "",
        "- LPM coefficients are percentage-point changes in the treated post window relative to matched controls.",
        "- OLS count coefficients are additional comments per PR/issue item.",
        "- PPML coefficients are log-point effects; see `ppml_pct_effect` in the CSV for `exp(beta)-1`.",
        "- Log-duration coefficients are approximate percent changes in time-related outcomes.",
        "",
        "## Interpretation Guardrails",
        "",
        "- These are early-window mechanism regressions, not long-run causal event-study estimates.",
        "- The maintained claim should remain burden restructuring: governance increases disclosure and verification signals and reallocates maintainer attention across clarification, action requests, quality/correctness, verification, integration fit, coordination, and boundary work rather than simply reducing total maintainer comments.",
        "- Validated text-mechanism variables are based on a 579-row stratified sample, `gpt-4o` auxiliary coding at temperature 0, conservative adjudication, and a revised full-pool rule dictionary.",
        "- `social_acknowledgement`, `other_nonmechanism`, and `not_maintainer_substantive` are reported for measurement transparency but should not be used as main burden-mechanism outcomes.",
        "- The current main sample still has residual PR-activity imbalance; controlled specs and strict-v2 matching should be used as robustness evidence.",
        "",
        f"Sample output: `{SAMPLE_OUT.relative_to(ROOT)}`",
        f"Regression CSV: `{RESULTS_OUT.relative_to(ROOT)}`",
    ])
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    sample = prepare_audit_sample()
    sample.to_csv(SAMPLE_OUT, index=False)

    results: List[ModelResult] = []
    binary_outcomes = [
        "body_has_ai_mention",
        "body_has_verification_language",
    ]
    pr_binary_outcomes = ["closed_without_merge"]
    count_outcomes = [
        "maintainer_comment_count",
        "clarification_comment_count",
        *(MECHANISM_COUNT_COLS[var] for var in MECHANISM_COUNT_VARS),
    ]
    duration_specs = [
        ("first_maintainer_response_hours", sample["first_maintainer_response_hours"] >= 0),
        ("time_to_close_hours", sample["time_to_close_hours"] >= 0),
    ]

    for spec in ["event_fe", "event_fe_controls"]:
        for outcome in binary_outcomes:
            results.append(fit_ols(sample.dropna(subset=[outcome]), outcome, spec))
        pr_sample = sample[sample["item_type"].astype(str) == "pr"].copy()
        for outcome in pr_binary_outcomes:
            results.append(fit_ols(pr_sample.dropna(subset=[outcome]), outcome, spec))
        timeline_sample = sample.dropna(subset=["maintainer_comment_count"]).copy()
        for outcome in count_outcomes:
            results.append(fit_ols(timeline_sample.dropna(subset=[outcome]), outcome, spec))
            results.append(fit_ppml(timeline_sample.dropna(subset=[outcome]), outcome, spec))
        for outcome, mask in duration_specs:
            dur_sample = sample[mask.fillna(False)].dropna(subset=[outcome]).copy()
            results.append(fit_ols(dur_sample, outcome, spec, transform_log=True))

    rows = [result_to_row(r) for r in results]
    with RESULTS_OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    results_df = pd.DataFrame(rows)
    write_report(results_df)
    print(f"wrote {SAMPLE_OUT}")
    print(f"wrote {RESULTS_OUT}")
    print(f"wrote {REPORT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
