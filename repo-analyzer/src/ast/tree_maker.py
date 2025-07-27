import ast
import pickle
from pathlib import Path

def build_tree(dir_path: Path, root_path: Path = None) -> dict:
    if root_path is None:
        root_path = dir_path  # 초기 진입점에서 root_path를 설정

    tree = {
        "name": dir_path.name,
        "type": "directory",
        "children": []
    }

    for entry in sorted(dir_path.iterdir()):
        if entry.name.startswith(".") or entry.name in {"__pycache__"}:
            continue

        if entry.is_dir():
            subtree = build_tree(entry, root_path)
            if subtree:
                tree["children"].append(subtree)

        elif entry.suffix == ".py":
            tree["children"].append({
                "name": entry.name,
                "type": "file",
                "path": str(entry.relative_to(root_path))  # 전체 상대 경로
            })

    return tree

# def build_tree(dir_path: Path) -> dict:
#     if not dir_path.is_dir():
#         return {}

#     tree = {
#         "name": dir_path.name,
#         "type": "folder",
#         "children": []
#     }

#     for entry in sorted(dir_path.iterdir()):
#         if entry.name.startswith(".") or entry.name in {"__pycache__"}:
#             continue
#         if entry.is_dir():
#             subtree = build_tree(entry)
#             if subtree:
#                 tree["children"].append(subtree)
#         elif entry.suffix == ".py":
#             tree["children"].append({
#                 "name": entry.name,
#                 "type": "file",
#                 "path": str(entry.relative_to(dir_path.parent))
#             })

#     return tree


def extract_function_names_from_ast(ast_path: Path) -> list[dict]:
    with open(ast_path, "rb") as f:
        tree = pickle.load(f)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return functions