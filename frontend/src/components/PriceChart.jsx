// src/components/PriceChart.jsx
import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function PriceChart({ data }) {
  return (
    <div>
      <h3 className="text-lg font-medium mb-2">Price Trend</h3>
      <div className="w-full h-64">
        <ResponsiveContainer>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip />
            <Line dataKey="price" stroke="#2563eb" strokeWidth={2} dot={{r:3}} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
