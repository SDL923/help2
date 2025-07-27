// src/pages/Home.jsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import LoadingOverlay from "../components/LoadingOverlay";
import ErrorBanner from "../components/ErrorBanner";
import {
  cloneRepo,
  generateAST,
  summarizeFiles
} from "../api/repoService";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setError("");
    setLoading(true);
    try {
      const { repo_name } = await cloneRepo(repoUrl, branch);
      await generateAST(repo_name);
      await summarizeFiles(repo_name);
      navigate("/analysis", { state: { repoName: repo_name } });
    } catch (err) {
      setError("❗️레포지토리 클론 또는 분석 중 오류가 발생했습니다. URL과 브랜치를 확인해 주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="w-full max-w-lg bg-white p-8 rounded-xl shadow-lg">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-blue-600 mb-2">📘 Repo Analyzer</h1>
          <p className="text-gray-500">Git 레포지토리를 분석하여 구조를 시각화합니다</p>
        </div>

        {error && <ErrorBanner message={error} />}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              📦 Repository URL
            </label>
            <input
              type="text"
              placeholder="https://github.com/user/repo.git"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              🌿 Branch (default: main)
            </label>
            <input
              type="text"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="w-full border px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-md transition"
          >
            분석 시작
          </button>
        </form>
      </div>

      {loading && <LoadingOverlay message="레포지토리 분석 중..." />}
    </div>
  );
}
