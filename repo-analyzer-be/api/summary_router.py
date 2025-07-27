from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from src.summarizer.file_summarizer import summarize_files, load_summary
from src.configs.config import REPO_DIR, SUMMARY_DIR

router = APIRouter()

class SummaryRequest(BaseModel):
    repo_name: str

@router.post("/summarize")
def summarize_repository(req: SummaryRequest):
    repo_path = REPO_DIR / req.repo_name
    print(repo_path)

    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository not found.")

    summarize_files(repo_path)
    return {
        "status": "success",
        "message": f"Summary files generated for repository '{req.repo_name}'"
    }


@router.get("/file/summary")
def get_file_summary(repo_name: str, file_path: str):
    try:
        summary = load_summary(Path(file_path))
        return summary
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Summary file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read summary: {e}")
