from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from src.ast.ast_generator import process_repo_ast
from src.configs.config import REPO_DIR

router = APIRouter()

class ASTRequest(BaseModel):
    repo_name: str

@router.post("/generate-ast")
def generate_ast(req: ASTRequest):
    repo_path = REPO_DIR / req.repo_name

    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository not found.")

    process_repo_ast(repo_path)
    return {
        "status": "success",
        "message": f"ASTs generated for repository '{req.repo_name}'"
    }
