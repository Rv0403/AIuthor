"""FastAPI — single POST /execute endpoint."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from evals.run_evals import run_all_evals, write_markdown_report
from graph.workflow import run_workflow

app = FastAPI(title="AIuthor", description="Agentic book generation orchestration engine")


class ExecuteRequest(BaseModel):
    user_input: str = Field(..., min_length=3)
    run_id: str | None = None


class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    task_type: str | None = None
    output_paths: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    eval_report: dict[str, Any] | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest):
    try:
        result = run_workflow(req.user_input, run_id=req.run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    run_id = result.get("run_id", "")
    eval_report = None
    if run_id and result.get("status") == "completed":
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
    )
