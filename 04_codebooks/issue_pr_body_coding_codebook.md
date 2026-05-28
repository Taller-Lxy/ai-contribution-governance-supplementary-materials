# Issue and Pull Request Body Coding Codebook

## Unit of Analysis

The unit of analysis is one GitHub issue or pull request item.

The coding target is the item body. The title is used only as local context.

## Outcome 1: AI-Use Disclosure

Variable: `body_ai_contribution_disclosure_binary`

Definition: whether the issue/PR body explicitly records AI-use information related to the submitted issue or pull request.

Code as `1` when the body:

1. States that a named AI tool, code assistant, language model, or AI agent was used for this contribution.
2. States that AI was not used for this contribution.
3. Provides a completed answer to an AI-use field in an issue/PR template.
4. Explains how AI assisted generation, modification, testing, review, reporting, or documentation for this specific item.

Code as `0` when:

1. The repository or requested feature is about AI, but the contributor does not disclose AI use in preparing the issue/PR.
2. The body contains an unanswered AI-disclosure template field.
3. AI appears only in file names, labels, dependencies, examples, or project content.
4. The text is empty, unclear, automated boilerplate, or unrelated to contributor AI use.

## Outcome 2: Verification Evidence

Variable: `body_verification_evidence_binary`

Definition: whether the issue/PR body contains contribution-specific testing, validation, reproduction, manual review, environment, log, or CI/check evidence.

Code as `1` when the body includes:

1. Test commands, test results, CI/check results, added tests, or local validation.
2. Reproduction steps, environment information, logs, actual/expected behavior, or minimal reproductions for issues.
3. Manual review, human review, double-checking, or validation of AI-assisted output.
4. Screenshots, benchmarks, traces, or other concrete verification evidence.

Code as `0` when:

1. A template heading such as "Steps to reproduce" or "How was this tested?" is present but unanswered.
2. The contributor states that testing was not performed or remains to be done.
3. Verification wording is unrelated to the current issue/PR.
4. The body is empty or unclear.

## GitHub State Outcome

Variable: `closed_without_merge`

Definition: for pull requests only, the PR was closed and not merged. This variable is constructed from GitHub state and merge metadata, not from text coding.

## Output Fields

The coded table records item identifiers, event-window variables, treatment indicators, controls, GitHub state variables, and the two coded body-level variables. Raw issue and pull request body text is excluded.
