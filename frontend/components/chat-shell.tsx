"use client";

import { useEffect, useMemo, useState } from "react";

import { api, Conversation, DevSettings, Message, RoutingMode, streamConversation, StreamEvent } from "../lib/api";

type UiMessage = Message & { isPending?: boolean };

export function ChatShell() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [files, setFiles] = useState<Array<{ id: string; filename: string; size_bytes: number }>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routeMode, setRouteMode] = useState<RoutingMode>("policy");
  const [manualModel, setManualModel] = useState("");
  const [temporaryPrompt, setTemporaryPrompt] = useState("");
  const [lastMeta, setLastMeta] = useState<StreamEvent | null>(null);
  const [devSettings, setDevSettings] = useState<DevSettings | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [globalPromptDraft, setGlobalPromptDraft] = useState("");
  const [workspacePromptDraft, setWorkspacePromptDraft] = useState("");

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeConversationId) ?? null,
    [conversations, activeConversationId],
  );

  useEffect(() => {
    void bootstrap();
  }, []);

  async function bootstrap() {
    try {
      const [allConversations, settings] = await Promise.all([api.listConversations(), api.getDevSettings()]);
      setConversations(allConversations);
      setDevSettings(settings);
      setGlobalPromptDraft(settings.prompt_profile.global_prompt);
      setWorkspacePromptDraft(settings.prompt_profile.workspace_prompt);

      if (allConversations.length === 0) {
        const created = await api.createConversation("New Conversation");
        setConversations([created]);
        setActiveConversationId(created.id);
        setRouteMode(created.routing_mode);
        await loadConversation(created.id);
      } else {
        const first = allConversations[0];
        setActiveConversationId(first.id);
        setRouteMode(first.routing_mode);
        setManualModel(first.manual_model ?? "");
        await loadConversation(first.id);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function loadConversation(conversationId: string) {
    const [detail, fileList] = await Promise.all([api.getConversation(conversationId), api.listFiles(conversationId)]);
    setMessages(detail.messages);
    setFiles(fileList);
    setRouteMode(detail.conversation.routing_mode);
    setManualModel(detail.conversation.manual_model ?? "");
  }

  async function createConversation() {
    try {
      const created = await api.createConversation("New Conversation");
      setConversations((prev) => [created, ...prev]);
      setActiveConversationId(created.id);
      setMessages([]);
      setFiles([]);
      setLastMeta(null);
      setRouteMode(created.routing_mode);
      setManualModel("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function saveTitle(title: string) {
    if (!activeConversationId) return;
    try {
      const updated = await api.renameConversation(activeConversationId, title);
      setConversations((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function sendMessage() {
    if (!activeConversationId || !input.trim() || loading) return;
    const userText = input.trim();
    setInput("");
    setLoading(true);

    const userMessage: UiMessage = {
      id: `u-${Date.now()}`,
      conversation_id: activeConversationId,
      role: "user",
      content: userText,
    };

    const assistantPendingId = `a-${Date.now()}`;
    const assistantPending: UiMessage = {
      id: assistantPendingId,
      conversation_id: activeConversationId,
      role: "assistant",
      content: "",
      isPending: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPending]);

    try {
      await streamConversation(
        activeConversationId,
        {
          message: userText,
          route_mode: routeMode,
          manual_model: manualModel || undefined,
          temporary_system_prompt: temporaryPrompt || undefined,
          require_tools: true,
          require_rag: true,
        },
        (event) => {
          if (event.type === "meta") {
            setLastMeta(event);
          } else if (event.type === "token") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantPendingId
                  ? {
                      ...msg,
                      content: msg.content + (event.delta ?? ""),
                    }
                  : msg,
              ),
            );
          } else if (event.type === "done") {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantPendingId
                  ? {
                      ...msg,
                      isPending: false,
                      citations: event.citations,
                    }
                  : msg,
              ),
            );
          } else if (event.type === "error") {
            setError(event.error ?? "Streaming error");
          }
        },
      );

      const detail = await api.getConversation(activeConversationId);
      setMessages(detail.messages);
      const nextConversations = await api.listConversations();
      setConversations(nextConversations);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function uploadSelectedFile(event: React.ChangeEvent<HTMLInputElement>) {
    if (!activeConversationId || !event.target.files?.[0]) return;
    const file = event.target.files[0];
    try {
      await api.uploadFile(activeConversationId, file);
      const list = await api.listFiles(activeConversationId);
      setFiles(list);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      event.target.value = "";
    }
  }

  async function savePrompts() {
    try {
      const updated = await api.updateDevSettings({
        prompt: {
          global_prompt: globalPromptDraft,
          workspace_prompt: workspacePromptDraft,
        },
      });
      setDevSettings(updated);
      setSettingsOpen(false);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>Assistant</h1>
          <button onClick={createConversation}>New</button>
        </div>
        <div className="conversation-list">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              className={conversation.id === activeConversationId ? "conversation-item active" : "conversation-item"}
              onClick={async () => {
                setActiveConversationId(conversation.id);
                await loadConversation(conversation.id);
              }}
            >
              {conversation.title}
            </button>
          ))}
        </div>
      </aside>

      <main className="chat-panel">
        <header className="chat-header">
          <input
            className="title-input"
            value={activeConversation?.title ?? ""}
            onChange={(e) => {
              const title = e.target.value;
              setConversations((prev) =>
                prev.map((item) => (item.id === activeConversationId ? { ...item, title } : item)),
              );
            }}
            onBlur={(e) => void saveTitle(e.target.value)}
            placeholder="Conversation title"
          />

          <div className="meta-strip">
            <span>Provider: {lastMeta?.provider ?? activeConversation?.provider ?? "-"}</span>
            <span>Model: {lastMeta?.model ?? activeConversation?.last_selected_model ?? "-"}</span>
            <span>Routing: {lastMeta?.routing_mode ?? routeMode}</span>
            <span>Prompt: {lastMeta?.prompt_profile ?? devSettings?.prompt_profile.name ?? "default"}</span>
            <button onClick={() => setSettingsOpen((prev) => !prev)}>Dev Settings</button>
          </div>

          <div className="controls-row">
            <label>
              Routing mode
              <select value={routeMode} onChange={(e) => setRouteMode(e.target.value as RoutingMode)}>
                <option value="policy">policy</option>
                <option value="manual">manual</option>
                <option value="locked">locked</option>
              </select>
            </label>

            {(routeMode === "manual" || routeMode === "locked") && (
              <label>
                Model override
                <input
                  value={manualModel}
                  onChange={(e) => setManualModel(e.target.value)}
                  placeholder="e.g. claude-sonnet-4-6"
                />
              </label>
            )}

            <label className="grow">
              Temporary system override
              <input
                value={temporaryPrompt}
                onChange={(e) => setTemporaryPrompt(e.target.value)}
                placeholder="Optional one-turn system override"
              />
            </label>
          </div>
        </header>

        {settingsOpen && (
          <section className="settings-panel">
            <h3>Prompt Configuration</h3>
            <label>
              Global prompt
              <textarea value={globalPromptDraft} onChange={(e) => setGlobalPromptDraft(e.target.value)} rows={4} />
            </label>
            <label>
              Workspace prompt
              <textarea value={workspacePromptDraft} onChange={(e) => setWorkspacePromptDraft(e.target.value)} rows={4} />
            </label>
            <button onClick={savePrompts}>Save prompts</button>
          </section>
        )}

        <section className="files-panel">
          <label className="upload-label">
            Upload txt/md/pdf
            <input type="file" accept=".txt,.md,.pdf" onChange={uploadSelectedFile} />
          </label>
          <div className="file-list">
            {files.map((file) => (
              <span key={file.id}>{file.filename}</span>
            ))}
          </div>
        </section>

        <section className="message-list">
          {messages.map((msg) => (
            <article key={msg.id} className={`message ${msg.role}`}>
              <div className="message-role">{msg.role}</div>
              <div className="message-content">{msg.content || (msg.isPending ? "…" : "")}</div>
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations">
                  {msg.citations.map((citation, index) => (
                    <span key={`${msg.id}-c-${index}`}>
                      {citation.filename}#{citation.chunk_index}
                      {citation.page_number ? ` (p.${citation.page_number})` : ""}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </section>

        <footer className="composer">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something..."
            rows={3}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void sendMessage();
              }
            }}
          />
          <button disabled={loading || !activeConversationId} onClick={() => void sendMessage()}>
            {loading ? "Streaming..." : "Send"}
          </button>
        </footer>
      </main>

      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
    </div>
  );
}
