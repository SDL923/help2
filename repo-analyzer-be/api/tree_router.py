from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from pathlib import Path
from src.configs.config import REPO_DIR, AST_DIR
from src.ast.tree_maker import build_tree, extract_function_names_from_ast
import os

router = APIRouter()

@router.get("/repo/tree")
def get_repo_tree(repo_name: str = Query(..., description="클론된 레포 디렉토리 이름")):
    repo_path = REPO_DIR / repo_name
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository not found.")

    tree = build_tree(repo_path)
    return tree

@router.get("/file/functions")
def list_functions(
    repo_name: str = Query(...),
    file_path: str = Query(...)
):
    ast_filename = file_path.replace("/", "@@@").replace("\\", "@@@") + ".ast"
    ast_file_path = AST_DIR / ast_filename

    if not ast_file_path.exists():
        raise HTTPException(status_code=404, detail="AST not found for this file.")

    try:
        functions = extract_function_names_from_ast(ast_file_path)
        return {
            "file": file_path,
            "functions": functions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AST: {e}")
    
