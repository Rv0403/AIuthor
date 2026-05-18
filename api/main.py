"""FastAPI — single POST /execute endpoint."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import get_settings
from evals.run_evals import run_all_evals, write_markdown_report
from graph.workflow import run_workflow

app = FastAPI(title="AIuthor", description="Agentic book generation orchestration engine")


class ExecuteRequest(BaseModel):
    user_input: str = Field(..., min_length=3)
    run_id: str | None = None
    task_type: str | None = None
    insert_after: int | None = None
    source_run_id: str | None = None


class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    task_type: str | None = None
    output_paths: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    eval_report: dict[str, Any] | None = None
    clarification_message: str | None = None
    pending_insert: dict[str, Any] | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    try:
        result = run_workflow(
            req.user_input,
            run_id=req.run_id,
            task_type=req.task_type,
            insert_after=req.insert_after,
            source_run_id=req.source_run_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    run_id = result.get("run_id", "")
    eval_report = None
    if run_id and result.get("status") == "completed" and get_settings().auto_run_evals:
        try:
            eval_report = run_all_evals(run_id)
            write_markdown_report(run_id, eval_report)
        except Exception:
            pass

    return ExecuteResponse(
        run_id=run_id,
        status=result.get("status", "unknown"),
        task_type=result.get("task_type"),
        output_paths=result.get("output_paths", {}),
        errors=result.get("errors", []),
        eval_report=eval_report,
        clarification_message=result.get("clarification_message"),
        pending_insert=result.get("pending_insert"),
    )
