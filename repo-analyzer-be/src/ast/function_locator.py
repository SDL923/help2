import os
import pickle
import ast
from pathlib import Path
from typing import Set
import pickle

from src.configs.config import AST_DIR, REPO_DIR


def get_function_and_context(func_name: str) -> dict:
    """
    주어진 함수 이름에 대해:
    - 본인 코드 (target)
    - 본문 내부에서 호출한 함수들의 정의 (internal)
    - 본인을 호출하는 상위 함수들의 정의 (caller)
    를 구분하여 반환합니다.

    반환 구조:
    {
        "target": {
            "function": str,
            "file": str,
            "code": str,
            "called_count": int,
            "called_by_count": int
        },
        "internal": [ {function, file, code}, ... ],
        "caller":   [ {function, file, code}, ... ]
    }
    """
    seen_internal = set()
    internal_funcs = []
    caller_funcs = []

    # 1. 본인 코드 추출 (target)
    target_defs = extract_function_code(func_name)
    if not target_defs:
        return {"target": None, "internal": [], "caller": []}

    target_def = target_defs[0]  # 복수일 수 있으나, 가장 먼저 찾은 정의만 사용
    target_code = target_def["code"]

    # 2. 내부 호출 함수들 추출
    called_func_names = get_called_functions(target_code)
    for name in called_func_names:
        if name == func_name or name in seen_internal:
            continue
        sub_defs = extract_function_code(name)
        if sub_defs:  # 정의가 실제로 존재할 때만 추가
            for sub_item in sub_defs:
                internal_funcs.append(sub_item)
            seen_internal.add(name)
    called_count = len(seen_internal)

    # 3. 상위 호출자 함수들 추출
    calling_locs = get_calling_functions(func_name)
    called_by_count = len(calling_locs)

    for loc in calling_locs:
        source_path = find_file_by_relative_path(REPO_DIR, loc["file"])
        if not source_path:
            continue
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            start = loc["lineno"] - 1
            end = loc["end_lineno"] if loc["end_lineno"] else start + 1
            code = "".join(lines[start:end])

            caller_funcs.append({
                "function": f"(caller of {func_name})",
                "file": loc["file"],
                "code": code.strip()
            })
        except Exception:
            continue

    return {
        "target": {
            **target_def,
            "called_count": called_count,
            "called_by_count": called_by_count
        },
        "internal": internal_funcs,
        "caller": caller_funcs
    }


def get_calling_functions(func_name: str) -> list[dict]:
    """
    레포 전체 AST를 통해 특정 함수가 호출되는 상위 함수들을 찾아 반환합니다.

    Args:
        func_name (str): 추적할 대상 함수 이름

    Returns:
        List[dict]: {"file": str, "lineno": int, "end_lineno": int}
    """
    results = []

    for ast_file in AST_DIR.glob("*.ast"):
        try:
            with open(ast_file, "rb") as f:
                tree = pickle.load(f)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for inner in ast.walk(node):
                        if isinstance(inner, ast.Call):
                            # 함수 호출 이름이 func_name과 일치하면
                            if (
                                isinstance(inner.func, ast.Name) and inner.func.id == func_name
                            ) or (
                                isinstance(inner.func, ast.Attribute) and inner.func.attr == func_name
                            ):
                                location = {
                                    "file": _restore_source_path(ast_file),
                                    "lineno": node.lineno,
                                    "end_lineno": getattr(node, "end_lineno", None)
                                }
                                #print(f"[✓] 호출 위치 발견: {location}")
                                results.append(location)
                                break

        except Exception as e:
            print(f"[!] Error analyzing {ast_file.name}: {e}")
    return results


def get_called_functions(func_code: str) -> Set[str]:
    """
    함수 코드 내부에서 호출된 함수 이름들을 반환합니다.

    Args:
        func_code (str): 함수 정의 코드 문자열

    Returns:
        Set[str]: 호출된 함수 이름들의 집합
    """
    called = set()
    try:
        tree = ast.parse(func_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # 예: module.func() → func
                    called.add(node.func.attr)
    except Exception as e:
        print(f"[!] Failed to parse function code: {e}")
    return called


def extract_function_code(func_name: str) -> list[dict]:
    """
    저장된 AST와 REPO 디렉토리를 기반으로 함수 정의 전체 코드를 추출합니다.

    Args:
        func_name (str): 추출할 함수 이름

    Returns:
        List[dict]: [
            {
                "function": str,
                "file": str,
                "code": str
            }
        ]
    """
    locations = find_function_location(func_name)
    results = []

    for loc in locations:
        source_path = find_file_by_relative_path(REPO_DIR, loc["file"])
        if not source_path:
            print(f"[!] 파일 경로를 찾을 수 없습니다: {loc['file']}")
            continue

        try:
            with open(source_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            start = loc["lineno"] - 1
            end = loc["end_lineno"] if loc["end_lineno"] else start + 1
            code_block = "".join(lines[start:end])

            results.append({
                "function": func_name,
                "file": str(source_path.relative_to(REPO_DIR)).replace("\\", "/"),
                "code": code_block.strip()
            })

        except Exception as e:
            print(f"[!] Error extracting {func_name} from {source_path}: {e}")

    return results


def find_file_by_relative_path(base_dir: Path, relative_path: str) -> Path | None:
    """
    base_dir 아래를 순회하면서 relative_path와 끝이 일치하는 파일을 찾는다.
    예: relative_path = "src/utils/helpers.py"

    Returns:
        전체 경로 Path 또는 None
    """
    relative_path = relative_path.replace("\\", "/")  # 윈도우 호환

    for root, _, files in os.walk(base_dir):
        for file in files:
            full_path = Path(root) / file
            try:
                rel = full_path.relative_to(base_dir).as_posix()
                if rel.endswith(relative_path):
                    return full_path
            except Exception:
                continue
    return None


def find_function_location(func_name: str) -> list[dict]:
    """
    저장된 .ast 파일들에서 주어진 함수 이름을 정의한 위치를 반환합니다.

    Args:
        func_name (str): 찾을 함수 이름

    Returns:
        List[dict]: [{"file": str, "lineno": int, "end_lineno": int}]
    """
    results = []

    for ast_file in AST_DIR.glob("*.ast"):
        try:
            with open(ast_file, "rb") as f:
                tree = pickle.load(f)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    result = {
                        "file": _restore_source_path(ast_file),
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, "end_lineno", None)
                    }
                    results.append(result)

        except Exception as e:
            print(f"[!] Error reading AST file {ast_file.name}: {e}")

    return results


def _restore_source_path(ast_file: Path) -> str:
    """
    src__utils__helpers.py.ast → src/utils/helpers.py
    """
    name = ast_file.stem  # remove .ast
    return name.replace("@@@", "/")


# if __name__ == "__main__":
#     name = input("찾을 함수 이름 입력: ").strip()
#     locations = find_function_location(name)

#     if not locations:
#         print("[X] 해당 함수 정의를 찾을 수 없습니다.")
#     else:
#         for loc in locations:
#             print(f"[✓] {loc['file']}:{loc['lineno']}")