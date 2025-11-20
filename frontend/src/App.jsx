// src/App.jsx
import Navbar from "./components/Navbar";
import Chatbot from "./components/ChatBot";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="p-6">
        <Chatbot />
      </div>
    </div>
  );
}
