from src.configs.config import REPO_DIR
from src.repo.cloner import clone_repo
from src.summarizer.file_summarizer import summarize_files
from src.ast.ast_generator import process_repo_ast 
from src.ast.function_locator import extract_function_code, get_called_functions, get_function_and_context
from src.ast.function_explainer import analyze_function

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
    
    name = input("함수 이름을 입력하세요: ").strip()

    context_blocks = get_function_and_context(name)
    
    #print(context_blocks)

    result = analyze_function(context_blocks)
    
    print(result)


if __name__ == "__main__":
    main()
