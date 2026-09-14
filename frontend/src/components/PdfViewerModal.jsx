import React, { useState, useEffect } from "react";
import {
  X,
  ExternalLink,
  Download,
  FileText,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  RefreshCw,
} from "lucide-react";

function PdfViewerModal({
  isOpen,
  onClose,
  apiUrl,
  documentId,
  initialPage = 1,
  title = "Prescribing Information",
  drug = "",
}) {
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const [iframeKey, setIframeKey] = useState(0);

  useEffect(() => {
    setCurrentPage(initialPage || 1);
    setIframeKey((prev) => prev + 1);
  }, [initialPage, documentId]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  if (!isOpen || !documentId) {
    return null;
  }

  const encodedDocId = encodeURIComponent(documentId);
  const pdfUrl = `${apiUrl}/documents/${encodedDocId}/pdf#page=${currentPage}`;

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
    }
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => prev + 1);
  };

  const handleOpenNewTab = () => {
    window.open(pdfUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="pdf-modal-overlay" onClick={onClose}>
      <div
        className="pdf-modal-container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="pdf-modal-title"
      >
        {/* ================= HEADER ================= */}
        <header className="pdf-modal-header">
          <div className="pdf-modal-header-left">
            <div className="pdf-modal-icon">
              <FileText size={18} />
            </div>
            <div className="pdf-modal-title-box">
              <h2 id="pdf-modal-title" className="pdf-modal-title">
                {title || "Prescribing Information"}
              </h2>
              {drug && <span className="pdf-modal-drug-tag">{drug}</span>}
            </div>
          </div>

          <div className="pdf-modal-header-actions">
            {/* Page Navigator */}
            <div className="pdf-page-controls">
              <button
                type="button"
                className="pdf-ctrl-btn"
                onClick={handlePrevPage}
                disabled={currentPage <= 1}
                title="Previous Page"
                aria-label="Previous Page"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="pdf-page-indicator">
                Page <strong>{currentPage}</strong>
              </span>
              <button
                type="button"
                className="pdf-ctrl-btn"
                onClick={handleNextPage}
                title="Next Page"
                aria-label="Next Page"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            {/* Open in new tab button */}
            <button
              type="button"
              className="pdf-header-btn pdf-btn-primary"
              onClick={handleOpenNewTab}
              title="Open PDF at this exact page in a new tab"
              aria-label="Open PDF in new tab"
            >
              <ExternalLink size={14} />
              <span>Open in New Tab</span>
            </button>

            {/* Close button */}
            <button
              type="button"
              className="pdf-header-btn pdf-close-btn"
              onClick={onClose}
              title="Close viewer (Esc)"
              aria-label="Close viewer"
            >
              <X size={18} />
            </button>
          </div>
        </header>

        {/* ================= PDF BODY ================= */}
        <div className="pdf-modal-body">
          <iframe
            key={`${documentId}-${currentPage}-${iframeKey}`}
            src={pdfUrl}
            className="pdf-iframe"
            title={`${title} - Page ${currentPage}`}
          />

          <div className="pdf-fallback-footer">
            <span>
              Viewing <strong>{title}</strong> at <strong>Page {currentPage}</strong>.
            </span>
            <button
              type="button"
              className="pdf-fallback-link"
              onClick={handleOpenNewTab}
            >
              Click here to open directly in a new tab with native browser controls ↗
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PdfViewerModal;
