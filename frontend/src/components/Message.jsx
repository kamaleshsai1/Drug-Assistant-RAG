import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  User,
  Pill,
  Video,
  ExternalLink
} from "lucide-react";

function Message({ message, onOpenSource }) {
  const isUser = message?.role === "user";

  const answer =
    message?.content ||
    message?.answer ||
    "";

  const sources = Array.isArray(message?.sources)
    ? message.sources
    : [];

  const videos = Array.isArray(message?.videos)
    ? message.videos
    : [];

  const evidence = Array.isArray(message?.evidence)
    ? message.evidence
    : [];

  // =========================================================
  // SOURCE HELPERS
  // =========================================================

  const getDocumentId = (source) => {
    if (!source) return null;

    return (
      source.database_document_id ??
      source.document_id_db ??
      source.databaseDocumentId ??
      source.documentId ??
      null
    );
  };

  const getPageNumber = (source, fallback = 1) => {
    if (!source) return fallback;

    const page =
      source.page ??
      source.page_number ??
      source.pageNumber ??
      fallback;

    const parsed = Number(page);

    if (
      Number.isFinite(parsed) &&
      parsed > 0
    ) {
      return Math.floor(parsed);
    }

    return fallback;
  };

  const getFilename = (source) => {
    if (!source) {
      return "Drug Information";
    }

    return (
      source.filename ||
      source.file_name ||
      source.source ||
      source.document_name ||
      source.documentName ||
      "Drug Information"
    );
  };

  const getSourceByNumber = (number) => {
    const index = Number(number) - 1;

    if (
      !Number.isInteger(index) ||
      index < 0 ||
      index >= sources.length
    ) {
      return null;
    }

    return sources[index];
  };

  // =========================================================
  // OPEN CITATION
  // =========================================================

  const handleCitationClick = (
    event,
    sourceNumber,
    pageNumber
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (!onOpenSource) {
      console.warn(
        "onOpenSource is not available."
      );
      return;
    }

    const source =
      getSourceByNumber(sourceNumber);

    if (!source) {
      console.warn(
        "Source not found:",
        sourceNumber,
        sources
      );
      return;
    }

    const documentId =
      getDocumentId(source);

    if (!documentId) {
      console.warn(
        "Database document ID missing:",
        source
      );
      return;
    }

    const page =
      Number(pageNumber) > 0
        ? Math.floor(Number(pageNumber))
        : getPageNumber(source);

    const filename =
      getFilename(source);

    console.log(
      "Opening citation:",
      {
        documentId,
        page,
        filename
      }
    );

    onOpenSource(
      documentId,
      page,
      filename
    );
  };

  // =========================================================
  // PREPARE CITATIONS
  // =========================================================
  //
  // Converts:
  //
  // Source 1, Page 1
  //
  // OR
  //
  // [Source 1, Page 1]
  //
  // into a special Markdown link.
  //
  // ReactMarkdown will then pass that link to
  // the custom "a" renderer below.
  //
  // =========================================================

  const prepareAnswer = (text) => {
  if (!text) return "";

  if (typeof text !== "string") {
    return text;
  }

  return text.replace(
    /\[?\s*Source\s+(\d+)\s*,\s*Page\s+(\d+)\s*\]?/gi,
    (match, sourceNumber, pageNumber) => {
      return `[Source ${sourceNumber}, Page ${pageNumber}](#drugassist-source-${sourceNumber}-page-${pageNumber})`;
    }
  );
};
  

  // =========================================================
  // MARKDOWN COMPONENTS
  // =========================================================

  const markdownComponents = {
    // -------------------------------------------------------
    // LINKS
    // -------------------------------------------------------

    a: ({
      href,
      children,
      ...props
    }) => {
      const citationMatch =
        href?.match(
          /^#drugassist-source-(\d+)-page-(\d+)$/
        );

      // -----------------------------------------------------
      // CITATION LINK
      // -----------------------------------------------------

      if (citationMatch) {
        const sourceNumber =
          Number(citationMatch[1]);

        const pageNumber =
          Number(citationMatch[2]);

        const source =
          getSourceByNumber(sourceNumber);

        const documentId =
          getDocumentId(source);

        return (
          <button
            type="button"
            className="citation-inline-button"
            disabled={!documentId}
            title={
              documentId
                ? `Open ${getFilename(
                    source
                  )} — Page ${pageNumber}`
                : "Source unavailable"
            }
            onClick={(event) =>
              handleCitationClick(
                event,
                sourceNumber,
                pageNumber
              )
            }
          >
            Source {sourceNumber}, Page {pageNumber}
          </button>
        );
      }

      // -----------------------------------------------------
      // NORMAL EXTERNAL LINK
      // -----------------------------------------------------

      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          {...props}
        >
          {children}
        </a>
      );
    },

    // -------------------------------------------------------
    // PARAGRAPH
    // -------------------------------------------------------

    p: ({ children }) => (
      <p className="message-paragraph">
        {children}
      </p>
    ),

    // -------------------------------------------------------
    // LISTS
    // -------------------------------------------------------

    ul: ({ children }) => (
      <ul className="message-list">
        {children}
      </ul>
    ),

    ol: ({ children }) => (
      <ol className="message-list">
        {children}
      </ol>
    ),

    li: ({ children }) => (
      <li className="message-list-item">
        {children}
      </li>
    ),

    // -------------------------------------------------------
    // HEADINGS
    // -------------------------------------------------------

    h1: ({ children }) => (
      <h1 className="message-heading">
        {children}
      </h1>
    ),

    h2: ({ children }) => (
      <h2 className="message-heading">
        {children}
      </h2>
    ),

    h3: ({ children }) => (
      <h3 className="message-heading">
        {children}
      </h3>
    ),

    // -------------------------------------------------------
    // CODE
    // -------------------------------------------------------

    code: ({
      inline,
      children,
      ...props
    }) => {
      if (inline) {
        return (
          <code
            className="message-inline-code"
            {...props}
          >
            {children}
          </code>
        );
      }

      return (
        <pre className="message-code-block">
          <code {...props}>
            {children}
          </code>
        </pre>
      );
    },

    // -------------------------------------------------------
    // BLOCKQUOTE
    // -------------------------------------------------------

    blockquote: ({
      children
    }) => (
      <blockquote className="message-blockquote">
        {children}
      </blockquote>
    ),

    // -------------------------------------------------------
    // TABLE
    // -------------------------------------------------------

    table: ({ children }) => (
      <div className="message-table-wrapper">
        <table className="message-table">
          {children}
        </table>
      </div>
    )
  };

  // =========================================================
  // RENDER
  // =========================================================

  return (
    <div
      className={
        isUser
          ? "message-row user-row"
          : "message-row assistant-row"
      }
    >
      {/* =====================================================
          AVATAR
      ====================================================== */}

      <div
        className={
          isUser
            ? "message-avatar user-avatar"
            : "message-avatar assistant-avatar"
        }
      >
        {isUser ? (
          <User
            size={17}
            strokeWidth={2}
          />
        ) : (
          <Pill
            size={17}
            strokeWidth={2}
          />
        )}
      </div>

      {/* =====================================================
          MESSAGE
      ====================================================== */}

      <div
        className={
          isUser
            ? "message-bubble user-bubble"
            : "message-bubble assistant-bubble"
        }
      >
        {/* ===================================================
            ANSWER
        ==================================================== */}

        <div className="message-content">
          <ReactMarkdown
            remarkPlugins={[
              remarkGfm
            ]}
            components={
              markdownComponents
            }
          >
            {prepareAnswer(answer)}
          </ReactMarkdown>
        </div>

        {/* ===================================================
            EVIDENCE
        ==================================================== */}

        {!isUser &&
          evidence.length > 0 && (
            <div className="evidence-section">
              {evidence.map(
                (item, index) => (
                  <div
                    key={
                      item?.id ||
                      `evidence-${index}`
                    }
                    className="evidence-item"
                  >
                    {typeof item ===
                    "string"
                      ? item
                      : item?.text ||
                        item?.content ||
                        JSON.stringify(
                          item
                        )}
                  </div>
                )
              )}
            </div>
          )}

        {/* ===================================================
            VIDEOS
        ==================================================== */}

        {!isUser &&
          videos.length > 0 && (
            <div className="videos-section">
              <div className="videos-heading">
                <Video size={15} />

                <span>
                  Related Videos
                </span>
              </div>

              <div className="videos-list">
                {videos.map(
                  (video, index) => {
                    const url =
                      video?.url ||
                      video?.link ||
                      video?.video_url;

                    const title =
                      video?.title ||
                      video?.name ||
                      `Video ${index + 1}`;

                    if (!url) {
                      return null;
                    }

                    return (
                      <a
                        key={
                          video?.id ||
                          `${url}-${index}`
                        }
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="video-link"
                      >
                        <Video
                          size={15}
                        />

                        <span>
                          {title}
                        </span>

                        <ExternalLink
                          size={13}
                        />
                      </a>
                    );
                  }
                )}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}

export default Message;