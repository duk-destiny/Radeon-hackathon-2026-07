"""Stage I automation task endpoints — CRUD, pause/resume, dry-run."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.services.automation_tasks import AutomationTaskService

router = APIRouter(prefix="/api", tags=["automation-tasks"])


def _get_service(request: Request) -> AutomationTaskService:
    db_path = Path(request.app.state.db_path)
    db_dir = db_path.parent if not db_path.parent.name == "" else db_path
    db_dir.mkdir(parents=True, exist_ok=True)
    return AutomationTaskService(db_path=str(db_dir / "automation_tasks.db"))


# ---------------------------------------------------------------------------
# List for a project
# ---------------------------------------------------------------------------

@router.get("/projects/{project_id}/automation-tasks")
async def list_automation_tasks(project_id: str, request: Request):
    """List all automation tasks for a project."""
    service = _get_service(request)
    tasks = service.list_by_project(project_id)
    return {
        "ok": True,
        "project_id": project_id,
        "tasks": [t.__dict__ for t in tasks],
        "count": len(tasks),
    }


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("/automation-tasks")
async def create_automation_task(payload: dict, request: Request):
    """Create a new automation task."""
    project_id = payload.get("project_id", "")
    name = payload.get("name", "")
    task_type = payload.get("type", "on_demand")
    config = payload.get("config")

    if not project_id:
        raise HTTPException(status_code=400, detail="project_id is required")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    service = _get_service(request)
    task = service.create(project_id, name, task_type, config)
    return {"ok": True, "task": task.__dict__}


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------

@router.post("/automation-tasks/{task_id}/pause")
async def pause_automation_task(task_id: str, request: Request):
    """Pause an active automation task."""
    service = _get_service(request)
    try:
        task = service.pause(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Automation task {task_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"ok": True, "task": task.__dict__}


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

@router.post("/automation-tasks/{task_id}/resume")
async def resume_automation_task(task_id: str, request: Request):
    """Resume a paused automation task."""
    service = _get_service(request)
    try:
        task = service.resume(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Automation task {task_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"ok": True, "task": task.__dict__}


# ---------------------------------------------------------------------------
# Dry Run
# ---------------------------------------------------------------------------

@router.post("/automation-tasks/{task_id}/dry-run")
async def dry_run_automation_task(task_id: str, request: Request):
    """Simulate an automation task without side effects."""
    service = _get_service(request)
    try:
        result = service.dry_run(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Automation task {task_id} not found")
    return {"ok": True, "dry_run": result}


# ---------------------------------------------------------------------------
# Delete (cancel)
# ---------------------------------------------------------------------------

@router.post("/automation-tasks/{task_id}/delete")
async def delete_automation_task(task_id: str, request: Request):
    """Cancel (soft-delete) an automation task."""
    service = _get_service(request)
    try:
        service.delete(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Automation task {task_id} not found")
    return {"ok": True, "message": f"Task {task_id} cancelled."}


# ---------------------------------------------------------------------------
# Audit log for a task
# ---------------------------------------------------------------------------

@router.get("/automation-tasks/{task_id}/audit")
async def audit_automation_task(task_id: str, request: Request):
    """Get the audit log for a specific automation task."""
    service = _get_service(request)
    try:
        log = service.audit_log(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Automation task {task_id} not found")
    return {"ok": True, "task_id": task_id, "audit_log": log, "count": len(log)}
