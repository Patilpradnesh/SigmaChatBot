import React from "react";

export default function Loader() {
  return (
    <div className="flex items-center gap-2">
      <div className="w-5 h-5 rounded-full animate-pulse bg-blue-500" />
      <div className="text-sm text-gray-600">Thinking…</div>
    </div>
  );
}
