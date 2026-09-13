import React, { useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";

function ConfirmationModal({
  isOpen,
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDanger = false,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onCancel?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="modal-backdrop"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
    >
      <div
        className="confirmation-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="confirmation-header">
          <div className={`confirmation-icon ${isDanger ? "danger" : ""}`}>
            <AlertTriangle size={20} strokeWidth={2.2} />
          </div>
          <button
            type="button"
            className="confirmation-close"
            onClick={onCancel}
            aria-label="Close modal"
          >
            <X size={18} />
          </button>
        </div>

        <div className="confirmation-body">
          <h3 id="confirm-modal-title" className="confirmation-title">
            {title}
          </h3>
          <p className="confirmation-message">{message}</p>
        </div>

        <div className="confirmation-actions">
          <button
            type="button"
            className="confirmation-cancel-btn"
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`confirmation-confirm-btn ${isDanger ? "danger" : ""}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmationModal;
