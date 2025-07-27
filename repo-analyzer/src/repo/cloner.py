from pathlib import Path
import git 
from src.utils.logger import setup_logger

logger = setup_logger("cloner")

def clone_repo(repo_url: str, dest_dir: Path, branch: str = None)->Path:
    repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git',"")
    repo_path = dest_dir / repo_name
    
    if repo_path.exists():
        logger.info("Repository already exists at %s", repo_path)
        return repo_name
    logger.info("Cloning %s into %s ...", repo_url, repo_path)
    try:
        if branch:
            git.Repo.clone_from(repo_url, repo_path, branch=branch)
        else:
            git.Repo.clone_from(repo_url, repo_path) 
        logger.info("Clone complete.")
        return repo_name
    except Exception as e:
        print(f"Failed to clone: %s", e)
        return None