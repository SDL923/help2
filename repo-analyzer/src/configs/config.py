from pathlib import Path

BASE_DATA_DIR = Path(__file__).parent.parent.parent / "data"
REPO_DIR = BASE_DATA_DIR / "cloned_repo"
SUMMARY_DIR = BASE_DATA_DIR / "summaries"
AST_DIR = BASE_DATA_DIR / "asts"
COMMIT_ANALYSIS_DIR = BASE_DATA_DIR / "commit_analysis"

REPO_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
AST_DIR.mkdir(parents=True, exist_ok=True)
COMMIT_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
