import React, { useEffect, useState } from "react";
import {
  ArrowLeft,
  FileText,
  Trash2,
  MessageCircle,
  ExternalLink,
  Search,
  Loader2,
  RefreshCw
} from "lucide-react";

function Library({
  apiUrl,
  token,
  onBack,
  onSelectDocument,
  onOpenDocument,
  selectedDocumentId
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState("");

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(`${apiUrl}/documents`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      if (!response.ok) {
        throw new Error(
          "Unable to load your PDF library."
        );
      }

      const data = await response.json();

      const docs = Array.isArray(data)
        ? data
        : data.documents || data.items || [];

      setDocuments(docs);
    } catch (err) {
      console.error("LIBRARY LOAD ERROR:", err);
      setError(
        err.message || "Unable to load your PDF library."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      loadDocuments();
    }
  }, [token]);

  const handleDelete = async (event, document) => {
    event.stopPropagation();

    if (!document?.id) return;

    const filename =
      document.filename ||
      document.file_name ||
      document.name ||
      "this document";

    const confirmed = window.confirm(
      `Delete "${filename}"?`
    );

    if (!confirmed) return;

    try {
      setDeletingId(document.id);

      const response = await fetch(
        `${apiUrl}/documents/${document.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 401) {
        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      if (!response.ok) {
        let message =
          "Unable to delete the document.";

        try {
          const data = await response.json();
          message =
            data.detail ||
            data.message ||
            message;
        } catch {
          // Ignore invalid JSON
        }

        throw new Error(message);
      }

      setDocuments((previous) =>
        previous.filter(
          (item) =>
            Number(item.id) !==
            Number(document.id)
        )
      );
    } catch (err) {
      console.error(
        "LIBRARY DELETE ERROR:",
        err
      );

      alert(
        err.message ||
          "Unable to delete document."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const handleOpenPDF = (
    event,
    document
  ) => {
    event.stopPropagation();

    if (!document?.id) {
      console.error(
        "Cannot open PDF: missing document ID."
      );
      return;
    }

    if (onOpenDocument) {
      onOpenDocument(document, 1);
    }
  };

  const handleAskQuestions = (
    event,
    document
  ) => {
    event.stopPropagation();

    if (!document) return;

    if (onSelectDocument) {
      onSelectDocument(document);
    }
  };

  const handleCardClick = (document) => {
    if (!document) return;

    if (onOpenDocument) {
      onOpenDocument(document, 1);
    }
  };

  const filteredDocuments =
    documents.filter((document) => {
      const filename =
        document.filename ||
        document.file_name ||
        document.name ||
        "";

      const drug =
        document.drug_name ||
        document.drug ||
        "";

      const source =
        document.source ||
        "";

      const searchText =
        `${filename} ${drug} ${source}`
          .toLowerCase();

      return searchText.includes(
        String(searchTerm).toLowerCase()
      );
    });

  return (
    <div className="library-page">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="library-header">

        <div className="library-header-left">

          <button
            type="button"
            className="library-back-button"
            onClick={onBack}
            title="Back to Chat"
          >
            <ArrowLeft size={18} />
          </button>

          <div className="library-header-icon">
            <FileText size={20} />
          </div>

          <div>
            <h1>PDF Library</h1>
            <p>
              Your trusted medical documents
            </p>
          </div>

        </div>

        <button
          type="button"
          className="library-refresh-button"
          onClick={loadDocuments}
          disabled={loading}
          title="Refresh library"
        >
          <RefreshCw
            size={17}
            className={
              loading
                ? "library-refresh-spinning"
                : ""
            }
          />
        </button>

      </div>

      {/* =====================================================
          SEARCH
      ===================================================== */}

      <div className="library-search-wrapper">

        <Search size={18} />

        <input
          type="text"
          placeholder="Search your PDFs..."
          value={searchTerm}
          onChange={(event) =>
            setSearchTerm(event.target.value)
          }
        />

      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}

      <div className="library-content">

        {/* Loading */}

        {loading && (
          <div className="library-state">
            <Loader2
              size={28}
              className="library-refresh-spinning"
            />

            <span>
              Loading your PDF library...
            </span>
          </div>
        )}

        {/* Error */}

        {!loading && error && (
          <div className="library-state">

            <span className="library-error">
              {error}
            </span>

            <button
              type="button"
              className="library-retry-button"
              onClick={loadDocuments}
            >
              Try Again
            </button>

          </div>
        )}

        {/* Empty */}

        {!loading &&
          !error &&
          filteredDocuments.length === 0 && (
            <div className="library-empty">

              <div className="library-empty-icon">
                <FileText size={34} />
              </div>

              <h2>
                {searchTerm
                  ? "No matching PDFs"
                  : "No PDFs in your library"}
              </h2>

              <p>
                {searchTerm
                  ? "Try a different search term."
                  : "Upload a trusted medical PDF to start using the library."}
              </p>

              {!searchTerm && (
                <button
                  type="button"
                  className="library-back-to-chat"
                  onClick={onBack}
                >
                  Back to Chat
                </button>
              )}

            </div>
          )}

        {/* Results */}

        {!loading &&
          !error &&
          filteredDocuments.length > 0 && (
            <>
              <div className="library-results-header">
                {filteredDocuments.length}{" "}
                {filteredDocuments.length === 1
                  ? "document"
                  : "documents"}
              </div>

              <div className="document-grid">

                {filteredDocuments.map(
                  (document) => {

                    const documentId =
                      document.id;

                    const filename =
                      document.filename ||
                      document.file_name ||
                      document.name ||
                      "Medical Document";

                    const drugName =
                      document.drug_name ||
                      document.drug ||
                      document.drugName ||
                      "";

                    const source =
                      document.source ||
                      document.source_name ||
                      document.sourceName ||
                      "";

                    const isSelected =
                      Number(
                        selectedDocumentId
                      ) ===
                      Number(documentId);

                    const isDeleting =
                      Number(deletingId) ===
                      Number(documentId);

                    return (
                      <div
                        key={documentId}
                        className={`document-card ${
                          isSelected
                            ? "document-card-active"
                            : ""
                        }`}
                        onClick={() =>
                          handleCardClick(
                            document
                          )
                        }
                      >

                        {/* =================================================
                            TOP
                        ================================================= */}

                        <div className="document-card-top">

                          <div className="document-icon">
                            <FileText size={23} />
                          </div>

                          <div className="document-card-actions">

                            {isSelected && (
                              <span className="document-active-badge">
                                Selected
                              </span>
                            )}

                            <button
                              type="button"
                              className="document-delete"
                              title="Delete PDF"
                              disabled={
                                isDeleting
                              }
                              onClick={(event) =>
                                handleDelete(
                                  event,
                                  document
                                )
                              }
                            >
                              {isDeleting ? (
                                <Loader2
                                  size={16}
                                  className="library-refresh-spinning"
                                />
                              ) : (
                                <Trash2
                                  size={16}
                                />
                              )}
                            </button>

                          </div>

                        </div>

                        {/* =================================================
                            DOCUMENT INFO
                        ================================================= */}

                        <h3
                          className="document-name"
                          title={filename}
                        >
                          {filename}
                        </h3>

                        {drugName && (
                          <div className="document-drug">
                            {drugName}
                          </div>
                        )}

                        {source && (
                          <div
                            className="document-source"
                            title={source}
                          >
                            {source}
                          </div>
                        )}

                        {/* =================================================
                            META
                        ================================================= */}

                        <div className="document-meta">

                          {document.pages && (
                            <span>
                              {document.pages} pages
                            </span>
                          )}

                          {document.file_type && (
                            <span>
                              {String(
                                document.file_type
                              ).toUpperCase()}
                            </span>
                          )}

                          {!document.pages &&
                            !document.file_type && (
                              <span>
                                Medical PDF
                              </span>
                            )}

                        </div>

                        {document.created_at && (
                          <div className="document-date">
                            Added{" "}
                            {new Date(
                              document.created_at
                            ).toLocaleDateString()}
                          </div>
                        )}

                        {/* =================================================
                            OPEN PDF BUTTON
                        ================================================= */}

                        <button
                          type="button"
                          className="document-chat-btn"
                          onClick={(event) =>
                            handleOpenPDF(
                              event,
                              document
                            )
                          }
                        >
                          <ExternalLink
                            size={15}
                          />

                          <span>
                            Open PDF
                          </span>
                        </button>

                        {/* =================================================
                            ASK QUESTIONS BUTTON
                        ================================================= */}

                        <button
                          type="button"
                          className="document-chat-btn"
                          onClick={(event) =>
                            handleAskQuestions(
                              event,
                              document
                            )
                          }
                        >
                          <MessageCircle
                            size={15}
                          />

                          <span>
                            Ask Questions
                          </span>
                        </button>

                      </div>
                    );
                  }
                )}

              </div>
            </>
          )}

      </div>

    </div>
  );
}

export default Library;