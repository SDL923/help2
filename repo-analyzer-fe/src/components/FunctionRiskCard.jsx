// src/components/FunctionRiskCard.jsx
import { AlertTriangle, CheckCircle } from "lucide-react";

export default function FunctionRiskCard({ risk }) {
  if (!risk) return null;

  const {
    risk_score,
    risk_factors,
    risk_reason
  } = risk;

  // 색상 결정 (초록~노랑~빨강)
  const getColor = (score) => {
    if (score >= 8) return "text-red-600";
    if (score >= 5) return "text-yellow-500";
    return "text-green-600";
  };

  const getIcon = (score) => {
    if (score >= 5) return <AlertTriangle className="inline-block w-5 h-5 mr-1" />;
    return <CheckCircle className="inline-block w-5 h-5 mr-1" />;
  };

  return (
    <div>
      <div className={`text-lg font-semibold mb-3 flex items-center ${getColor(risk_score)}`}>
        {getIcon(risk_score)}
        종합 리스크 점수: {risk_score} / 10
      </div>

      <ul className="text-sm text-gray-700 space-y-1 mb-3">
        <li>📌 내부 호출 함수 수: {risk_factors.internal_function_count}</li>
        <li>📌 상위 함수 수: {risk_factors.called_by_count}</li>
        <li>📌 함수 길이 (줄 수): {risk_factors.function_size}</li>
        <li>📌 관련 커밋 수: {risk_factors.commit_count}</li>
        <li>📌 버그 커밋 수: {risk_factors.bug_commit_count}</li>
      </ul>

      <p className="text-sm text-gray-800 leading-relaxed">
        💡<span className="font-medium">Risk Analysis:</span> {risk_reason}
      </p>
    </div>
  );
}
