// src/components/DataTable.jsx
import React from "react";

export default function DataTable({ data }) {
  if (!data || data.length === 0) return null;
  const cols = Object.keys(data[0]);
  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Table (first 20 rows)</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              {cols.map((c) => <th key={c} className="p-2 text-left border-b">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {data.slice(0,20).map((row, i) => (
              <tr key={i} className="odd:bg-white even:bg-gray-50">
                {cols.map((c) => <td key={c} className="p-2 align-top">{String(row[c] ?? "")}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
