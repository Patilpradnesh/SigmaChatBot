// src/components/Navbar.jsx
import React from "react";

export default function Navbar() {
  return (
    <nav className="w-full bg-white/80 backdrop-blur-md shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-3">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Sigma RealEstate AI
        </h1>

        <div className="flex gap-6 text-sm text-gray-600 font-medium">
          <button className="hover:text-blue-600 transition">Home</button>
          <button className="hover:text-blue-600 transition">Chat</button>
          <button className="hover:text-blue-600 transition">Dataset</button>
          <button className="hover:text-blue-600 transition">About</button>
        </div>
      </div>
    </nav>
  );
}
