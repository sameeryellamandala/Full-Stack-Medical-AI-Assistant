"use client";

import { SignInButton, UserButton, useUser, Show } from "@clerk/nextjs";
import { useState } from "react";
import { Upload, Send, Loader2 } from "lucide-react";

export default function Home() {
  const { user } = useUser(); 
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || !user) return;
    const userMessage = input;
    setInput("");
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const formData = new FormData();
      formData.append("user_id", user.id);
      formData.append("thread_id", `thread_${user.id}`);
      formData.append("message", userMessage);

      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setMessages((prev) => [...prev, { role: "ai", content: data.response }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "ai", content: "Error: Is the Python backend running?" }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between p-4 bg-white shadow-sm border-b">
        <h1 className="text-xl font-bold text-blue-600">Med-AI Assistant</h1>
        <div>
          <Show when="signed-out"><SignInButton mode="modal"><button className="px-4 py-2 bg-blue-600 text-white rounded-md">Log In</button></SignInButton></Show>
          <Show when="signed-in"><UserButton /></Show>
        </div>
      </header>

      <Show when="signed-in">
        <div className="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col">
          <div className="flex-1 bg-white rounded-lg shadow-sm border p-4 mb-4 overflow-y-auto flex flex-col gap-4">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-center mt-10">Welcome! How can I help you today?</p>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`p-3 rounded-lg max-w-[80%] ${msg.role === "user" ? "bg-blue-600 text-white self-end" : "bg-gray-100 text-gray-800 self-start"}`}>
                  {msg.content}
                </div>
              ))
            )}
            {isLoading && <Loader2 className="w-5 h-5 animate-spin text-blue-600 self-start" />}
          </div>
          <div className="flex items-center gap-2 bg-white p-2 rounded-lg border shadow-sm">
            <Upload className="w-5 h-5 text-gray-400 ml-2" />
            <input 
              type="text" 
              className="flex-1 p-2 outline-none text-gray-800" 
              placeholder="Ask a medical question..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button onClick={handleSend} className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"><Send className="w-5 h-5" /></button>
          </div>
        </div>
      </Show>

      <Show when="signed-out">
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Your Professional AI Medical Assistant</h2>
          <p className="text-gray-600 mb-8 max-w-md">Securely analyze reports, ask questions, and manage your health data with GenAI.</p>
          <SignInButton mode="modal"><button className="px-8 py-3 bg-blue-600 text-white rounded-lg text-lg font-semibold">Get Started</button></SignInButton>
        </div>
      </Show>
    </main>
  );
}