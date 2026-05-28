# Supplementary Materials

This repository contains supplementary materials for:

**AI Contribution Governance Rules in Open Source Software: Effects on Information Visibility and Maintainer Comment Patterns**

This folder contains a compact support package.

The package is intentionally limited to the materials needed to inspect the final empirical claims:

- `01_rule_identification_RQ1/`: confirmed AI contribution governance rule events and adoption-date trace.
- `02_matched_event_window_sample/`: matched treated-control event design, compact matching-balance table, and the item-level analysis sample.
- `03_results_tables/`: regression, robustness, mechanism, and heterogeneity tables.
- `04_codebooks/`: coding definitions.
- `05_reproduction_code/`: scripts for reproducing the main RQ2 and RQ3 event-window estimates from the submitted analysis sample.
- `00_manifest/`: file manifest and field dictionary.

Raw GitHub issue/PR bodies, raw maintainer comments, large intermediate timeline files, post-hoc exploratory tables, and process logs are not included. The item-level analysis sample keeps only the identifiers, treatment/window variables, controls, coded body-level variables, and aggregated maintainer-comment mechanism variables needed to reproduce the reported models.

Key counts:

- Confirmed AI contribution governance rule events: 203.
- Treated rule events with reliable event windows: 123.
- Matched control event rows: 615.
- RQ2 issue/PR item rows used in the reported models: 44,304.
- RQ3 issue/PR rows with maintainer-comment timeline coverage: 29,539.
- Maintainer comments classified before item-level aggregation: 37,492.

To reproduce the main reported estimates, run:

```bash
python3 05_reproduction_code/run_main_regressions.py
```

The script writes reproduced result tables to `05_reproduction_code/reproduced_outputs/`.

## License

The materials are released under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

## Citation

Please cite the archived release DOI once it is available.
