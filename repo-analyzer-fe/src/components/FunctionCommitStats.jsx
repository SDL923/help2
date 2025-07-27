const COMMIT_TYPE_COLORS = {
  "Bug&Error": "bg-red-500",
  Feature: "bg-green-500",
  Refactor: "bg-blue-500",
  Documentation: "bg-purple-500",
  "Code Style": "bg-gray-400",
  Other: "bg-orange-400",
};

export default function FunctionCommitStats({ summary }) {
  if (!summary) return null;

  const { total_commits, top_authors, type_distribution } = summary;

  const sortedAuthors = Object.entries(top_authors).sort((a, b) => b[1] - a[1]);
  const sortedTypes = Object.entries(type_distribution).sort((a, b) => b[1] - a[1]);

  const maxCount = Math.max(...sortedTypes.map(([_, count]) => count));

  return (
    <div>
      <p className="text-sm font-semibold text-gray-600 rounded-md px-1 py-0 inline-block mb-0">
        총 {total_commits}개의 Commit
      </p>

      <div className="flex gap-8 mt-0">
        {/* 왼쪽: 작성자 정보 */}
        <div className="w-1/2 mt-3">
          {/* <p className="text-sm font-midium mb-2 text-gray-600">작성자</p> */}
          <ul className="space-y-2">
            {sortedAuthors.map(([name, count]) => (
              <li key={name} className="flex items-center text-sm text-gray-800">
                <span className="mr-2 text-blue-500">👤</span>
                <span className="font-medium">{name}</span>
                <span className="ml-2 text-gray-500">({count}회)</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 오른쪽: 커밋 유형 정보 */}
        <div className="w-1/2">
          {/* <p className="text-sm font-midium mb-2 text-gray-600">커밋 유형</p> */}
          <div className="space-y-2">
            {sortedTypes.map(([type, count]) => {
              const color = COMMIT_TYPE_COLORS[type] || "bg-gray-300";
              const barWidth = Math.max((count / maxCount) * 100, 8);
              return (
                <div key={type}>
                  <div className="flex justify-between text-sm mb-1">
                    <span>{type}</span>
                    <span className="text-gray-500">{count}회</span>
                  </div>
                  <div className="w-full h-3 bg-gray-200 rounded-md">
                    <div
                      className={`h-full rounded-md ${color}`}
                      style={{ width: `${barWidth}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
