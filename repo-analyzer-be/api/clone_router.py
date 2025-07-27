from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from src.repo.cloner import clone_repo
from src.configs.config import REPO_DIR

router = APIRouter()

class CloneRequest(BaseModel):
    repo_url: str
    branch: str | None = None

@router.post("/clone")
def clone_repository(req: CloneRequest):
    repo_name = clone_repo(req.repo_url, REPO_DIR, req.branch)
    
    if repo_name is None:
        raise HTTPException(status_code=500, detail="Failed to clone repository.")
    
    return {
        "status": "success",
        "repo_name": str(repo_name)
    }
