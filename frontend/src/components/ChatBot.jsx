// src/components/Chatbot.jsx
import React, { useState, useRef, useEffect } from "react";

import MessageBubble from "./MessageBubble.jsx";
import Loader from "./Loader.jsx";
import PriceChart from "./PriceChart.jsx";
import DataTable from "./DataTable.jsx";
import PlacesList from "./PlacesList.jsx";
import CompareChart from "./CompareChart.jsx";
import DemandChart from "./DemandChart.jsx";
import InteractiveMenu from "./InteractiveMenu.jsx";

const BACKEND_URL = "http://127.0.0.1:8000/api/analyze/";

export default function Chatbot() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Right panel data
  const [chartData, setChartData] = useState(null);
  const [tableData, setTableData] = useState(null);
  const [places, setPlaces] = useState(null);
  const [compareData, setCompareData] = useState(null);
  const [demandData, setDemandData] = useState(null);

  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current)
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, loading]);

  const sendQuery = async (customQuery = null) => {
    const text = (customQuery || query).trim();
    if (!text) return;

    // Add user message
    setMessages((prev) => [...prev, { from: "user", text }]);
    setQuery("");
    setLoading(true);

    // Reset right panel
    setChartData(null);
    setTableData(null);
    setPlaces(null);
    setCompareData(null);
    setDemandData(null);

    try {
      const res = await fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });

      const data = await res.json();

      // Add bot text reply
      setMessages((prev) => [
        ...prev,
        {
          from: "bot",
          text: data.summary || data.error || "Response received.",
        },
      ]);

      // Right panel logic
      if (data.chart) {
        const merged = data.chart.years.map((yr, i) => ({
          year: yr,
          price: data.chart.prices[i],
        }));
        setChartData(merged);
      }

      if (data.table) setTableData(data.table);
      if (data.places) setPlaces(data.places);
      if (data.compare) setCompareData(data.compare);
      if (data.demand) setDemandData(data.demand);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: "Network error: " + err.message },
      ]);
    }

    setLoading(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading) sendQuery();
  };

  return (
    <div className="flex max-w-7xl mx-auto gap-6 mt-10 px-4">
      {/* LEFT CHAT PANEL */}
      <div className="w-1/2 bg-white/80 backdrop-blur-lg shadow-xl border border-white/40 rounded-2xl flex flex-col">
        {/* Header */}
        <div className="p-5 border-b">
          <h1 className="text-xl font-semibold">SigmaChatBot</h1>
          <p className="text-gray-600 text-sm">
            Ask anything like <code>Analyze Wakad</code> or{" "}
            <code>Compare Wakad and Aundh</code>
          </p>
        </div>

        {/* Chat Messages */}
        <div
          ref={chatRef}
          className="h-[430px] overflow-y-auto p-5 flex flex-col gap-3"
        >
          {messages.map((msg, idx) => (
            <MessageBubble key={idx} from={msg.from} text={msg.text} />
          ))}

          {messages.length > 0 &&
            messages[messages.length - 1].from === "bot" && (
              <InteractiveMenu
                onSelect={(prompt) => {
                  if (prompt.endsWith(" ")) {
                    setQuery(prompt);
                  } else {
                    sendQuery(prompt);
                  }
                }}
              />
            )}

          {loading && <Loader />}
        </div>

        {/* Input bar */}
        <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your message…"
            className="flex-1 px-3 py-2 border rounded-lg"
          />
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg">
            Send
          </button>
        </form>
      </div>

      {/* RIGHT RESULT PANEL */}
      <div className="w-1/2 bg-white shadow rounded-xl border p-5 space-y-6 h-[680px] overflow-y-auto">
        {chartData && <PriceChart data={chartData} />}
        {tableData && <DataTable data={tableData} />}

        {places && (
          <PlacesList
            places={places}
            onPick={(p) => sendQuery(`Analyze ${p}`)}
          />
        )}

        {compareData && <CompareChart data={compareData} />}
        {demandData && <DemandChart data={demandData} />}
      </div>
    </div>
  );
}
