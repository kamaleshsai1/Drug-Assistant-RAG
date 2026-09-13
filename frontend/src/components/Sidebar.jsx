import { useMemo, useState } from "react";
import {
  Pill,
  Plus,
  Search,
  MessageSquare,
  Library as LibraryIcon,
  Trash2,
  LogOut,
  X,
  UserCircle,
  FileText,
  ArrowRight,
} from "lucide-react";
import ConfirmationModal from "./ConfirmationModal";

function Sidebar({
  user,
  chats = [],
  activeChatId = null,
  currentView = "chat",
  onNewChat,
  onViewChat,
  onSelectChat,
  onDeleteChat,
  onLibrary,
  onLogout,
  mobileOpen = false,
  onClose,
  onOpenPrivacy,
  onOpenTerms,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [deleteTargetId, setDeleteTargetId] = useState(null);

  // ============================================================
  // SEARCH CHATS
  // ============================================================

  const filteredChats = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();

    if (!term) {
      return Array.isArray(chats) ? chats : [];
    }

    return (Array.isArray(chats) ? chats : []).filter(
      (chat) =>
        String(chat?.title || "New Chat")
          .toLowerCase()
          .includes(term)
    );
  }, [chats, searchTerm]);

  // ============================================================
  // DELETE CHAT
  // ============================================================

  const handleDelete = (event, chatId) => {
    event.stopPropagation();
    setDeleteTargetId(chatId);
  };

  const confirmDelete = () => {
    if (deleteTargetId && typeof onDeleteChat === "function") {
      onDeleteChat(deleteTargetId);
    }
    setDeleteTargetId(null);
  };

  // ============================================================
  // NEW CHAT
  // ============================================================

  const handleNewChat = () => {
    if (typeof onNewChat === "function") {
      onNewChat();
    }

    onClose?.();
  };

  // ============================================================
  // SELECT CHAT
  // ============================================================

  const handleSelectChat = (chatId) => {
    if (typeof onSelectChat === "function") {
      onSelectChat(chatId);
    }

    onClose?.();
  };

  // ============================================================
  // OPEN LIBRARY
  // ============================================================

  const handleLibrary = () => {
    if (typeof onLibrary === "function") {
      onLibrary();
    }

    onClose?.();
  };

  // ============================================================
  // USER INITIAL
  // ============================================================

  const userName = user?.name || "User";

  const userInitial = String(userName)
    .trim()
    .charAt(0)
    .toUpperCase() || "U";

  return (
    <>
      {/* ========================================================
          MOBILE OVERLAY
      ======================================================== */}

      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* ========================================================
          SIDEBAR
      ======================================================== */}

      <aside
        className={`sidebar ${
          mobileOpen ? "sidebar-mobile-open" : ""
        }`}
      >
        {/* ======================================================
            HEADER
        ====================================================== */}

        <div className="sidebar-header">
          <div className="brand">
            <div className="brand-icon">
              <Pill
                size={20}
                strokeWidth={2.2}
              />
            </div>

            <div className="brand-text">
              <div className="brand-name">
                DrugAssist
              </div>

              <div className="brand-subtitle">
                Evidence-first drug intelligence
              </div>
            </div>
          </div>

          {/* Mobile close button */}
          <button
            type="button"
            className="sidebar-close"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X size={20} />
          </button>
        </div>

        {/* ======================================================
            NEW CHAT
        ====================================================== */}

        <div className="sidebar-action-area">
          <button
            type="button"
            className="new-chat-button"
            onClick={handleNewChat}
          >
            <Plus
              size={19}
              strokeWidth={2.3}
            />

            <span>New chat</span>
          </button>
        </div>

        {/* ======================================================
            SEARCH
        ====================================================== */}

        <div className="sidebar-search">
          <Search size={17} />

          <input
            type="text"
            placeholder="Search chats"
            value={searchTerm}
            onChange={(event) =>
              setSearchTerm(event.target.value)
            }
            aria-label="Search chats"
          />

          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm("")}
              aria-label="Clear search"
              style={{
                border: "none",
                background: "transparent",
                padding: 0,
                margin: 0,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <X size={15} />
            </button>
          )}
        </div>

        {/* ======================================================
            NAVIGATION
        ====================================================== */}

        <div className="sidebar-navigation">
          {/* CHAT */}

          <button
            type="button"
            className={`sidebar-nav-item ${
              currentView === "chat" ? "sidebar-nav-item-active" : ""
            }`}
            onClick={() => {
              if (typeof onViewChat === "function") {
                onViewChat();
              } else {
                handleNewChat();
              }
              onClose?.();
            }}
          >
            <MessageSquare size={18} />

            <span>Chat</span>
          </button>

          {/* LIBRARY */}

          <button
            type="button"
            className={`sidebar-nav-item ${
              currentView === "library" ? "sidebar-nav-item-active" : ""
            }`}
            onClick={handleLibrary}
          >
            <LibraryIcon size={18} />

            <span>Library</span>
          </button>
        </div>

        {/* ======================================================
            RECENT CHATS
        ====================================================== */}

        <div className="recent-section">
          <div className="section-heading">
            <span>Recent</span>

            {chats.length > 0 && (
              <span className="chat-count">
                {chats.length}
              </span>
            )}
          </div>

          <div className="chat-list">
            {filteredChats.length === 0 ? (
              <div className="empty-chats">
                <MessageSquare size={20} />

                <span>
                  {searchTerm
                    ? "No matching chats"
                    : "No conversations yet"}
                </span>
              </div>
            ) : (
              filteredChats.map((chat) => {
                const chatId = chat?.id;

                const isActive =
                  String(chatId) ===
                  String(activeChatId);

                return (
                  <button
                    type="button"
                    key={chatId}
                    className={`chat-item ${
                      isActive
                        ? "chat-item-active"
                        : ""
                    }`}
                    onClick={() =>
                      handleSelectChat(chatId)
                    }
                  >
                    <MessageSquare
                      className="chat-item-icon"
                      size={17}
                    />

                    <span className="chat-title">
                      {chat?.title ||
                        "New Chat"}
                    </span>

                    {/* Delete */}
                    <span
                      className="chat-delete"
                      role="button"
                      tabIndex={0}
                      aria-label={`Delete ${
                        chat?.title ||
                        "chat"
                      }`}
                      onClick={(event) =>
                        handleDelete(
                          event,
                          chatId
                        )
                      }
                      onKeyDown={(event) => {
                        if (
                          event.key ===
                            "Enter" ||
                          event.key === " "
                        ) {
                          event.preventDefault();

                          handleDelete(
                            event,
                            chatId
                          );
                        }
                      }}
                    >
                      <Trash2 size={15} />
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ======================================================
            LIBRARY QUICK ACCESS
        ====================================================== */}

        <div
          className={`sidebar-library-card ${
            currentView === "library" ? "sidebar-library-card-active" : ""
          }`}
          onClick={handleLibrary}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              handleLibrary();
            }
          }}
          title="Open your drug information library"
        >
          <div className="library-card-icon">
            <FileText size={19} />
          </div>

          <div className="library-card-content">
            <div className="library-card-title">
              Your documents
            </div>

            <div className="library-card-text">
              Access your uploaded drug information
            </div>
          </div>

          <button
            type="button"
            className="library-card-button"
            onClick={(event) => {
              event.stopPropagation();
              handleLibrary();
            }}
            aria-label="Open Library"
            title="Open Library"
          >
            <ArrowRight size={16} strokeWidth={2} />
          </button>
        </div>

        {/* ======================================================
            LEGAL & COMPLIANCE
        ====================================================== */}

        <div className="sidebar-legal-links">
          <button
            type="button"
            className="sidebar-legal-btn"
            onClick={onOpenPrivacy}
          >
            Privacy Policy
          </button>
          <span className="sidebar-legal-sep">•</span>
          <button
            type="button"
            className="sidebar-legal-btn"
            onClick={onOpenTerms}
          >
            Terms of Use
          </button>
        </div>

        {/* ======================================================
            USER PROFILE
        ====================================================== */}

        <div className="sidebar-user">
          <div className="user-avatar">
            <UserCircle size={25} />
          </div>

          <div className="user-info">
            <div className="user-name">
              {userName}
            </div>

            <div className="user-email">
              {user?.email || ""}
            </div>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={onLogout}
            title="Logout"
            aria-label="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <ConfirmationModal
        isOpen={deleteTargetId !== null}
        title="Delete Conversation"
        message="Are you sure you want to delete this chat session? This action cannot be undone."
        confirmLabel="Delete Chat"
        cancelLabel="Keep Chat"
        isDanger={true}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTargetId(null)}
      />
    </>
  );
}

export default Sidebar;