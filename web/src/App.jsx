import { useEffect, useMemo, useRef, useState } from "react";
import {
  createSession,
  getCurrentUser,
  listMessages,
  listSessions,
  login,
  register,
  sendMessage
} from "./api";

const TOKEN_KEY = "sunmark_auth_token";

function formatTime(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch (_error) {
    return "";
  }
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messagesRequestIdRef = useRef(0);
  const messagesContainerRef = useRef(null);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) || null,
    [sessions, activeSessionId]
  );

  function isUnauthorized(err) {
    return (
      err?.status === 401 ||
      String(err?.message || "").toLowerCase().includes("could not validate credentials")
    );
  }

  function resetAuthState(nextError = "") {
    localStorage.removeItem(TOKEN_KEY);
    setToken("");
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    setDraft("");
    setError(nextError);
  }

  function getSessionLabel(session) {
    if (!session) return "New Chat";
    const title = String(session.title || "").trim();
    if (!title || title.toLowerCase() === "new chat") {
      return `Chat ${session.id}`;
    }
    return title;
  }

  useEffect(() => {
    if (!token) return;
    localStorage.setItem(TOKEN_KEY, token);
  }, [token]);

  useEffect(() => {
    async function bootstrap() {
      if (!token) return;
      setLoading(true);
      setError("");
      try {
        const [me, allSessions] = await Promise.all([
          getCurrentUser(token),
          listSessions(token)
        ]);
        setUser(me);
        setSessions(allSessions);
        setActiveSessionId((prev) => prev || allSessions[0]?.id || null);
      } catch (err) {
        resetAuthState(err.message);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, [token]);

  useEffect(() => {
    async function loadMessages() {
      if (!token || !activeSessionId) {
        setMessages([]);
        return;
      }
      const requestId = ++messagesRequestIdRef.current;
      setLoading(true);
      setError("");
      try {
        const items = await listMessages(token, activeSessionId);
        if (requestId !== messagesRequestIdRef.current) return;
        setMessages(items);
      } catch (err) {
        if (requestId !== messagesRequestIdRef.current) return;
        if (isUnauthorized(err)) {
          resetAuthState("Session expired. Please log in again.");
          return;
        }
        setError(err.message);
      } finally {
        if (requestId !== messagesRequestIdRef.current) return;
        setLoading(false);
      }
    }
    loadMessages();
  }, [token, activeSessionId]);

  useEffect(() => {
    if (!messagesContainerRef.current) return;
    messagesContainerRef.current.scrollTo({
      top: messagesContainerRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages, activeSessionId]);

  async function handleAuthSubmit(e) {
    e.preventDefault();
    if (authMode === "register" && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      if (authMode === "register") {
        await register(email.trim(), password);
      }
      const auth = await login(email.trim(), password);
      setToken(auth.access_token);
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleNewSession() {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const session = await createSession(token);
      const allSessions = await listSessions(token);
      setSessions(allSessions);
      setActiveSessionId(session.id);
      setMessages([]);
    } catch (err) {
      if (isUnauthorized(err)) {
        resetAuthState("Session expired. Please log in again.");
        return;
      }
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !token || sending) return;

    setSending(true);
    setError("");
    setDraft("");

    let sessionId = activeSessionId;
    let tempMessageId = null;
    try {
      if (!sessionId) {
        const created = await createSession(token);
        sessionId = created.id;
        setActiveSessionId(created.id);
        setSessions((prev) => [created, ...prev]);
      }

      tempMessageId = Date.now();
      const tempUserMessage = {
        id: tempMessageId,
        role: "user",
        content: text,
        created_at: new Date().toISOString()
      };

      setMessages((prev) => [...prev, tempUserMessage]);
      const res = await sendMessage(token, sessionId, text);
      const refreshed = await listMessages(token, sessionId);
      setMessages(refreshed);

      if (!res.response) {
        setError("No response from chat service.");
      }
    } catch (err) {
      if (tempMessageId) {
        setMessages((prev) => prev.filter((msg) => msg.id !== tempMessageId));
      }
      if (isUnauthorized(err)) {
        resetAuthState("Session expired. Please log in again.");
        return;
      }
      setError(err.message);
    } finally {
      setSending(false);
    }
  }

  function handleLogout() {
    resetAuthState("");
  }

  if (!token) {
    return (
      <main className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">Sunmark Bot</p>
          <h1>School Assistant</h1>
          <p className="subtitle">
            Sign in to manage sessions and chat with your RAG assistant.
          </p>
          <form onSubmit={handleAuthSubmit} className="auth-form">
            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
            </label>
            {authMode === "register" ? (
              <label>
                Confirm Password
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  minLength={6}
                  required
                />
              </label>
            ) : null}
            <button disabled={loading} type="submit">
              {loading
                ? "Please wait..."
                : authMode === "login"
                ? "Login"
                : "Create account"}
            </button>
          </form>
          <button
            className="switch-mode"
            type="button"
            onClick={() => {
              setAuthMode((m) => (m === "login" ? "register" : "login"));
              setError("");
              setPassword("");
              setConfirmPassword("");
            }}
          >
            {authMode === "login"
              ? "Need an account? Register"
              : "Already have an account? Login"}
          </button>
          {error ? <p className="error-text">{error}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div>
            <p className="eyebrow">Sunmark Bot</p>
            <h2>Conversations</h2>
          </div>
          <button onClick={handleNewSession} disabled={loading}>
            + New
          </button>
        </div>
        <div className="session-list">
          {sessions.length === 0 ? (
            <p className="muted">No sessions yet. Start one.</p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                className={`session-item ${
                  session.id === activeSessionId ? "active" : ""
                }`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <span>{getSessionLabel(session)}</span>
                <small>{formatTime(session.created_at)}</small>
              </button>
            ))
          )}
        </div>
      </aside>

      <section className="chat-panel">
        <header className="chat-header">
          <div>
            <p className="muted">
              Logged in as <strong>{user?.email}</strong>
            </p>
            <h1>{activeSession ? getSessionLabel(activeSession) : "New Chat"}</h1>
          </div>
          <button className="logout" onClick={handleLogout}>
            Logout
          </button>
        </header>

        <div className="messages" ref={messagesContainerRef}>
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>Ask anything about Sunmarke School</h3>
              <p>Admissions, fees, curriculum, transport, events and more.</p>
            </div>
          ) : (
            messages.map((msg) => (
              <article key={msg.id} className={`bubble ${msg.role}`}>
                <p>{msg.content}</p>
                <small>{formatTime(msg.created_at)}</small>
              </article>
            ))
          )}
        </div>

        <form className="composer" onSubmit={handleSend}>
          <input
            type="text"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Type your question..."
            disabled={sending}
            required
          />
          <button type="submit" disabled={sending || !draft.trim()}>
            {sending ? "Sending..." : "Send"}
          </button>
        </form>

        {error ? <p className="error-text">{error}</p> : null}
      </section>
    </main>
  );
}
