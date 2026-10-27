# InvestIQ — Efficient CI and PR Development

**Status:** Adopted workflow policy for v0.2 onward.

## Why multiple Actions runs happened

The `pull_request` `synchronize` event fires on **every branch update**. The existing concurrency cancellation rule cancels superseded in-progress runs, but each push can still enqueue a new workflow and incur setup cost. GitHub Actions cannot reliably infer that a particular commit is the developer's last commit.

## Working agreement

1. **Build an outcome locally before opening the PR.** Group cohesive changes into a single push whenever practical; perform local lint, relevant tests, packaging and documentation checks first.
2. **Use a draft PR for work in progress.** The `CI` workflow has a draft gate on its Python job. Intermediate pushes to draft PRs may still show a **skipped workflow run** in GitHub's UI, but **will not start the Python runner or execute the expensive checks**.
3. **Mark ready only at the reviewable latest head.** The `ready_for_review` event activates full lint, pytest, wheel/sdist, and installed CLI smoke.
4. **After ready, every new head requires fresh CI.** Keep `synchronize` enabled and cancel superseded runs. Never disable it or reuse a passing status from an older commit: it is a security and correctness requirement.
5. **After merge, run CI on `main`.** This verifies the resulting integration commit; it is intentionally separate from a pull-request check.
6. **Manual CI is available** through `workflow_dispatch` if an operator needs it. Do not use manual runs to bypass required latest-head PR checks.

### Trade-off

GitHub still records a skipped workflow for draft updates. This is not a zero-event workflow and not a promise that the Actions UI will show one row per PR. It avoids installing dependencies and running tests for every intermediate draft push while preserving the last-head quality gate. The simplest way to further reduce events is to push less frequently and open the PR after local validation.

### Engineering acceptance

- New draft PR and further draft pushes: `CI / python` job skipped; **not accepted for merge** while draft.
- Transition to ready: full CI runs for the current head.
- Update a ready PR: full CI reruns for the changed head; older run gets cancelled by concurrency.
- Push or merge on `main`: full CI runs.
- A PR is mergeable only after required latest-head checks, completed code review and resolved material findings.

The workflow does **not** use path-only skips for required PR checks, nor does it eliminate necessary verification just to save runner minutes.
