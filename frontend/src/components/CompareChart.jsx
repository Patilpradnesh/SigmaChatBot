// src/components/CompareChart.jsx
import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function CompareChart({ data }) {
  // Data = { location1: [...], location2: [...] }
  const locations = Object.keys(data);
  if (locations.length < 2) return null;

  const loc1 = locations[0];
  const loc2 = locations[1];

  // Normalize structure for recharts
  const combined = [];

  data[loc1].forEach((item, i) => {
    combined.push({
      year: item.year,
      [loc1]: item.value,
      [loc2]: data[loc2][i] ? data[loc2][i].value : null,
    });
  });

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">Comparison Chart</h3>
      <div className="w-full h-72">
        <ResponsiveContainer>
          <LineChart data={combined}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Legend />

            <Line dataKey={loc1} stroke="#3b82f6" strokeWidth={2} dot={false} />
            <Line dataKey={loc2} stroke="#ef4444" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
