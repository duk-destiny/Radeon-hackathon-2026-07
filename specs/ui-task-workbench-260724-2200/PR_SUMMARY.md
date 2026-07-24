# PR Summary

**PR title (fixed official identity):** `Track 2, PLASMA, ProjectPack Office Agent`

**Suggested commit:** `feat(web): add task workbench with human confirmation (UI-2)`

## What

Implements stage UI-2 of `docs/UNIFIED_WORKBENCH_UI_PLAN.zh-CN.md` — the task
workbench and human-confirmation surface of the unified project workbench.
Frontend-only feature work plus contract-guard scripts/tests; no backend
behavior change. Other stages are intentionally untouched.

### Frontend (web/)

- `src/api/paths.ts` — route constants for the full backend task family:
  list/detail, transition, history, confirmation-queue, confirmation,
  audit-log, extract, submit-candidates, import-preview, import-confirm.
- `src/api/dto.ts` — `// maps:` annotated DTOs (`TaskUpdate`,
  `TaskStatusTransition`, `TaskChangeRecord`, `CandidateTask`,
  `ConfirmationRecord`, `ConfirmationAction`, `TaskImportDiff`,
  `TaskImportResult`, `OperationAuditRecord`, `TaskExtractionRequest`,
  `TaskExtractionResult`) plus a display-only mirror of the lifecycle
  (`PhaseFTaskStatus`, `TASK_ALLOWED_TRANSITIONS`).
- `src/api/client.ts` — 13 typed methods covering CRUD, lifecycle
  transition, history, confirmation queue, audit log, extraction and
  multipart CSV/XLSX import preview/confirm.
- `src/api/errors.ts` — unwraps FastAPI `detail`-nested structured error
  bodies so task rejections (`TASK_INVALID_TRANSITION`,
  `CONFIRMATION_ALREADY_PROCESSED`, `IMPORT_FILE_UNSUPPORTED`, …) map to the
  same `ApiError` as flat bodies.
- `src/components/TaskWorkbench.tsx` — new dashboard section with four tabs:
  - **Tasks**: server-side status filter + client-side owner/priority/due
    refinement; detail pane with acceptance criteria, evidence, confirmation
    info, full change history, and a transition form that only offers legal
    targets (server stays the single authority).
  - **Confirmation queue**: accept / accept-with-changes / ignore extracted
    candidates, recording operator, basis and notes; double-processing is
    surfaced as a recoverable error.
  - **Import**: preview-then-confirm CSV/XLSX flow with duplicate/conflict
    flags; nothing is persisted before explicit confirmation.
  - **Audit log**: who/what/when for imports, confirmations and transitions.
- `src/pages/DashboardPage.tsx`, `src/styles.css` — mount + styling.

### Guards (scripts/, tests/)

- `scripts/validate_task_ui.py` — pins the frontend lifecycle mirror to
  `app/schemas/task_sql.py::ALLOWED_TRANSITIONS` and
  `app/schemas/models.py::PhaseFTaskStatus`; fails on any drift.
- `tests/test_task_ui_contract.py` — same guarantee inside the governance
  unittest suite.
- `web/src/api/tasks.test.ts` (23 cases) — URL/verb/payload for every client
  method, multipart handling, nested + flat error mapping, lifecycle-mirror
  invariants; registered in the `npm test` script.
- `specs/ui-task-workbench-260724-2200/` — S2 PRODUCT/TECH/TEST_REPORT.

## Why

Meeting-minute candidates and imported task lists must never enter the plan
without an accountable human decision. This stage gives operators a reviewable
queue, an explicit import diff, server-arbitrated status changes and a full
audit trail — while the UI renders only backend-reported state.

## Dependencies

No new Python or npm dependencies; `pyproject.toml` and `web/package.json`
dependency sections are unchanged (verified by the dependency-declaration
governance test in the full suite).

## Verification

| Check | Result |
| --- | --- |
| `npm --prefix web test` | 71 passed (40 client incl. 23 new, 28 contract, 3 guard) |
| `npm --prefix web run build` | PASS (tsc + vite) |
| `python scripts/validate_ui_contract.py` | PASS |
| `python scripts/validate_task_ui.py` | PASS (7 statuses / 15 transitions in sync) |
| `make check-governance` equivalent (`git diff --check`, `validate_specs --strict`) | PASS |
| `make test-governance` equivalent (`unittest discover`) | 11 OK |
| `python -m pytest -q` (full suite) | 525 passed, 6 skipped |
| Acceptance smoke (TestClient replay of the exact UI call sequence) | 14/14 |

## Known gap / follow-up

Backend task routes validate project scope but do not yet enforce per-role
authorization; the UI makes no false claim of it. Server-side role
enforcement is a backend follow-up outside this stage.

## Rollback

Revert this branch. UI-0/UI-1a/UI-1b remain fully functional without the task
workbench.
