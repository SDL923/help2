// src/api/repoService.js
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function cloneRepo(repoUrl, branch) {
  const res = await axios.post(`${BASE_URL}/clone`, {
    repo_url: repoUrl,
    branch,
  });
  return res.data;
}

export async function generateAST(repoName) {
  const res = await axios.post(`${BASE_URL}/generate-ast`, {
    repo_name: repoName,
  });
  return res.data;
}

export async function summarizeFiles(repoName) {
  const res = await axios.post(`${BASE_URL}/summarize`, {
    repo_name: repoName,
  });
  return res.data;
}
