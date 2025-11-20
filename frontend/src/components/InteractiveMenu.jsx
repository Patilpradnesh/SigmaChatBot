// src/components/InteractiveMenu.jsx
import React from "react";

const actions = [
  { label: "Analyze Location", query: "Analyze ", icon: "📊" },
  { label: "Show Demand Trend", query: "Show demand trend for ", icon: "📉" },
  { label: "Show Price Growth", query: "Show price growth for ", icon: "📈" },
  { label: "Compare Two Locations", query: "Compare ", icon: "⚖️" },
  { label: "List All Places", query: "List places", icon: "🗺️" },
  { label: "Help / What Else", query: "What else", icon: "❓" },
];

export default function InteractiveMenu({ onSelect }) {
  return (
    <div className="bg-white border rounded-xl shadow-md p-4 mt-3">
      <h3 className="font-semibold text-gray-800 mb-2">
        What would you like to do next?
      </h3>

      <div className="grid grid-cols-2 gap-3">
        {actions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(item.query)}
            className="flex items-center gap-2 bg-gray-50 hover:bg-gray-100 
                       transition px-3 py-2 rounded-lg border text-sm"
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}
