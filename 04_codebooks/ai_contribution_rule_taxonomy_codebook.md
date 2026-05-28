# Contribution Rule Taxonomy Codebook

## Unit of Analysis

The unit of analysis is a repository-level rule event: a contributor-facing rule written into a repository file or contribution entry point that governs whether or how contributors may use AI tools when submitting issues, pull requests, patches, documentation, translations, or security reports.

## Inclusion Criteria

A text segment is included when it satisfies all conditions below:

1. It is located in a repository file or contribution-facing entry point.
2. It addresses contributors, issue reporters, pull-request authors, patch submitters, security reporters, or equivalent external participants.
3. It contains a normative requirement, restriction, disclosure request, responsibility statement, verification requirement, or process field related to AI-assisted contributions.

## Exclusion Criteria

A text segment is excluded when it only describes:

1. The repository's AI functionality, model integration, API use, or product behavior.
2. Internal maintainer notes that do not govern external contributions.
3. Generic automation, bots, CI, or scripts without a connection to AI-assisted contribution generation or submission.
4. Unfilled template artifacts that do not impose or invite an AI-related contribution requirement.

## Carrier

`carrier` records where the rule appears.

| Carrier | Definition |
|---|---|
| `pr_template` | Pull request templates, including checklist fields and structured PR forms. |
| `issue_template` | Issue templates, bug-report forms, feature-request forms, or equivalent issue-entry fields. |
| `contributing_guide` | CONTRIBUTING files or contribution guides under repository documentation. |
| `security_policy` | Security reporting files or vulnerability disclosure policies. |
| `standalone_ai_policy` | Dedicated AI contribution policy files. |
| `developer_or_maintainer_doc` | Developer documentation that explicitly governs external contributions. |
| `readme_contributor_section` | Contributor-facing rules embedded in README files. |
| `agent_instruction_boundary` | Agent instruction files included only when they explicitly govern external contributors. |
| `other_contributor_facing_doc` | Other contributor-facing documentation that imposes AI-related contribution requirements. |

## Scope

`scope` records the contribution process to which the rule applies.

| Scope | Definition |
|---|---|
| `pull_request_or_patch` | Code pull requests, patches, commits, or merge requests. |
| `issue_or_bug_report` | Issues, bug reports, reproduction reports, or feature requests. |
| `security_report` | Vulnerability reports, security issue reports, or PoC reports. |
| `documentation_or_translation` | Documentation, translation, README, or copy-editing contributions. |
| `general_contribution` | General contributor obligations not limited to one entry point. |
| `internal_agent_workflow` | Internal agent workflows; treated as boundary cases unless externally binding. |

## Rule Components

Rules may contain multiple components.

| Component | Definition |
|---|---|
| `disclosure` | Requires contributors to disclose whether or how AI was used. |
| `model_tool_usage_detail` | Requires details about the model, tool, usage context, or AI-assisted task. |
| `human_responsibility` | Requires human understanding, review, ownership, explanation, or responsibility for AI-assisted output. |
| `verification_testing` | Requires testing, validation, reproduction, review, or other evidence that the contribution works. |
| `authorship_or_provenance` | Addresses AI provenance, authorship, attribution, generated-by/assisted-by notices, or commit trailers. |
| `restriction_or_ban` | Restricts, rejects, or prohibits AI-generated or insufficiently reviewed AI-assisted contributions. |
| `process_requirement` | Embeds AI-related requirements into templates, checklists, mandatory fields, or contribution steps. |
| `security_reporting` | Governs AI-generated or automated security reports and vulnerability reports. |
| `maintainer_review_discretion` | States that maintainers may reject, close, return, or apply heightened review to noncompliant AI-assisted contributions. |
| `agent_instruction_boundary` | Marks agent instruction files or internal agent rules as boundary cases. |

## Orientation

`orientation` summarizes the rule's governance logic.

| Orientation | Definition |
|---|---|
| `conditional_acceptance_accountability` | Allows AI assistance under disclosure, human responsibility, verification, or provenance/accountability conditions. |
| `exclusionary_gatekeeping` | Restricts, rejects, or prohibits low-trust, unverified, fully automated, or otherwise prohibited AI-assisted contributions. |
| `process_template_absorption` | Converts AI-related information requirements into templates, checklists, or structured contribution fields. |
| `security_risk_control` | Applies AI-related rules to vulnerability reports, automated security reports, or other security-sensitive submissions. |
| `agent_workflow_boundary` | Covers agent instruction or workflow files that are included only when they explicitly govern contributor-facing AI-assisted work. |

## Coding Output

Each confirmed rule event records repository, file path, carrier, scope, components, orientation, source URL, concise rule summary, and evidence fields.
