from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.clone_router import router as clone_router
from api.ast_router import router as ast_router
from api.summary_router import router as summary_router
from api.function_analysis_router import router as function_router
from api.tree_router import router as tree_router

app = FastAPI(
    title="Repo Analyzer API",
    description="Python 프로젝트 분석을 위한 REST API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(clone_router)
app.include_router(ast_router)
app.include_router(summary_router)
app.include_router(function_router)
app.include_router(tree_router)

# 루트 경로 확인용
@app.get("/")
def read_root():
    return {"message": "Repo Analyzer API is running"}


# from src.configs.config import REPO_DIR
# from src.repo.cloner import clone_repo
# from src.summarizer.file_summarizer import summarize_files
# from src.ast.ast_generator import process_repo_ast 
# from src.ast.function_locator import extract_function_code, get_called_functions, get_function_and_context
# from src.ast.function_explainer import analyze_function
# from src.commit.commit_analyzer import analyze_function_commits, save_commit_analysis, get_commit_summary
# from src.risk_analysis.risk_score_calculator import calculate_risk_score, explain_risk_with_llm, generate_risk_report
# from pathlib import Path
# from pprint import pprint

# def main():
#     # repo_url = input("Enter Git repo URL: ").strip()
#     # repo_branch = input("Enter branch name: ").strip()
#     # repo_path = clone_repo(repo_url, REPO_DIR, repo_branch)

#     # if not repo_path:
#     #     print("\n[X] Repository clone failed.")
#     #     return

#     # print(f"\n[✓] Repository ready at: {repo_path}")

#     # summarize_files(repo_path)
    
#     # process_repo_ast(repo_path)
    
#     # name = input("함수 이름을 입력하세요: ").strip()

#     # context_blocks = get_function_and_context(name)
    
#     # print(context_blocks)

#     # result = analyze_function(context_blocks)
    
#     # print(result)
    
#     # repo_root = REPO_DIR / "whereami" 
#     # file_path = repo_root / "whereami" / "predict.py"
#     # function_name = "crossval"

#     # print(f"[*] 분석 시작: {file_path} / 함수: {function_name}")
#     # result = analyze_function_commits(file_path=file_path, function_name=function_name, repo_root=repo_root)

#     # if result:
#     #     save_commit_analysis(result, file_path=file_path, function_name=function_name)
#     #     print("[+] 분석 완료 및 저장됨.")
#     # else:
#     #     print("[!] 분석 실패 또는 결과 없음.")
    
    
#     function_name = "train_model"
#     repo_root = Path("data/cloned_repo/whereami")  # .git 있는 디렉토리
#     file_path = repo_root / "whereami/pipeline.py"

#     # risk_info = calculate_risk_score(file_path, function_name, repo_root)

#     # explanation = explain_risk_with_llm(risk_info)

    
#     result = generate_risk_report(file_path, function_name, repo_root)
#     print(result)


# if __name__ == "__main__":
#     main()
