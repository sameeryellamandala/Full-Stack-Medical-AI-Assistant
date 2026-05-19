"use client";

import { SignInButton, UserButton, useAuth, useUser } from "@clerk/nextjs";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  Upload, Send, Loader2, FileText, CheckCircle, XCircle, X,
  Plus, MessageSquare, Trash2, Menu, ChevronLeft, Clock
} from "lucide-react";

// ==========================================
// TYPES
// ==========================================
interface ChunkPreview {
  chunk_number: number;
  preview: string;
  char_count: number;
}

interface UploadResult {
  status: string;
  message: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  chunk_previews: ChunkPreview[];
}

interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  active_document: string;
  created_at: string;
  updated_at: string;
}

interface ChatMessage {
  id?: number;
  role: string;
  content: string;
  created_at?: string;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

// ==========================================
// HELPER: Group sessions by date
// ==========================================
function groupSessionsByDate(sessions: ChatSession[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const sevenDaysAgo = new Date(today.getTime() - 7 * 86400000);
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 86400000);

  const groups: { label: string; sessions: ChatSession[] }[] = [
    { label: "Today", sessions: [] },
    { label: "Yesterday", sessions: [] },
    { label: "Previous 7 Days", sessions: [] },
    { label: "Previous 30 Days", sessions: [] },
    { label: "Older", sessions: [] },
  ];

  for (const session of sessions) {
    const d = new Date(session.updated_at + "Z"); // UTC
    if (d >= today) groups[0].sessions.push(session);
    else if (d >= yesterday) groups[1].sessions.push(session);
    else if (d >= sevenDaysAgo) groups[2].sessions.push(session);
    else if (d >= thirtyDaysAgo) groups[3].sessions.push(session);
    else groups[4].sessions.push(session);
  }

  return groups.filter((g) => g.sessions.length > 0);
}

const API_BASE = "http://127.0.0.1:8000";

// ==========================================
// MAIN COMPONENT
// ==========================================
export default function Home() {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  // Sidebar
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Chat
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeDocument, setActiveDocument] = useState<string>("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Upload
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string>("");
  const [uploadFileName, setUploadFileName] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ==========================================
  // LOAD SESSIONS
  // ==========================================
  const loadSessions = useCallback(async () => {
    if (!user) return;
    setLoadingSessions(true);
    try {
      const res = await fetch(`${API_BASE}/sessions?user_id=${user.id}`);
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error("Failed to load sessions:", err);
    } finally {
      setLoadingSessions(false);
    }
  }, [user]);

  useEffect(() => {
    if (isSignedIn && user) {
      loadSessions();
    }
  }, [isSignedIn, user, loadSessions]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ==========================================
  // CREATE NEW CHAT
  // ==========================================
  const handleNewChat = async () => {
    if (!user) return;
    try {
      const formData = new FormData();
      formData.append("user_id", user.id);
      formData.append("title", "New Chat");
      const res = await fetch(`${API_BASE}/sessions`, { method: "POST", body: formData });
      const session = await res.json();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setActiveDocument("");
      setUploadStatus("idle");
      setUploadResult(null);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  // ==========================================
  // LOAD A PREVIOUS CHAT
  // ==========================================
  const handleLoadSession = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
      const data = await res.json();
      setActiveSessionId(sessionId);
      setActiveDocument(data.session?.active_document || "");
      setMessages(
        (data.messages || []).map((m: ChatMessage) => ({
          role: m.role,
          content: m.content,
        }))
      );
      setUploadStatus("idle");
      setUploadResult(null);
      // Close sidebar on mobile
      if (window.innerWidth < 768) setSidebarOpen(false);
    } catch (err) {
      console.error("Failed to load session:", err);
    }
  };

  // ==========================================
  // DELETE A CHAT
  // ==========================================
  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId("");
        setMessages([]);
        setActiveDocument("");
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  // ==========================================
  // SEND MESSAGE
  // ==========================================
  const handleSend = async () => {
    if (!input.trim() || !user) return;

    // Auto-create session if none is active
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const formData = new FormData();
        formData.append("user_id", user.id);
        formData.append("title", "New Chat");
        if (activeDocument) formData.append("active_document", activeDocument);
        const res = await fetch(`${API_BASE}/sessions`, { method: "POST", body: formData });
        const session = await res.json();
        currentSessionId = session.id;
        setActiveSessionId(session.id);
        setSessions((prev) => [session, ...prev]);
      } catch (err) {
        console.error("Failed to create session:", err);
        return;
      }
    }

    const userMessage = input;
    setInput("");
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      const formData = new FormData();
      formData.append("user_id", user.id);
      formData.append("thread_id", currentSessionId);
      formData.append("message", userMessage);
      formData.append("active_document", activeDocument);
      formData.append("session_id", currentSessionId);

      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "ai", content: `Error: ${data.detail || "Something went wrong."}` },
        ]);
      } else {
        setMessages((prev) => [...prev, { role: "ai", content: data.response }]);
      }

      // Refresh sessions to update titles/timestamps
      loadSessions();
    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages((prev) => [
        ...prev,
        { role: "ai", content: "Sorry, I couldn't connect to the server." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // ==========================================
  // UPLOAD PDF
  // ==========================================
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadStatus("error");
      setUploadError("Only PDF files are supported.");
      return;
    }

    // Auto-create session if none is active
    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      try {
        const formData = new FormData();
        formData.append("user_id", user.id);
        formData.append("title", `📄 ${file.name}`);
        formData.append("active_document", file.name);
        const res = await fetch(`${API_BASE}/sessions`, { method: "POST", body: formData });
        const session = await res.json();
        currentSessionId = session.id;
        setActiveSessionId(session.id);
        setSessions((prev) => [session, ...prev]);
      } catch (err) {
        console.error("Failed to create session:", err);
        return;
      }
    }

    setUploadFileName(file.name);
    setUploadStatus("uploading");
    setUploadResult(null);
    setUploadError("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", user.id);
      formData.append("session_id", currentSessionId);

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setUploadStatus("error");
        setUploadError(data.detail || "Upload failed. Please try again.");
      } else {
        setUploadStatus("success");
        setUploadResult(data);
        setActiveDocument(data.filename);
        setMessages((prev) => [
          ...prev,
          {
            role: "ai",
            content: `📄 ${data.filename} uploaded successfully!\n📊 ${data.total_pages} pages → ${data.total_chunks} chunks processed and stored in Pinecone.\n\n🔍 All your questions will now be answered from this document.`,
          },
        ]);
        loadSessions(); // Refresh sidebar
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus("error");
      setUploadError("Could not connect to server. Make sure the backend is running.");
    }

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const dismissUpload = () => {
    setUploadStatus("idle");
    setUploadResult(null);
    setUploadError("");
    setUploadFileName("");
  };

  // ==========================================
  // RENDER
  // ==========================================
  const groupedSessions = groupSessionsByDate(sessions);

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-blue-50/30 overflow-hidden">
      {/* ========== SIDEBAR ========== */}
      <aside
        className={`${
          sidebarOpen ? "w-72" : "w-0"
        } flex-shrink-0 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 text-white transition-all duration-300 overflow-hidden flex flex-col`}
      >
        {/* Sidebar Header */}
        <div className="p-3 flex items-center justify-between border-b border-white/10">
          <button
            onClick={handleNewChat}
            className="flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 transition-all duration-200 text-sm font-medium shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-2 p-2 rounded-lg hover:bg-white/10 transition"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
          {loadingSessions ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-8">No chats yet</p>
          ) : (
            groupedSessions.map((group) => (
              <div key={group.label}>
                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider px-2 mb-1.5">
                  {group.label}
                </p>
                <div className="space-y-0.5">
                  {group.sessions.map((session) => (
                    <div
                      key={session.id}
                      onClick={() => handleLoadSession(session.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === "Enter" && handleLoadSession(session.id)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-2 group transition-all duration-200 text-sm cursor-pointer ${
                        activeSessionId === session.id
                          ? "bg-gradient-to-r from-blue-600/30 to-indigo-600/20 text-white border border-blue-500/30"
                          : "text-gray-300 hover:bg-white/5"
                      }`}
                    >
                      {session.active_document ? (
                        <FileText className="w-4 h-4 flex-shrink-0 text-blue-400" />
                      ) : (
                        <MessageSquare className="w-4 h-4 flex-shrink-0 text-gray-500" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-medium">{session.title}</p>
                        {session.active_document && (
                          <p className="text-[11px] text-gray-500 truncate mt-0.5">{session.active_document}</p>
                        )}
                      </div>
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); handleDeleteSession(session.id, e as unknown as React.MouseEvent); }}}
                        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-red-500/20 transition-all flex-shrink-0"
                        title="Delete chat"
                      >
                        <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-400 transition-colors" />
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Sidebar Footer - User Info */}
        {isLoaded && isSignedIn && (
          <div className="p-3 border-t border-white/10 flex items-center gap-2 bg-black/20">
            <UserButton />
            <span className="text-sm text-gray-400 truncate">{user?.fullName || "User"}</span>
          </div>
        )}
      </aside>

      {/* ========== MAIN AREA ========== */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200/50 flex-shrink-0">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
            )}
            <div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Med-AI Assistant</h1>
              {activeDocument && (
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="inline-flex items-center gap-1 text-[11px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium border border-emerald-200/50">
                    <FileText className="w-3 h-3" />
                    {activeDocument}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div>
            {!isLoaded && (
              <div className="w-20 h-9 bg-gray-200 rounded-xl animate-pulse" />
            )}
            {isLoaded && !isSignedIn && (
              <SignInButton mode="modal">
                <button className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all text-sm font-medium">
                  Log In
                </button>
              </SignInButton>
            )}
          </div>
        </header>

        {/* Chat Area or Landing */}
        {isLoaded && isSignedIn ? (
          <div className="flex-1 flex flex-col min-h-0 max-w-4xl w-full mx-auto">
            {/* Upload Banners */}
            <div className="px-4 pt-3 flex-shrink-0">
              {uploadStatus === "uploading" && (
                <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-3 animate-pulse">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-600 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-blue-800 text-sm">Processing: {uploadFileName}</p>
                    <p className="text-xs text-blue-600">Splitting → Embedding → Storing in Pinecone...</p>
                  </div>
                </div>
              )}
              {uploadStatus === "success" && uploadResult && (
                <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="font-medium text-green-800 text-sm">{uploadResult.message}</p>
                        <p className="text-xs text-green-700 mt-0.5">
                          📄 {uploadResult.total_pages} pages → 🧩 {uploadResult.total_chunks} chunks
                        </p>
                        {uploadResult.chunk_previews.length > 0 && (
                          <div className="mt-2 space-y-1 max-h-28 overflow-y-auto">
                            {uploadResult.chunk_previews.map((chunk) => (
                              <div key={chunk.chunk_number} className="flex items-start gap-1.5 text-xs bg-white/60 p-1.5 rounded border border-green-100">
                                <span className="bg-green-200 text-green-800 px-1 py-0.5 rounded font-mono flex-shrink-0 text-[10px]">
                                  #{chunk.chunk_number}
                                </span>
                                <span className="text-green-900 line-clamp-2">{chunk.preview}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <button onClick={dismissUpload} className="p-1 hover:bg-green-100 rounded transition flex-shrink-0">
                      <X className="w-3.5 h-3.5 text-green-600" />
                    </button>
                  </div>
                </div>
              )}
              {uploadStatus === "error" && (
                <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    <XCircle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-medium text-red-800 text-sm">Upload Failed</p>
                      <p className="text-xs text-red-600">{uploadError}</p>
                    </div>
                  </div>
                  <button onClick={dismissUpload} className="p-1 hover:bg-red-100 rounded transition flex-shrink-0">
                    <X className="w-3.5 h-3.5 text-red-600" />
                  </button>
                </div>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 pb-2">
              <div className="flex flex-col gap-3 py-4">
                {messages.length === 0 ? (
                  <div className="text-center mt-16">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-xl shadow-blue-500/20">
                      <FileText className="w-10 h-10 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">How can I help you today?</h2>
                    <p className="text-gray-500 text-sm max-w-md mx-auto leading-relaxed">
                      Upload a medical PDF document, then ask questions about it.<br/>Your chat history is automatically saved.
                    </p>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-3.5 rounded-2xl max-w-[85%] text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white self-end rounded-br-md shadow-md shadow-blue-500/15"
                          : "bg-white border border-gray-100 self-start rounded-bl-md text-gray-800 shadow-md shadow-gray-200/50"
                      }`}
                    >
                      <p className="whitespace-pre-line">{msg.content}</p>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="p-3 rounded-xl bg-white border border-gray-200 self-start shadow-sm rounded-bl-sm">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                      <span className="text-sm text-gray-500">Thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="px-4 pb-4 flex-shrink-0">
              <div className="flex items-center gap-2 bg-white p-2.5 rounded-2xl border border-gray-200/80 shadow-lg shadow-gray-200/40">
                <label
                  className={`cursor-pointer p-2 rounded-lg transition flex-shrink-0 ${
                    uploadStatus === "uploading" ? "bg-blue-100 cursor-wait" : "hover:bg-gray-100"
                  }`}
                >
                  {uploadStatus === "uploading" ? (
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  ) : (
                    <Upload className="w-5 h-5 text-gray-500" />
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept=".pdf"
                    onChange={handleFileUpload}
                    disabled={uploadStatus === "uploading"}
                  />
                </label>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  placeholder="Ask a medical question..."
                  className="flex-1 p-2 outline-none bg-transparent text-gray-900 placeholder-gray-400 text-sm"
                  disabled={isLoading}
                />
                <button
                  onClick={handleSend}
                  disabled={isLoading || !input.trim()}
                  className="p-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-30 disabled:shadow-none flex-shrink-0"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Logged Out / Loading */
          <div className="flex-1 flex flex-col items-center justify-center">
            {!isLoaded ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-48 h-8 bg-gray-200 rounded animate-pulse" />
                <div className="w-64 h-5 bg-gray-200 rounded animate-pulse" />
              </div>
            ) : (
              <>
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl flex items-center justify-center mb-6 shadow-2xl shadow-blue-500/25">
                  <FileText className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mb-3">Professional Medical AI</h2>
                <p className="text-gray-500 mb-8 text-sm">Please log in to access your secure chat history.</p>
                <SignInButton mode="modal">
                  <button className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:shadow-xl hover:shadow-blue-500/30 transition-all font-medium text-sm">
                    Get Started
                  </button>
                </SignInButton>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}