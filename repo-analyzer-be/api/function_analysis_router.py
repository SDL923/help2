from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

from src.ast.function_locator import get_function_and_context
from src.ast.function_explainer import analyze_function
from src.commit.commit_analyzer import get_commit_summary
from src.risk_analysis.risk_score_calculator import generate_risk_report
from src.configs.config import REPO_DIR

router = APIRouter()

# ====== /function/explain ======
class ExplainRequest(BaseModel):
    function_name: str

@router.post("/function/explain")
def explain_function(req: ExplainRequest):
    context = get_function_and_context(req.function_name)
    if not context or context.get("target") is None:
        raise HTTPException(status_code=404, detail="Function not found.")

    result = analyze_function(context)
    if result is None:
        raise HTTPException(status_code=500, detail="LLM 분석 실패")

    return {
        "status": "success",
        "function": req.function_name,
        "analysis": result
    }


# ====== /function/commits ======
class CommitRequest(BaseModel):
    repo_name: str
    file_path: str
    function_name: str

@router.post("/function/commits")
def get_function_commit_summary(req: CommitRequest):
    repo_path = REPO_DIR / req.repo_name
    full_file_path = repo_path / req.file_path

    if not full_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        summary = get_commit_summary(full_file_path, req.function_name, repo_path)
        return {
            "status": "success",
            "summary": summary
        }
    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))


# ====== /function/risk ======
class RiskRequest(BaseModel):
    repo_name: str
    file_path: str
    function_name: str

@router.post("/function/risk")
def assess_function_risk(req: RiskRequest):
    repo_path = REPO_DIR / req.repo_name
    full_file_path = repo_path / req.file_path

    if not full_file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        report = generate_risk_report(full_file_path, req.function_name, repo_path)
        return {
            "status": "success",
            "function": req.function_name,
            "risk_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")
