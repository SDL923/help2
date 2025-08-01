import subprocess
import json
from pathlib import Path
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional

import requests
from openai import OpenAI
from src.utils.secrets_loader import load_llm_config
from src.configs.config import COMMIT_ANALYSIS_DIR


# === LLM 설정 ===
provider, LLM_API_KEY, LLM_API_URL, LLM_MODEL = load_llm_config()
USE_OPENAI = provider.lower() == "openai"
if USE_OPENAI:
    client = OpenAI(api_key=LLM_API_KEY)

# === 커밋 유형 분류 프롬프트 ===
COMMIT_TYPE_PROMPT = """
당신은 Git 커밋 이력을 분석하여 변경 목적을 분류하는 전문가입니다.
아래는 하나의 커밋의 diff 내용과 메시지입니다.
이 커밋의 목적을 다음 중 하나로 분류하세요:

- Bug&Error
- Feature
- Refactor
- Documentation
- Testing
- Code Style
- Chore
- Other

반드시 위 목록 중 하나만 출력하세요. 추가 설명은 하지 마세요.

### Commit Message:
{message}

### Diff:
{diff}
"""

def classify_commit_type(diff: str, message: str) -> str:
    prompt = COMMIT_TYPE_PROMPT.format(diff=diff[:3000], message=message[:1000])
    system_prompt = "당신은 Git 커밋 이력을 분석하여 커밋의 목적을 분류하는 전문가입니다."

    try:
        if USE_OPENAI:
            response = client.chat.completions.create(
                model=LLM_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            result = response.choices[0].message.content.strip()

        else:
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": LLM_MODEL or "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            response = requests.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"].strip()

        result = result.strip("`").strip()
        valid_labels = {
            "Bug&Error", "Feature", "Refactor", "Documentation",
            "Testing", "Code Style", "Chore", "Other"
        }
        return result if result in valid_labels else "Other"

    except Exception as e:
        print(f"[!] classify_commit_type error: {e}")
        return "Other"

def run_git_log_L(function_name: str, file_path: Path, repo_root: Path) -> str:
    rel_path = file_path.relative_to(repo_root)
    cmd = [
        "git", "log", "-L", f":{function_name}:{rel_path}", "--patch"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
        return result.stdout
    except Exception as e:
        print(f"[!] git log -L failed: {e}")
        return ""

def parse_git_log(log_output: str) -> List[Dict]:
    commits = []
    current = {}
    lines = log_output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("commit "):
            if current:
                commits.append(current)
                current = {}
            current["hash"] = line.split()[1]
        elif line.startswith("Author: "):
            author = line[len("Author: "):].strip()
            if "<" in author:
                name, email = author.split("<")
                current["author"] = name.strip()
                current["email"] = email.strip("> ")
        elif line.startswith("Date: "):
            date_str = line[len("Date: "):].strip()
            current["date"] = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y %z").isoformat()
        elif line.strip() == "":
            i += 1
            break  # skip empty line after header
        i += 1

    # diff
    diff_lines = []
    while i < len(lines):
        if lines[i].startswith("commit "):
            continue  # skip, already handled above
        diff_lines.append(lines[i])
        i += 1
    current["diff"] = "\n".join(diff_lines)
    commits.append(current)
    return [c for c in commits if "hash" in c]

def analyze_function_commits(file_path: Path, function_name: str, repo_root: Path) -> Optional[Dict]:
    log_output = run_git_log_L(function_name, file_path, repo_root)
    if not log_output:
        return None

    commits_raw = parse_git_log(log_output)
    if not commits_raw:
        return None
    commits_raw = commits_raw[:3]
    type_counter = Counter()
    author_counter = Counter()
    for c in commits_raw:
        commit_type = classify_commit_type(c.get("diff", ""), c.get("message", ""))
        c["commit_type"] = commit_type
        type_counter[commit_type] += 1
        author_counter[c.get("author", "")] += 1

    summary = {
        "total_commits": len(commits_raw),
        "top_authors": dict(author_counter),
        "first_commit": commits_raw[-1]["date"],
        "last_commit": commits_raw[0]["date"],
        "type_distribution": dict(type_counter)
    }

    return {
        "function": function_name,
        "file": str(file_path),
        "commit_history": commits_raw,
        "summary": summary
    }

def save_commit_analysis(data: Dict, file_path: Path, function_name: str):
    rel_path = file_path.relative_to(Path.cwd()).as_posix().replace("/", "@@@")
    save_path = COMMIT_ANALYSIS_DIR / f"{rel_path}@@@{function_name}.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)






````````````````````````````````

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


````````````````````````````````````

from src.configs.config import REPO_DIR
from src.repo.cloner import clone_repo
from src.summarizer.file_summarizer import summarize_files
from src.ast.ast_generator import process_repo_ast 
from src.ast.function_locator import extract_function_code, get_called_functions, get_function_and_context
from src.ast.function_explainer import analyze_function
from src.commit.commit_analyzer import analyze_function_commits, save_commit_analysis
from pathlib import Path

def main():
    # repo_url = input("Enter Git repo URL: ").strip()
    # repo_branch = input("Enter branch name: ").strip()
    # repo_path = clone_repo(repo_url, REPO_DIR, repo_branch)

    # if not repo_path:
    #     print("\n[X] Repository clone failed.")
    #     return

    # print(f"\n[✓] Repository ready at: {repo_path}")

    # summarize_files(repo_path)
    
    # process_repo_ast(repo_path)
    
    # name = input("함수 이름을 입력하세요: ").strip()

    # context_blocks = get_function_and_context(name)
    
    # print(context_blocks)

    # result = analyze_function(context_blocks)
    
    # print(result)
    
    repo_root = REPO_DIR / "whereami" 
    file_path = repo_root / "whereami" / "predict.py"
    function_name = "crossval"

    print(f"[*] 분석 시작: {file_path} / 함수: {function_name}")
    result = analyze_function_commits(file_path=file_path, function_name=function_name, repo_root=repo_root)

    if result:
        save_commit_analysis(result, file_path=file_path, function_name=function_name)
        print("[+] 분석 완료 및 저장됨.")
    else:
        print("[!] 분석 실패 또는 결과 없음.")
    


if __name__ == "__main__":
    main()
