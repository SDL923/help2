// src/components/LoadingOverlay.jsx
export default function LoadingOverlay({ message = "로딩 중..." }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-white/60 z-50">
      <div className="text-center">
        <div className="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-gray-700 text-lg font-medium">{message}</p>
      </div>
    </div>
  );
}
