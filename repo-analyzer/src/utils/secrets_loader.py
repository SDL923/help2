import yaml
from pathlib import Path

def load_llm_config():
    secrets_file = Path("secrets.yml")
    if not secrets_file.exists():
        raise FileNotFoundError("secrets.yml 파일이 존재하지 않습니다.")

    with open(secrets_file, "r", encoding="utf-8") as f:
        secrets = yaml.safe_load(f)

    if "llama" in secrets:
        config = secrets["llama"]
        provider = "llama"
    elif "openai" in secrets:
        config = secrets["openai"]
        provider = "openai"
    else:
        raise ValueError("secrets.yml에 'llama' 또는 'openai' 섹션이 필요합니다.")

    api_key = config.get("api_key")
    api_url = config.get("api_url")
    model = config.get("model")  # OpenAI만 해당, llama일 경우 None

    if not api_key or not api_url:
        raise ValueError(f"{provider} 설정에 api_key 또는 api_url이 없습니다.")

    return provider, api_key, api_url, model
