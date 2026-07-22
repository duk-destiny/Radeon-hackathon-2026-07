"""Stage I integration endpoints — email, webhook, SCM."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.integrations.email import EmailConnector
from app.integrations.webhook import WebhookRegistry, WebhookDispatcher
from app.integrations.scm import SCMConnector

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _db(request: Request, name: str) -> str:
    """Get a stage-i-scoped db path, creating parent dirs."""
    db_path = Path(request.app.state.db_path)
    db_dir = db_path.parent if not db_path.parent.name == "" else db_path
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / name)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

@router.post("/email/send")
async def email_send(payload: dict, request: Request):
    """Send a task report / risk alert / project summary via email."""
    db = _db(request, "integration_email.db")
    connector = EmailConnector(db_path=db)

    preview = connector.preview_diff(payload)
    result = connector.execute(preview, confirmation_id="confirmed_by_api")

    if result.status.name == "FAILED":
        raise HTTPException(status_code=500, detail=result.summary)

    return {"ok": True, "summary": result.summary, "details": result.details}


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

@router.post("/webhook/register")
async def webhook_register(payload: dict, request: Request):
    """Register an external webhook URL."""
    db = _db(request, "integration_webhooks.db")
    url = payload.get("url", "")
    events = payload.get("events", [])
    secret = payload.get("secret", "")

    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    if not events:
        raise HTTPException(status_code=400, detail="events list is required")

    registry = WebhookRegistry(db_path=db)
    reg = registry.register(url, events, secret)

    # dispatch a test event to confirm delivery
    dispatcher = WebhookDispatcher(registry)
    result = dispatcher.dispatch("project_member_change", {
        "event": "webhook_registered",
        "webhook_id": reg.id,
        "url": reg.url,
    })

    return {"ok": True, "webhook": reg.__dict__, "dispatch_result": result}


# ---------------------------------------------------------------------------
# SCM
# ---------------------------------------------------------------------------

@router.post("/scm/commit")
async def scm_commit(payload: dict, request: Request):
    """Push a report or task list to Git/SCM (confirmed write-back)."""
    db = _db(request, "integration_scm.db")
    connector = SCMConnector(db_path=db)

    # Read current state
    state = connector.read(target=payload.get("target", "github_issues"))

    # Preview
    from app.integrations.base import ConfirmationRequired
    try:
        connector.preview_diff(payload)
    except ConfirmationRequired as cr:
        confirmation_id = cr.details.get("confirmation_id", "")
        if not confirmation_id:
            raise HTTPException(status_code=400, detail="Could not generate confirmation")

        # Execute with confirmation
        result = connector.execute(payload, confirmation_id=confirmation_id)
        return {"ok": True, "summary": result.summary, "details": result.details, "state": state}

    raise HTTPException(status_code=400, detail="SCM commit requires a diff preview")
