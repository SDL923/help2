import json
import requests
from openai import OpenAI
from src.utils.secrets_loader import load_llm_config

provider, LLM_API_KEY, LLM_API_URL, LLM_MODEL = load_llm_config()
USE_OPENAI = provider.lower() == "openai"

if USE_OPENAI:
    client = OpenAI(api_key=LLM_API_KEY)

SYSTEM_PROMPT = """
당신은 Python 프로젝트 분석 전문가입니다. 함수와 관련된 코드 구조를 기반으로 함수의 역할을 정확히 파악하고, 관련 함수들을 추천할 수 있습니다.
"""

USER_PROMPT_TEMPLATE = """
다음은 특정 함수에 대한 코드 분석 결과입니다. 

1. 이 함수가 수행하는 기능을 명확하고 상세하게 설명해 주세요.
2. 이 함수와 함께 참고하면 도움이 되는 다른 함수들을 중요도 순으로 추천해 주세요. 가능하면 3개 이상 추천하되, 연관된 함수가 적다면 그보다 적어도 괜찮습니다.
   - 내부적으로 호출하는 함수, 호출한 상위 함수, 연관 흐름을 기준으로 판단하세요.

반드시 아래 JSON 형식으로만 응답해야 하며, 설명 외의 어떠한 부가 텍스트도 포함하지 마세요.

결과 형식:
```json
{
  "description": "이 함수의 기능을 명확히 설명한 내용",
  "related_functions": [
    {
      "function": "함수 이름",
      "file": "파일 경로 (예: utils/logger.py)",
      "reason": "왜 이 함수를 함께 참고하면 좋은지에 대한 설명"
    }
  ]
}
```

입력 데이터:
```json
{context_data}
```
"""

def analyze_function(context: dict) -> dict | None:
    try:
        context_str = json.dumps(context, indent=2, ensure_ascii=False)
        prompt = USER_PROMPT_TEMPLATE.replace("{context_data}", context_str)

        if USE_OPENAI:
            response = client.chat.completions.create(
                model=LLM_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content.strip()
        else:
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            response = requests.post(LLM_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            
        # 코드 블럭 감지 제거
        if content.startswith("```json"):
            content = content.lstrip("`json\n").rstrip("`").strip()
        elif content.startswith("```"):
            content = content.lstrip("`").strip()
        
        return json.loads(content)

    except Exception as e:
        print(f"[!] 분석 실패: {e}")
        return None
