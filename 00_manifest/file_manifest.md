# File Manifest

## 00_manifest

| File | Purpose |
|---|---|
| `field_dictionary.xlsx` | Describes the major variables in the submitted support datasets and result tables. |
| `file_manifest.md` | Lists the files included in this compact support package. |

## 01_rule_identification_RQ1

| File | Purpose |
|---|---|
| `ai_governance_rule_taxonomy_final_main.csv` | Contains the 203 confirmed AI contribution governance rule events, including repository, file path, carrier, scope, components, orientation, evidence fields, and source links. |
| `final_main_governance_adoption_trace.csv` | Records the adoption-date tracing results used to identify rule events with reliable timing. |

## 02_matched_event_window_sample

| File | Purpose |
|---|---|
| `final_main_matched_control_events.csv` | Links each treated rule event to five matched control repositories and their pseudo-event dates. |
| `paper_table_matching_balance.csv` | Compact matching-balance table. |
| `item_level_analysis_sample_text_excluded.csv` | Item-level analysis sample with 44,304 issue/PR rows. It includes treatment/window variables, controls, coded body-level variables, and aggregated maintainer-comment mechanism variables; raw issue/PR body text and raw maintainer-comment text are excluded. |

## 03_results_tables

| File | Purpose |
|---|---|
| `rq2_body_formal_regression_results.csv` | Model estimates for AI-use disclosure and verification-evidence outcomes. |
| `rq2_body_robustness_results.csv` | Robustness estimates for body-level coded outcomes. |
| `rq3_mechanism_family_results.csv` | Mechanism-family estimates for maintainer-comment outcomes. |
| `paper_table_mechanism_family.csv` | Compact mechanism-family table. |
| `paper_table_mechanism_family_robustness.csv` | Robustness table for mechanism-family results. |
| `paper_table_governance_type_heterogeneity.csv` | Estimates by governance-rule type, supporting the mechanism interpretation. |

## 04_codebooks

| File | Purpose |
|---|---|
| `ai_contribution_rule_taxonomy_codebook.md` | Definitions for coding rule carriers, scopes, components, and orientations. |
| `issue_pr_body_coding_codebook.md` | Definitions for coding AI-use disclosure and verification evidence in issue/PR bodies. |
| `maintainer_comment_coding_codebook.md` | Definitions for maintainer-comment labels and item-level aggregation. |

## 05_reproduction_code

| File | Purpose |
|---|---|
| `build_formal_regression_tables.py` | Estimation utilities for OLS/LPM and PPML models with treated-event clustered standard errors. |
| `run_main_regressions.py` | Reproduces the main RQ2 body-level estimates, RQ2 robustness estimates, and RQ3 mechanism-family estimates from the submitted item-level analysis sample. |
| `reproduced_outputs/rq2_body_formal_regression_results.csv` | Output produced by `run_main_regressions.py`; matches the submitted RQ2 main result table. |
| `reproduced_outputs/rq2_body_robustness_results.csv` | Output produced by `run_main_regressions.py`; matches the submitted RQ2 robustness table. |
| `reproduced_outputs/rq3_mechanism_family_results.csv` | Output produced by `run_main_regressions.py`; matches the submitted RQ3 mechanism-family result table. |
