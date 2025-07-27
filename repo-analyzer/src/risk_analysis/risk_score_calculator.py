import json
from pathlib import Path
import re

from src.ast.function_locator import get_function_and_context
from src.commit.commit_analyzer import (
    analyze_function_commits,
    save_commit_analysis
)
from src.configs.config import COMMIT_ANALYSIS_DIR
from src.utils.secrets_loader import load_llm_config

import requests
from openai import OpenAI

# === LLM 설정 ===
provider, LLM_API_KEY, LLM_API_URL, LLM_MODEL = load_llm_config()
USE_OPENAI = provider.lower() == "openai"
if USE_OPENAI:
    client = OpenAI(api_key=LLM_API_KEY)

def calculate_risk_score(file_path: Path, function_name: str, repo_root: Path) -> dict:
    """
    함수의 구조 및 커밋 정보를 바탕으로 리스크 점수를 계산하고 관련 정보를 반환합니다.
    """
    # === 1. AST 기반 구조 정보 수집 ===
    context = get_function_and_context(function_name)
    target = context.get("target")
    if not target:
        raise ValueError(f"[X] 함수 '{function_name}' 정의를 찾을 수 없습니다.")

    internal_count = len(context.get("internal", []))
    called_by_count = target.get("called_by_count", 0)
    code = target.get("code", "")
    function_size = len(code.splitlines())

    # === 2. 커밋 정보 로드 또는 분석 ===
    commit_data_path = COMMIT_ANALYSIS_DIR / f"{function_name}.json"

    if commit_data_path.exists():
        with open(commit_data_path, "r", encoding="utf-8") as f:
            commit_data = json.load(f)
    else:
        commit_data = analyze_function_commits(file_path, function_name, repo_root)
        if not commit_data:
            raise ValueError("[X] 커밋 분석 실패")
        save_commit_analysis(commit_data, file_path, function_name)

    commits = commit_data.get("commit_history", [])
    commit_count = len(commits)
    bug_commit_count = sum(1 for c in commits if c.get("commit_type") == "Bug&Error")

    # === 3. 점수 산정 ===
    score = 0
    score += score_internal_functions(internal_count)
    score += score_called_by(called_by_count)
    score += score_function_size(function_size)
    score += score_commit_count(commit_count)
    score += score_bug_commit_count(bug_commit_count)

    risk_score = round(score / 10, 2)

    return {
        "function": function_name,
        "file": str(file_path),
        "risk_score": risk_score,
        "risk_factors": {
            "internal_function_count": internal_count,
            "called_by_count": called_by_count,
            "function_size": function_size,
            "commit_count": commit_count,
            "bug_commit_count": bug_commit_count
        },
        "code": code
    }


def explain_risk_with_llm(risk_info: dict) -> dict:
    system_prompt = """
당신은 Python 함수의 구조 및 변경 이력을 분석해 수정 시 리스크 요인을 평가하는 전문가입니다.
"""
    user_prompt = f"""
다음은 함수 \"{risk_info['function']}\"의 구조 및 변경 이력을 바탕으로 한 위험도 분석 정보입니다.

- 종합 리스크 점수: {risk_info['risk_score']}점 (1~10점, 높을수록 위험)
[세부 평가 지표]
- 함수 줄 수: {risk_info['risk_factors']['function_size']}줄 (기준: 0~20점)
- 내부 호출 함수 수: {risk_info['risk_factors']['internal_function_count']}개 (기준: 0~20점)
- 호출되는 함수 수: {risk_info['risk_factors']['called_by_count']}개 (기준: 0~20점)
- 관련 커밋 수: {risk_info['risk_factors']['commit_count']}회 (기준: 0~20점)
- 그 중 Bug&Error 커밋 수: {risk_info['risk_factors']['bug_commit_count']}회 (기준: 0~20점)

함수 코드:
```python
{risk_info['code']}
```

이 정보를 바탕으로 다음 JSON 형식으로 설명해주세요:
```json
{{
  "risk_reason": "함수 수정 시 위험한 이유를 설명",
  "highlight_factors": ["function_size", "bug_commit_count", ...]
}}
"""
    try:
        if USE_OPENAI:
            response = client.chat.completions.create(
                model=LLM_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
        else:
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": LLM_MODEL or "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3
            }
            response = requests.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            
        
        
        cleaned = clean_llm_json_response(content)
        return json.loads(cleaned)

    except Exception as e:
        print(f"[!] LLM 분석 실패: {e}")
        return {
            "risk_reason": "LLM 분석 실패",
            "highlight_factors": []
        }


def clean_llm_json_response(text: str) -> str:
    """
    LLM 응답에서 ```json ... ``` 블록을 제거하고 JSON만 반환.
    """
    text = text.strip()
    match = re.search(r"```json\s*(.*?)```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    # fallback: 그냥 ``` ... ```인 경우
    match = re.search(r"```\s*(.*?)```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return text 

# === 요인별 점수 함수 (최대 100점) ===
def score_internal_functions(count: int) -> int:
    if count <= 1: return 0
    if count <= 3: return 5
    if count <= 5: return 10
    if count <= 7: return 15
    return 20

def score_called_by(count: int) -> int:
    if count <= 1: return 0
    if count <= 3: return 5
    if count <= 5: return 10
    if count <= 7: return 15
    return 20

def score_function_size(lines: int) -> int:
    if lines <= 20: return 0
    if lines <= 40: return 5
    if lines <= 60: return 10
    if lines <= 80: return 15
    return 20

def score_commit_count(count: int) -> int:
    if count <= 2: return 0
    if count <= 4: return 5
    if count <= 6: return 10
    if count <= 9: return 15
    return 20

def score_bug_commit_count(count: int) -> int:
    if count == 0: return 0
    if count <= 2: return 5
    if count <= 4: return 10
    if count <= 6: return 15
    return 20
    
def generate_risk_report(file_path: Path, function_name: str, repo_root: Path) -> dict:
    """
    특정 함수에 대해 리스크 점수 계산과 LLM 기반 위험 설명을 모두 수행하고 통합된 결과를 반환합니다.
    """
    risk_info = calculate_risk_score(file_path, function_name, repo_root)
    explanation = explain_risk_with_llm(risk_info)

    # risk_info 딕셔너리에 LLM 결과를 추가하여 하나의 dict로 병합
    return {
        **risk_info,
        **explanation
    }
