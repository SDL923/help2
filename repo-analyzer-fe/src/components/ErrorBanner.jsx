// src/components/ErrorBanner.jsx
export default function ErrorBanner({ message }) {
  return (
    <div className="bg-red-100 text-red-700 border border-red-300 px-4 py-3 rounded-md mb-4">
      ⚠️ {message}
    </div>
  );
}
