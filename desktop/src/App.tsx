import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import "./App.css";

interface Message {
  role: "user" | "ai";
  content: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "Hi! I'm Vaivi. Press Alt+V anytime to ask me about your screen." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Listen for Alt+V shortcut triggered in backend
    const unlisten = listen("shortcut-triggered", async () => {
      // Auto-capture screen when Vaivi is opened via hotkey
      analyzeScreen();
    });

    return () => {
      unlisten.then((f) => f());
    };
  }, []);

  const analyzeScreen = async (query?: string) => {
    setLoading(true);
    try {
      // 1. Take screenshot via Tauri Rust
      const base64Image = await invoke<string>("take_screenshot");
      
      // Convert base64 to Blob for FastAPI
      const res = await fetch(base64Image);
      const blob = await res.blob();
      
      const formData = new FormData();
      formData.append("image", blob, "screenshot.png");
      if (query) {
        formData.append("query", query);
      }

      // 2. Send to localhost FastAPI backend
      const backendRes = await fetch("http://localhost:8000/analyze-screen", {
        method: "POST",
        body: formData,
      });

      const data = await backendRes.json();
      
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: data.response || "No response received." }
      ]);
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Error analyzing screen: " + String(e) }
      ]);
    }
    setLoading(false);
  };

  const askText = async (text: string) => {
    setLoading(true);
    try {
      const backendRes = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      const data = await backendRes.json();
      setMessages((prev) => [...prev, { role: "ai", content: data.response }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "ai", content: "Error: " + String(e) }]);
    }
    setLoading(false);
  };

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input;
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    
    // Choose whether to just ask text or analyze screen with text
    // For Vaivi, the primary feature is screen context. So we can default to analyzing screen
    analyzeScreen(userMsg);
  };

  const handleHide = async () => {
    await invoke("hide_window");
  };

  return (
    <div className="container">
      <div className="header">
        <div className="title">Vaivi Assistant</div>
        <button className="close-btn" onClick={handleHide}>✖</button>
      </div>
      
      <div className="chat-area">
        {messages.map((m, idx) => (
          <div key={idx} className={`message ${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && <div className="message ai loading">Vaivi is thinking...</div>}
      </div>

      <div className="input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me something..."
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>Send</button>
      </div>
    </div>
  );
}

export default App;
