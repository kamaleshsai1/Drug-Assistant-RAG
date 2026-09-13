import React, { useState } from "react";
import { MessageSquare, X, CheckCircle, AlertCircle, Send } from "lucide-react";

function FeedbackModal({ isOpen, onClose }) {
  const [category, setCategory] = useState("feedback");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");

    if (!message.trim()) {
      setError("Please enter your message or question before submitting.");
      return;
    }

    if (message.trim().length < 10) {
      setError("Please provide at least 10 characters so we can understand your feedback.");
      return;
    }

    setLoading(true);
    // Simulate lightweight client submission / local save
    setTimeout(() => {
      setLoading(false);
      setIsSubmitted(true);
      try {
        const feedbackEntries = JSON.parse(
          localStorage.getItem("drugassist_feedback") || "[]"
        );
        feedbackEntries.push({
          category,
          message: message.trim(),
          email: email.trim(),
          date: new Date().toISOString(),
        });
        localStorage.setItem(
          "drugassist_feedback",
          JSON.stringify(feedbackEntries.slice(-20))
        );
      } catch (err) {
        // ignore
      }
    }, 450);
  };

  const handleReset = () => {
    setIsSubmitted(false);
    setMessage("");
    setError("");
    onClose?.();
  };

  return (
    <div
      className="modal-backdrop"
      onClick={handleReset}
      role="dialog"
      aria-modal="true"
      aria-labelledby="feedback-modal-title"
    >
      <div
        className="feedback-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="feedback-header">
          <div className="feedback-header-left">
            <MessageSquare size={18} className="feedback-icon" />
            <h3 id="feedback-modal-title" className="feedback-title">
              Contact & Clinical Feedback
            </h3>
          </div>
          <button
            type="button"
            className="feedback-close-btn"
            onClick={handleReset}
            aria-label="Close feedback modal"
          >
            <X size={18} />
          </button>
        </div>

        {isSubmitted ? (
          <div className="feedback-success-state">
            <div className="feedback-success-icon">
              <CheckCircle size={36} strokeWidth={2.2} />
            </div>
            <h4>Thank you for your feedback</h4>
            <p>
              Your clinical notes and observations help keep DrugAssist's
              retrieval and labeling indexes accurate.
            </p>
            <button
              type="button"
              className="feedback-primary-btn"
              onClick={handleReset}
            >
              Close
            </button>
          </div>
        ) : (
          <form className="feedback-form" onSubmit={handleSubmit}>
            <p className="feedback-desc">
              Have a suggestion, reported issue, or drug monograph inquiry? Let us know.
            </p>

            {error && (
              <div className="feedback-error-state" role="alert">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="feedback-field">
              <label htmlFor="feedback-category">Category</label>
              <select
                id="feedback-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="feedback-select"
              >
                <option value="feedback">General Clinical Feedback</option>
                <option value="drug_request">Drug Monograph Request</option>
                <option value="citation_issue">Citation / Labeling Correction</option>
                <option value="technical">Technical Issue / Bug</option>
              </select>
            </div>

            <div className="feedback-field">
              <label htmlFor="feedback-email">
                Your Email <span className="feedback-optional">(Optional)</span>
              </label>
              <input
                id="feedback-email"
                type="email"
                placeholder="clinician@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="feedback-input"
              />
            </div>

            <div className="feedback-field">
              <label htmlFor="feedback-message">Details</label>
              <textarea
                id="feedback-message"
                rows={4}
                placeholder="Describe your suggestion or observation..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className={`feedback-textarea ${error ? "has-error" : ""}`}
              />
            </div>

            <div className="feedback-actions">
              <button
                type="button"
                className="feedback-cancel-btn"
                onClick={handleReset}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="feedback-submit-btn"
                disabled={loading}
              >
                <Send size={15} />
                <span>{loading ? "Sending..." : "Submit Feedback"}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default FeedbackModal;
