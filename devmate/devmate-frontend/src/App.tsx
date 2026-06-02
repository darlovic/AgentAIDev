import React, { useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import axios from "axios";
import Sidebar from "./components/Sidebar";
import "./App.css";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Conversation {
  id: number;
  title: string;
}

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentChat, setCurrentChat] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  // Load sidebar conversations (mock data temporaire)
  useEffect(() => {
    // TODO: Remplacer par appel API réel quand backend prêt
    setConversations([
      { id: 1, title: "Docker chat" },
      { id: 2, title: "FastAPI help" },
      { id: 3, title: "React debugging" },
      { id: 4, title: "PostgreSQL query" },
    ]);
  }, []);

  // Create new chat
  const createNewChat = () => {
    const newId = conversations.length + 1;
    const newChat = {
      id: newId,
      title: `New Chat ${newId}`,
    };
    setConversations([newChat, ...conversations]);
    setCurrentChat(newId);
    setMessages([]);
    setStreamingText("");
  };

  // Send message with streaming
  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: message
    };

    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);
    setStreamingText("");

    try {
      const res = await fetch("http://10.139.79.163:8000/chat-stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
          message: userMessage.content,
          conversation_id: currentChat?.toString() || undefined
        })
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      let fullText = "";

      if (!reader) return;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);

        // SSE format: "data: ..."
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const token = line.replace("data: ", "");
            fullText += token;
            setStreamingText(fullText);
          }
        }
      }

      // Une fois le streaming terminé, ajouter le message complet à l'historique
      if (fullText) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: fullText
          }
        ]);
      }
    } catch (err) {
      console.error("Streaming error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: Unable to get response"
        }
      ]);
    }

    setLoading(false);
    setStreamingText("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <Sidebar
        conversations={conversations}
        currentId={currentChat}
        onSelect={setCurrentChat}
        onNewChat={createNewChat}
      />

      <div className="chat-area">
        <div className="messages">
          {messages.length === 0 && !streamingText && (
            <div className="welcome-message">
              <h2>Welcome to DevMate</h2>
              <p>Ask me anything about your code!</p>
              {currentChat && <p className="chat-info">Current chat: {currentChat}</p>}
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div
              key={index}
              className={
                msg.role === "user"
                  ? "message user"
                  : "message assistant"
              }
            >
              {msg.role === "assistant" ? (
                <ReactMarkdown
                  components={{
                    code({ className, children, ...props }: any) {
                      const match = /language-(\w+)/.exec(className || "");
                      return match ? (
                        <SyntaxHighlighter
                          style={oneDark as any}
                          language={match[1]}
                          PreTag="div"
                          {...props}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          ))}

          {/* Message en cours de streaming avec animation curseur */}
          {loading && streamingText && (
            <div className="message assistant streaming">
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "");
                    return match ? (
                      <SyntaxHighlighter
                        style={oneDark as any}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {streamingText}
              </ReactMarkdown>
              <span className="cursor">▊</span>
            </div>
          )}

          {loading && !streamingText && (
            <div className="thinking">
              Thinking...
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <textarea
            placeholder="Ask DevMate..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
