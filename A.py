# src/commit_analysis/function_commit_tracker.py

import subprocess
import json
from pathlib import Path
from collections import Counter
from datetime import datetime
from typing import List, Dict, Optional

import requests
from openai import OpenAI
from src.utils.secrets_loader import load_llm_config
from src.configs.config import BASE_DATA_DIR

# === 저장 경로 설정 ===
COMMIT_ANALYSIS_DIR = BASE_DATA_DIR / "commit_analysis"
COMMIT_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_root
        )
        return result.stdout
    except Exception as e:
        print(f"[!] git log -L failed: {e}")
        return ""

def parse_git_log(log_output: str) -> List[Dict]:
    commits = []
    lines = log_output.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("commit "):
            current = {"diff": "", "message": ""}
            current["hash"] = line.split()[1]
            i += 1

            # Parse metadata
            while i < len(lines):
                line = lines[i]
                if line.startswith("Author: "):
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
                    break
                i += 1

            # Parse commit message (indented lines)
            message_lines = []
            while i < len(lines) and lines[i].startswith("    "):
                message_lines.append(lines[i].strip())
                i += 1
            current["message"] = " ".join(message_lines)

            # Parse diff (until next commit or end)
            diff_lines = []
            while i < len(lines) and not lines[i].startswith("commit "):
                diff_lines.append(lines[i])
                i += 1
            current["diff"] = "\n".join(diff_lines).strip()

            commits.append(current)
        else:
            i += 1

    return commits

def analyze_function_commits(file_path: Path, function_name: str, repo_root: Path) -> Optional[Dict]:
    if not (repo_root / ".git").exists():
        raise ValueError(f"{repo_root} is not a valid Git repository")

    log_output = run_git_log_L(function_name, file_path, repo_root)
    if not log_output:
        return None

    commits_raw = parse_git_log(log_output)
    if not commits_raw:
        return None

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
    rel_path = file_path.relative_to(Path.cwd()).as_posix().replace("/", "__")
    save_path = COMMIT_ANALYSIS_DIR / f"{rel_path}__{function_name}.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
