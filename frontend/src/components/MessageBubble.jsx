// src/components/MessageBubble.jsx
import React from "react";

export default function MessageBubble({ from, text }) {
  const isUser = from === "user";

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "bg-blue-600 text-white px-4 py-2 rounded-xl shadow-md max-w-[80%]"
            : "bg-gradient-to-r from-indigo-100 to-blue-100 text-gray-900 px-4 py-2 rounded-xl shadow-sm border border-gray-200 max-w-[80%]"
        }
      >
        <pre className="whitespace-pre-wrap text-sm">{text}</pre>
      </div>
    </div>
  );
}

