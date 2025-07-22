import ast
import os
import pickle
from pathlib import Path

from src.configs.config import REPO_DIR, AST_DIR
from src.configs.filter_config import EXCLUDED_DIRS, EXCLUDED_FILES

def should_process(filepath: Path) -> bool:
    if not filepath.suffix == ".py":
        return False
    if filepath.name in EXCLUDED_FILES:
        return False
    if any(part in EXCLUDED_DIRS for part in filepath.parts):
        return False
    if filepath.stat().st_size < 30:
        return False
    return True

def save_ast(filepath: Path, base_dir: Path):
    try:
        code = filepath.read_text(encoding="utf-8")
        tree = ast.parse(code)

        # 파일 경로를 안전한 이름으로 변경
        rel_path = filepath.relative_to(base_dir)
        ast_filename = str(rel_path).replace("/", "@@@").replace("\\", "@@@") + ".ast"
        ast_path = AST_DIR / ast_filename

        with open(ast_path, "wb") as f:
            pickle.dump(tree, f)
        print(f"[+] Saved AST: {ast_path.name}")
    except Exception as e:
        print(f"[!] Failed to parse {filepath}: {e}")

def process_repo_ast(repo_path: Path):
    print(f"[*] Generating ASTs from repo: {repo_path}")
    for root, _, files in os.walk(repo_path):
        for file in files:
            path = Path(root) / file
            if should_process(path):
                save_ast(path, repo_path)

