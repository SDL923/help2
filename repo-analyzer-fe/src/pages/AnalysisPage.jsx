import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import axios from "axios";
import FunctionCommitStats from "../components/FunctionCommitStats";
import FunctionRiskCard from "../components/FunctionRiskCard";


export default function AnalysisPage() {
  const { state } = useLocation();
  const repoName = state?.repoName;

  const [tree, setTree] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [functions, setFunctions] = useState([]);
  const [summary, setSummary] = useState(null);

  const [selectedFunction, setSelectedFunction] = useState(null);
  const [functionDesc, setFunctionDesc] = useState(null);
  const [relatedFunctions, setRelatedFunctions] = useState([]);
  const [functionCommits, setFunctionCommits] = useState(null);
  const [functionRisk, setFunctionRisk] = useState(null);

  useEffect(() => {
    if (!repoName) return;
    axios
      .get(`${import.meta.env.VITE_API_BASE_URL}/repo/tree`, {
        params: { repo_name: repoName },
      })
      .then((res) => setTree(res.data))
      .catch((err) => console.error("트리 불러오기 실패", err));
  }, [repoName]);

  useEffect(() => {
    if (!selectedFile) return;

    axios
      .get(`${import.meta.env.VITE_API_BASE_URL}/file/functions`, {
        params: {
          repo_name: repoName,
          file_path: selectedFile,
        },
      })
      .then((res) => setFunctions(res.data.functions))
      .catch((err) => {
        setFunctions([]);
        console.error("함수 목록 불러오기 실패", err);
      });

    axios
      .get(`${import.meta.env.VITE_API_BASE_URL}/file/summary`, {
        params: {
          repo_name: repoName,
          file_path: selectedFile,
        },
      })
      .then((res) => setSummary(res.data?.description || null))
      .catch(() => setSummary(null));
  }, [selectedFile]);

  useEffect(() => {
    if (!selectedFunction || !selectedFile) return;

    axios
      .post(`${import.meta.env.VITE_API_BASE_URL}/function/explain`, {
        function_name: selectedFunction,
      })
        .then((res) => {
        setFunctionDesc(res.data.analysis.description);
        setRelatedFunctions(res.data.analysis.related_functions || []);
      })
      .catch(() => {
        setFunctionDesc(null);
        setRelatedFunctions([]);
      });

    axios
      .post(`${import.meta.env.VITE_API_BASE_URL}/function/commits`, {
        repo_name: repoName,
        file_path: selectedFile,
        function_name: selectedFunction,
      })
      .then((res) => setFunctionCommits(res.data.summary))
      .catch(() => setFunctionCommits(null));


    axios
      .post(`${import.meta.env.VITE_API_BASE_URL}/function/risk`, {
        repo_name: repoName,
        file_path: selectedFile,
        function_name: selectedFunction,
      })
      .then((res) => setFunctionRisk(res.data.risk_report));
  }, [selectedFunction]);

  const renderTree = (node) => {
    if (node.type === "file") {
      return (
        <div
          key={node.path}
          className={`pl-4 py-1 cursor-pointer hover:text-blue-600 ${
            selectedFile === node.path ? "text-blue-700 font-semibold" : ""
          }`}
          onClick={() => {
            setSelectedFile(node.path);
            setSelectedFunction(null);
            setFunctionDesc(null);
            setFunctionCommits(null);
            setRelatedFunctions([]);
            setFunctionRisk(null);
          }}
        >
          📄 {node.name}
        </div>
      );
    }

    return (
      <div key={node.name} className="pl-2">
        <div className="font-medium text-gray-700">📁 {node.name}</div>
        <div className="pl-2">
          {node.children?.map((child) => renderTree(child))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-1/3 max-w-sm bg-white border-r p-4 overflow-y-auto">
        <h2 className="text-lg font-bold text-gray-800 mb-4">📂 프로젝트 구조</h2>
        {tree ? renderTree(tree) : <p>로딩 중...</p>}
      </aside>

      {/* Main panel */}
      <main className="flex-1 p-6 overflow-y-auto">
        {selectedFile && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-blue-600 flex items-center gap-4">
              🧠 {selectedFile}
            </h2>
            <p className="text-gray-500 text-sm mt-4">
              {summary ? `📄 ${summary}` : "📄 요약 정보 없음"}
            </p>
          </div>
        )}

        <div className="flex gap-6">
          {/* 함수 목록 */}
          <div className="w-1/3 pr-4 border-r">
            <h3 className="text-sm text-gray-500 mb-2">📑 함수 목록</h3>
            <div className="space-y-2">
              {functions.map((func) => (
                <div
                  key={func}
                  className={`cursor-pointer border rounded-md px-3 py-2 ${
                    selectedFunction === func
                      ? "bg-blue-100 border-blue-300 text-blue-800 font-semibold"
                      : "bg-white hover:bg-gray-50"
                  }`}
                  onClick={() => {
                    setSelectedFunction(func);
                    setFunctionDesc(null);
                    setFunctionCommits(null);
                    setRelatedFunctions([]);
                    setFunctionRisk(null);
                  }}
                >
                  <code>def {func}()</code>
                </div>
              ))}
            </div>
          </div>

          {/* 설명 영역 */}
          <div className="w-2/3 pl-4"> 
            <h3 className="text-sm text-gray-500 mb-2">🧾 함수 설명</h3>
            <div className="bg-white border rounded-md p-4 min-h-[80px]">
              {selectedFunction && !functionDesc ? (
                <p className="text-blue-500 italic">함수 설명을 불러오는 중...</p>
              ) : selectedFunction ? (
                <p className="text-gray-800 text-sm">{functionDesc}</p>
              ) : (
                <p className="text-gray-400 italic">함수를 선택해주세요</p>
              )}
            </div>

            {/* 커밋 통계 */}
            <h3 className="text-sm text-gray-500 mt-6 mb-2">📊 커밋 통계</h3>
            <div className="bg-white border rounded-md p-4">
              {selectedFunction && !functionCommits ? (
                <p className="text-blue-500 italic">커밋 통계를 불러오는 중...</p>
              ) : selectedFunction ? (
                <FunctionCommitStats summary={functionCommits} />
              ) : (
                <p className="text-gray-400 italic">함수를 선택해주세요</p>
              )}
            </div>

            {/* 관련 함수 추천 */}
            <h3 className="text-sm text-gray-500 mt-6 mb-2">🔗 참고 함수 목록</h3>
            <div className="bg-white border rounded-md p-4 min-h-[100px]">
              {selectedFunction && relatedFunctions.length === 0 ? (
                <p className="text-blue-500 italic">관련 함수를 불러오는 중...</p>
              ) : (
                <ol className="space-y-4 list-decimal pl-5 text-sm text-gray-800">
                  {relatedFunctions.map((item, index) => (
                    <li key={`${item.function}-${index}`}>
                      <p className="font-semibold">{item.function}</p>
                      <p className="text-xs text-gray-500 mb-1">{item.file}</p>
                      <p className="text-gray-700 text-sm">↳ {item.reason}</p>
                    </li>
                  ))}
                </ol>
              )}
            </div>

            {/* 함수 리스크 분석 */}
            <h3 className="text-sm text-gray-500 mt-6 mb-2">⚠️ 함수 수정 시 리스크 분석</h3>
            <div className="bg-white border rounded-md p-4 min-h-[100px]">
              {selectedFunction && !functionRisk ? (
                <p className="text-blue-500 italic">리스크 분석 정보를 불러오는 중...</p>
              ) : selectedFunction ? (
                <FunctionRiskCard risk={functionRisk} />
              ) : (
                <p className="text-gray-400 italic">함수를 선택해주세요</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
