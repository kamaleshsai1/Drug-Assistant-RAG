import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Copy, Check, ExternalLink } from "lucide-react";

function Message({ message, onOpenCitation }) {
  const isUser = message?.role === "user";
  const [copied, setCopied] = useState(false);

  const sources = Array.isArray(message?.sources)
    ? message.sources
    : [];

  const answer =
    message?.content ||
    message?.answer ||
    "";

  // Pre-process citations like [Source 1, Page 2] into markdown links
  // so ReactMarkdown can render them as interactive buttons.
  const formattedAnswer = useMemo(() => {
    if (!answer) return "";

    // 1. Support multi-citation brackets like [Source 1, Page 2; Source 2, Page 5]
    let text = answer.replace(
      /\[((?:Source\s*\d+[:,\s]+(?:Page|p\.?|pp\.?)[:\s]*\d+[\s;,]*)+)\]/gi,
      (fullMatch, innerText) => {
        return innerText.replace(
          /Source\s*(\d+)[:,\s]+(?:Page|p\.?|pp\.?)[:\s]*(\d+)/gi,
          (m, sId, pNum) => `[Source ${sId}, Page ${pNum}](#citation-source-${sId}-page-${pNum}) `
        ).trim();
      }
    );

    // 2. Support standard and loose single citations like [Source 1, Page 2] or [Source 1: Page 2]
    text = text.replace(
      /\[Source\s*(\d+)[:,\s]+(?:Page|p\.?|pp\.?)[:\s]*(\d+)\]/gi,
      (match, sId, page) => {
        if (match.includes("](#citation-")) return match;
        return `[Source ${sId}, Page ${page}](#citation-source-${sId}-page-${page})`;
      }
    );

    return text;
  }, [answer]);

  const handleCopy = async () => {
    if (!answer) return;
    try {
      await navigator.clipboard.writeText(answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy message:", err);
    }
  };

  const handleCitationClick = (sourceNum, pageNum, sourceObj = null) => {
    if (!onOpenCitation) return;

    const matchedSource =
      sourceObj ||
      sources.find(
        (s, idx) => (s.source_id === sourceNum || idx + 1 === sourceNum) && Number(s.page) === pageNum
      ) ||
      sources[sourceNum - 1] || {
        page: pageNum,
        source: "Prescribing Information",
        document_id: message?.document_id,
        drug: "",
      };

    onOpenCitation({
      documentId: matchedSource.document_id || message?.document_id || "active",
      page: pageNum || Number(matchedSource.page) || 1,
      title: matchedSource.source || matchedSource.drug || "Prescribing Information",
      drug: matchedSource.drug || "",
    });
  };

  return (
    <div
      className={`message-row ${
        isUser
          ? "message-row-user"
          : "message-row-assistant"
      }`}
    >
      {/* Avatar */}
      <div
        className={`message-avatar ${
          isUser
            ? "message-avatar-user"
            : "message-avatar-assistant"
        }`}
      >
        {isUser ? "You" : "DA"}
      </div>

      <div className="message-content">
        {/* Author */}
        <div className="message-author">
          {isUser ? "You" : "DrugAssist"}
        </div>

        {/* USER MESSAGE */}
        {isUser ? (
          <div className="user-message-text">
            {answer}
          </div>
        ) : (
          /* ASSISTANT MESSAGE */
          <>
            <div className="assistant-answer">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children, ...props }) => {
                    if (href && href.startsWith("#citation-source-")) {
                      const match = href.match(/#citation-source-(\d+)-page-(\d+)/);
                      if (match) {
                        const sNum = parseInt(match[1], 10);
                        const pNum = parseInt(match[2], 10);

                        return (
                          <button
                            type="button"
                            className="citation-pill-btn"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleCitationClick(sNum, pNum);
                            }}
                            title={`Jump to Page ${pNum} in PDF`}
                            aria-label={`View Source ${sNum} Page ${pNum} in PDF`}
                          >
                            {children}
                          </button>
                        );
                      }
                    }

                    return (
                      <a
                        {...props}
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {children}
                      </a>
                    );
                  },

                  img: ({ src, alt }) => (
                    <img
                      src={src}
                      alt={alt || ""}
                      loading="lazy"
                    />
                  ),
                }}
              >
                {formattedAnswer}
              </ReactMarkdown>
            </div>

            {/* ================================================= */}
            {/* EVIDENCE */}
            {/* ================================================= */}
            {sources.length > 0 && (
              <section className="sources-section">
                <div className="sources-heading">
                  <FileText size={15} strokeWidth={2} />
                  <span>Evidence</span>
                </div>

                <div className="sources-list">
                  {sources.map((source, index) => (
                    <div
                      className="source-card source-card-interactive"
                      key={`${source.document_id || "doc"}-${source.page}-${index}`}
                      onClick={() =>
                        handleCitationClick(
                          source.source_id || index + 1,
                          Number(source.page) || 1,
                          source
                        )
                      }
                      title={`Click to view Page ${source.page} in PDF`}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          handleCitationClick(
                            source.source_id || index + 1,
                            Number(source.page) || 1,
                            source
                          );
                        }
                      }}
                    >
                      <div className="source-number">
                        {index + 1}
                      </div>

                      <div className="source-details">
                        <div className="source-title">
                          {source.source || "Drug Information"}
                        </div>

                        <div className="source-meta">
                          <span>Source {index + 1}</span>
                          <span className="source-dot">•</span>
                          <span>Page {source.page}</span>
                          {source.drug && (
                            <>
                              <span className="source-dot">•</span>
                              <span>{source.drug}</span>
                            </>
                          )}
                          <span className="source-jump-badge">
                            <ExternalLink size={11} />
                            <span>View Page {source.page}</span>
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <div className="message-actions">
              <button
                type="button"
                className={`message-action-btn ${copied ? "copied" : ""}`}
                onClick={handleCopy}
                title="Copy answer to clipboard"
                aria-label="Copy answer to clipboard"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Message;