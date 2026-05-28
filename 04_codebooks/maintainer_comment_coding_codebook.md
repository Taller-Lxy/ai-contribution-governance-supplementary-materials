# Maintainer Comment Coding Codebook

## Unit of Analysis

The coding unit is one maintainer comment from a GitHub issue or pull request discussion.

Each comment receives one primary label and, when clearly supported, secondary labels. Item-level mechanism-family variables are then constructed by aggregating comment labels within each issue/PR item.

## Fine-Grained Comment Labels

| Label | Definition |
|---|---|
| `information_clarification` | Maintainer asks for missing information, rationale, reproduction steps, expected/actual behavior, use cases, or explanation of intent. |
| `action_request` | Maintainer asks the contributor to change code, add documentation, update a branch, resolve conflicts, split a PR, fill a template, or perform another concrete action. |
| `quality_correctness` | Maintainer comments on bugs, edge cases, correctness, style, linting, refactoring, performance, API behavior, implementation quality, or code smells. |
| `verification_testing` | Maintainer asks for tests, CI evidence, reproduction, validation, benchmarks, coverage, or proof that behavior works. |
| `integration_project_fit` | Maintainer evaluates architecture, project conventions, roadmap fit, scope, compatibility, maintainability, dependencies, branch fit, or repository context. |
| `responsibility_provenance_ai` | Maintainer explicitly discusses AI-use provenance, generated-output trust, contributor responsibility, disclosure, or authorship of AI-assisted output. |
| `security_risk` | Maintainer discusses vulnerabilities, authentication, tokens, secrets, injection, permissions, CVE/CWE issues, exploitability, or security-sensitive review. |
| `rejection_moderation` | Maintainer closes, rejects, marks invalid/out of scope, declines to merge, identifies spam/low value, or enforces contribution boundaries. |
| `coordination_management` | Maintainer routes work, assigns participants, pings experts, manages milestones, links duplicates, schedules releases, or coordinates discussion. |
| `social_acknowledgement` | Maintainer gives thanks, approval, encouragement, LGTM, or brief acknowledgement without substantive review content. |
| `other_nonmechanism` | Substantive maintainer comment that does not fit the above labels. |
| `not_maintainer_substantive` | Empty, command-only, emoji-only, quoted-only, bot/noise, or uninterpretable text. |

## Coding Boundaries

1. Code the maintainer's own comment function, not quoted contributor text.
2. Do not infer AI use from repository status or surrounding metadata.
3. Use `responsibility_provenance_ai` only when AI/provenance/responsibility wording is explicit.
4. If a comment mainly requests a concrete change, use `action_request`; add a technical secondary label only when the technical concern is explicit.
5. If a comment mainly requests tests, reproduction, or validation evidence, use `verification_testing`.
6. If a comment mainly evaluates project architecture, compatibility, maintainability, roadmap, or scope, use `integration_project_fit`.

## Mechanism Families

Fine-grained labels are aggregated into three item-level mechanism families.

| Mechanism family | Fine-grained labels included | Interpretation |
|---|---|---|
| `post_hoc_query_burden` | `information_clarification`, `action_request`, `responsibility_provenance_ai` | Follow-up work that asks contributors to provide missing information, perform concrete follow-up actions, or clarify AI provenance/responsibility. |
| `quality_assurance_work` | `quality_correctness`, `verification_testing`, `security_risk` | Maintainer work focused on correctness, validation, implementation quality, and security risk. |
| `coordination_boundary_work` | `integration_project_fit`, `coordination_management`, `rejection_moderation` | Maintainer work focused on project fit, workflow coordination, and acceptance/rejection boundaries. |

For each issue/PR item, the coded table records both count outcomes and binary any-occurrence outcomes for each mechanism family. Raw maintainer-comment text is excluded.
