# Pull Request

## Summary

Describe the change in 2–5 sentences.

Example:
This PR implements the question creation form for MVP v2. It adds validation, connects the feature to the existing flow, and updates the required documentation.

---

## Linked issue

Closes #

Related issues:

* #

---

## Assignment 5 workflow evidence

* [ ] This PR is linked to an issue.
* [ ] The branch name follows `<issue-number>-short-description`.
* [ ] The PR was created from an issue-linked branch.
* [ ] The PR has a reviewer who is different from the assignee.
* [ ] The PR has at least one meaningful review comment.
* [ ] The PR has approval before merge.
* [ ] The PR will be merged using a merge commit.

Branch name:

```text
<issue-number>-short-description
```

---

## Type of work

Select all that apply:

* [ ] User Story
* [ ] Other PBI
* [ ] Course Task
* [ ] Bug Report
* [ ] Documentation
* [ ] Testing
* [ ] Refactoring
* [ ] Deployment / Release
* [ ] Changelog update

---

## MVP / Sprint metadata

MVP version:

* [ ] MVP v1
* [ ] MVP v2
* [ ] MVP v3
* [ ] Not assigned to an MVP version

Sprint milestone:

```text
Sprint:
```

Assignee:

```text
@
```

Reviewer:

```text
@
```

---

## What changed

List the concrete changes made in this PR.

*
*
*

---

## Acceptance criteria verification

For every acceptance criterion from the linked issue, describe how it was verified.

### AC1

Issue criterion:

```text
```

Verification evidence:

```text
```

Status:

* [ ] Verified
* [ ] Not verified
* [ ] Not applicable

### AC2

Issue criterion:

```text
```

Verification evidence:

```text
```

Status:

* [ ] Verified
* [ ] Not verified
* [ ] Not applicable

### AC3

Issue criterion:

```text
```

Verification evidence:

```text
```

Status:

* [ ] Verified
* [ ] Not verified
* [ ] Not applicable

Additional acceptance criteria, if any:

```text
```

---

## Testing evidence

### Manual testing

For each scenario tested, describe: what was done, the expected result, and the actual result.
Include edge cases and error/boundary conditions where relevant.

```text
Scenario 1:
  Steps:
  Expected:
  Actual:

Scenario 2:
  Steps:
  Expected:
  Actual:
```

### Automated tests

List the test files or test suites that cover this change.
State which critical modules are affected and confirm their line coverage meets ≥ 30%.
Write `Not applicable` only if no source code was changed.

```text
Test files / suites:

Critical modules affected:

Line coverage on critical modules: % (attach CI report or paste summary)
```

### Commands executed

Paste the exact commands used to run tests locally or reference the CI job.

```bash
```

### Test result

* [ ] Passed
* [ ] Failed
* [ ] Not applicable

---

## Screenshots / demo evidence

Add screenshots, screen recordings, logs, or links when relevant.

```text
Screenshot:
Demo:
Log:
```

---

## Documentation impact

* [ ] README updated
* [ ] docs updated
* [ ] reports/week4 updated
* [ ] No documentation change needed

Files changed:

```text
```

---

## Changelog

Select exactly one option:

* [ ] Added or updated a user-visible entry in `CHANGELOG.md`.
* [ ] Not applicable because the change is not user-visible.

---

## Definition of Done checklist

* [ ] The linked issue is clear and traceable.
* [ ] The implementation satisfies the acceptance criteria.
* [ ] The change was tested (unit and/or integration tests pass).
* [ ] Automated unit tests pass and critical modules maintain ≥ 30% line coverage.
* [ ] The PR was reviewed by another team member.
* [ ] Required documentation was updated (README, docs/).
* [ ] `CHANGELOG.md` was updated for user-visible changes, or marked not applicable.
* [ ] No secrets, credentials, or real/non-sanitized employee data were committed.
* [ ] If a Docker container is affected, it builds and runs successfully.
* [ ] For changes affecting the recognition pipeline, manual verification on the test page is performed and recorded.
* [ ] Relevant QRTs pass in CI (if applicable).
* [ ] CI pipeline passes, including linting, type/format check, tests, coverage, and QA checks.
* [ ] The branch can be merged into the default branch.
* [ ] The linked issue can be moved to Done after merge.

---

## Risks and limitations

Describe known limitations, remaining risks, or follow-up work.

```text
```

---

## Reviewer notes

Reviewer should check:

**Workflow and traceability**
* [ ] The linked issue exists and is traceable.
* [ ] The branch name follows `<issue-number>-short-description`.
* [ ] Exactly one changelog option is selected.
* [ ] The change matches the MVP/Sprint scope.
* [ ] The PR will be merged using a merge commit.

**Evidence quality**
* [ ] Each acceptance criterion has specific, observable verification evidence (not just "it works").
* [ ] Manual testing describes concrete scenarios with expected and actual results, including edge cases.
* [ ] Automated test output or CI coverage report is included and confirms ≥ 30% line coverage on critical modules.
* [ ] Screenshots, logs, or a demo recording are present where the change has a visible or behavioral effect.
* [ ] The testing evidence is sufficient to confirm the AC is met — not merely that tests were run.

**Code and CI**
* [ ] The CI pipeline passes (lint, type/format check, tests, coverage, QA checks).
* [ ] No secrets, credentials, or sensitive data are present in the diff.
* [ ] The PR can be safely merged into the default branch.

Meaningful review comment:

```text
```
