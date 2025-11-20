// src/components/PlacesList.jsx
import React from "react";

export default function PlacesList({ places = [], onPick = () => {} }) {
  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Places</h3>
      <div className="flex flex-wrap gap-2">
        {places.map((p, i) => (
          <button key={i} onClick={() => onPick(p)}
                  className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-sm">
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

