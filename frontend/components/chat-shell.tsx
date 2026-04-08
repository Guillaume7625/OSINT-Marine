"use client";

import { useEffect, useMemo, useState } from "react";

import { api, Conversation, DevSettings, Message, RoutingMode, streamConversation, StreamEvent } from "../lib/api";

type UiMessage = Message & { isPending?: boolean };

function formatDateLabel(value?: string | null) {
  if (!value) return "A l'instant";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "A l'instant";

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatSize(bytes: number) {
  if (!bytes) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ChatShell() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [files, setFiles] = useState<Array<{ id: string; filename: string; size_bytes: number; ingestion_status: string }>>([]);
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

  const completedFiles = files.filter((file) => file.ingestion_status === "done").length;
  const userMessages = messages.filter((msg) => msg.role === "user").length;
  const assistantMessages = messages.filter((msg) => msg.role === "assistant").length;
  const headerModel = lastMeta?.model ?? activeConversation?.last_selected_model ?? "-";
  const headerProvider = lastMeta?.provider ?? activeConversation?.provider ?? "-";

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
    const hasKnowledgeBase = files.some((file) => file.ingestion_status === "done");
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
          manual_model: routeMode === "policy" ? undefined : manualModel || undefined,
          user_model_preference: routeMode === "policy" ? manualModel || undefined : undefined,
          temporary_system_prompt: temporaryPrompt || undefined,
          require_tools: hasKnowledgeBase,
          require_rag: hasKnowledgeBase,
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
        <div className="sidebar-topline">Private Intelligence Console</div>
        <div className="brand-block">
          <div className="brand-mark">A</div>
          <div>
            <h1>Atelier Claude</h1>
            <p>Interface premium pour conversations, retrieval et pilotage fin.</p>
          </div>
        </div>

        <button className="primary-button" onClick={createConversation}>
          Nouvelle conversation
        </button>

        <div className="sidebar-section">
          <div className="section-label">Apercu</div>
          <div className="sidebar-stats">
            <article className="stat-card">
              <span className="stat-value">{conversations.length}</span>
              <span className="stat-label">Conversations</span>
            </article>
            <article className="stat-card">
              <span className="stat-value">{completedFiles}</span>
              <span className="stat-label">Sources prêtes</span>
            </article>
            <article className="stat-card">
              <span className="stat-value">{assistantMessages}</span>
              <span className="stat-label">Réponses</span>
            </article>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="section-label">Conversations</div>
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
                <span className="conversation-title">{conversation.title}</span>
                <span className="conversation-meta">
                  {conversation.routing_mode} · {formatDateLabel(conversation.updated_at)}
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="chat-panel">
        <header className="hero-panel">
          <div className="hero-copy">
            <div className="eyebrow">Salon de commandement</div>
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
            <p className="hero-text">
              Une experience plus editoriale, plus calme et plus haut de gamme pour piloter le modele, les fichiers
              et les prompts sans perdre en lisibilite.
            </p>
          </div>

          <div className="hero-side">
            <div className="hero-badges">
              <span className="badge">Provider · {headerProvider}</span>
              <span className="badge">Model · {headerModel}</span>
              <span className="badge">Routing · {lastMeta?.routing_mode ?? routeMode}</span>
              <span className="badge">Prompt · {lastMeta?.prompt_profile ?? devSettings?.prompt_profile.name ?? "default"}</span>
            </div>
            <div className="hero-metrics">
              <article className="metric-panel">
                <span className="metric-kicker">Dialogues</span>
                <strong>{userMessages + assistantMessages}</strong>
              </article>
              <article className="metric-panel">
                <span className="metric-kicker">Fichiers</span>
                <strong>{files.length}</strong>
              </article>
            </div>
            <button className="ghost-button" onClick={() => setSettingsOpen((prev) => !prev)}>
              {settingsOpen ? "Fermer les réglages" : "Ouvrir les réglages"}
            </button>
          </div>
        </header>

        <section className="control-deck">
          <label className="control-card">
            <span className="control-label">Mode de routage</span>
            <select value={routeMode} onChange={(e) => setRouteMode(e.target.value as RoutingMode)}>
              <option value="policy">policy</option>
              <option value="manual">manual</option>
              <option value="locked">locked</option>
            </select>
          </label>

          <label className="control-card">
            <span className="control-label">{routeMode === "policy" ? "Préférence modèle" : "Override modèle"}</span>
            <input
              value={manualModel}
              onChange={(e) => setManualModel(e.target.value)}
              placeholder="e.g. claude-sonnet-4-6"
            />
          </label>

          <label className="control-card control-card-wide">
            <span className="control-label">Système temporaire</span>
            <input
              value={temporaryPrompt}
              onChange={(e) => setTemporaryPrompt(e.target.value)}
              placeholder="Optional one-turn system override"
            />
          </label>
        </section>

        {settingsOpen && (
          <section className="settings-panel">
            <div className="panel-headline">
              <div>
                <div className="section-label">Prompt design</div>
                <h3>Configuration avancée</h3>
              </div>
              <button className="primary-button" onClick={savePrompts}>
                Sauvegarder
              </button>
            </div>

            <label>
              Global prompt
              <textarea value={globalPromptDraft} onChange={(e) => setGlobalPromptDraft(e.target.value)} rows={4} />
            </label>
            <label>
              Workspace prompt
              <textarea value={workspacePromptDraft} onChange={(e) => setWorkspacePromptDraft(e.target.value)} rows={4} />
            </label>
          </section>
        )}

        <section className="files-panel">
          <div className="panel-headline compact">
            <div>
              <div className="section-label">Knowledge base</div>
              <h3>Sources jointes</h3>
            </div>
            <label className="upload-button">
              Importer
              <input type="file" accept=".txt,.md,.pdf,.png,.jpg,.jpeg,.tif,.tiff,.webp,.bmp,.gif" onChange={uploadSelectedFile} />
            </label>
          </div>

          <div className="file-list">
            {files.length === 0 && <div className="empty-pill">Aucun document chargé pour cette conversation.</div>}
            {files.map((file) => (
              <article key={file.id} className="file-card">
                <span className="file-name">{file.filename}</span>
                <span className="file-meta">
                  {file.ingestion_status} · {formatSize(file.size_bytes)}
                </span>
              </article>
            ))}
          </div>
        </section>

        <section className="message-list">
          {messages.length === 0 && (
            <div className="empty-state">
              <div className="section-label">Prêt à écrire</div>
              <h2>Commence une conversation avec une interface plus éditoriale.</h2>
              <p>
                Tu peux piloter le routing, injecter un prompt ponctuel ou enrichir la session avec des documents avant
                de lancer la requête.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <article key={msg.id} className={`message ${msg.role}`}>
              <div className="message-role">{msg.role}</div>
              <div className="message-content">{msg.content || (msg.isPending ? "…" : "")}</div>
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations">
                  {msg.citations.map((citation, index) => (
                    <span key={`${msg.id}-c-${index}`} className="citation-chip">
                      {citation.filename}#{citation.chunk_index}
                      {citation.page_number ? ` · p.${citation.page_number}` : ""}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </section>

        <footer className="composer-shell">
          <div className="composer-copy">
            <div className="section-label">Composer</div>
            <p>Ecris simplement. `Entrée` envoie, `Shift + Entrée` garde le retour à la ligne.</p>
          </div>

          <div className="composer">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Formule ta demande avec précision..."
              rows={3}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void sendMessage();
                }
              }}
            />
            <button className="primary-button send-button" disabled={loading || !activeConversationId} onClick={() => void sendMessage()}>
              {loading ? "Streaming..." : "Envoyer"}
            </button>
          </div>
        </footer>
      </main>

      {error && (
        <div className="toast" role="alert">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Fermer</button>
        </div>
      )}
    </div>
  );
}
