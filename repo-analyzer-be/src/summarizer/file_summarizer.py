import os
import json
import requests
from pathlib import Path
from openai import OpenAI
from src.utils.secrets_loader import load_llm_config
from src.configs.config import SUMMARY_DIR
from src.configs.filter_config import EXCLUDED_DIRS, EXCLUDED_FILES

provider, LLM_API_KEY, LLM_API_URL, LLM_MODEL = load_llm_config()
USE_OPENAI = provider.lower() == "openai"

if USE_OPENAI:
    client = OpenAI(api_key=LLM_API_KEY)

SYSTEM_PROMPT = """
당신은 Python 코드를 구조적으로 분석해서 요약하는 전문가입니다.
"""

USER_PROMPT_TEMPLATE = """
다음은 하나의 Python 파일입니다. 이 파일의 핵심 구조와 기능을 요약해 주세요.

요약 결과는 반드시 **JSON 형식**으로 작성하며, 다음 항목을 포함해야 합니다:

- file: (string) 파일 이름
- description: (string) 이 파일이 수행하는 주요 역할, 기능 설명
- key_functions: (list of strings) 핵심 함수 이름 목록
- key_classes: (list of strings) 핵심 클래스 이름 목록
- depends_on: (list of strings) 이 파일이 import한 외부 모듈 또는 다른 내부 파일 이름

반드시 JSON으로만 응답하고, 주석이나 설명을 추가하지 마세요.

파일명: {filename}

```python
{code}
```
"""

def should_summarize(filepath: Path) -> bool:
    if not filepath.suffix == ".py":
        return False
    if filepath.name in EXCLUDED_FILES:
        return False
    if any(part in EXCLUDED_DIRS for part in filepath.parts):
        return False
    if filepath.stat().st_size < 30:
        return False
    return True

def summarize_file_with_llm(filepath: Path) -> dict:
    try:
        code = filepath.read_text(encoding="utf-8")
        prompt = USER_PROMPT_TEMPLATE.format(filename=str(filepath.name), code=code[:6000])

        if USE_OPENAI:
            response = client.chat.completions.create(
                model=LLM_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            summary = response.choices[0].message.content.strip()
        else:
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
            }
            response = requests.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            summary = response.json()["choices"][0]["message"]["content"].strip()

        if summary.startswith("```json"):
            summary = summary.lstrip("`json\n").rstrip("`").strip()
        elif summary.startswith("```"):
            summary = summary.lstrip("`").strip()

        return json.loads(summary)

    except Exception as e:
        print(f"[!] Error summarizing {filepath}: {e}")
        return None

def summarize_files(repo_path: Path):
    print(f"[*] Summarizing Python files in: {repo_path}")
    for root, _, files in os.walk(repo_path):
        for file in files:
            path = Path(root) / file
            if should_summarize(path):
                rel_path = path.relative_to(repo_path)
                safe_name = str(rel_path).replace("/", "__").replace("\\", "__")
                save_path = SUMMARY_DIR / (safe_name + ".json")

                if save_path.exists():
                    print(f"[-] Skipping (already summarized): {rel_path}")
                    continue

                print(f"[+] Summarizing: {rel_path}")
                summary = summarize_file_with_llm(path)
                if summary:
                    with open(save_path, "w", encoding="utf-8") as f:
                        json.dump(summary, f, indent=2, ensure_ascii=False)

# def summarize_files(repo_path: Path):
#     print(f"[*] Summarizing Python files in: {repo_path}")
#     for root, _, files in os.walk(repo_path):
#         for file in files:
#             path = Path(root) / file
#             if should_summarize(path):
#                 print(f"[+] Summarizing: {path.relative_to(repo_path)}")
#                 summary = summarize_file_with_llm(path)
#                 if summary:
#                     rel_path = path.relative_to(repo_path)
#                     safe_name = str(rel_path).replace("/", "__").replace("\\", "__")
#                     save_path = SUMMARY_DIR / (safe_name + ".json")
#                     with open(save_path, "w", encoding="utf-8") as f:
#                         json.dump(summary, f, indent=2, ensure_ascii=False)

def load_summary(file_path: Path) -> dict:
    """
    주어진 파일 경로에 해당하는 요약 JSON을 로드합니다.
    예: file_path = Path("whereami/utils.py") -> whereami__utils.py.json
    """
    rel_path = str(file_path).replace("/", "__").replace("\\", "__") + ".json"
    summary_path = SUMMARY_DIR / rel_path

    if not summary_path.exists():
        raise FileNotFoundError(f"No summary found for file: {file_path}")
    
    with open(summary_path, "r", encoding="utf-8") as f:
        return json.load(f)
