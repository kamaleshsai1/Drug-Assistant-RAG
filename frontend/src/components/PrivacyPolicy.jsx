import React from "react";

export default function PrivacyPolicy({ onClose }) {
  return (
    <div className="legal-page-overlay">
      <div className="legal-page-modal">
        <div className="legal-header">
          <div>
            <h2>Privacy Policy</h2>
            <p className="legal-date">Effective Date: September 2026</p>
          </div>
          <button
            type="button"
            className="legal-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="legal-content">
          <section className="legal-section">
            <h3>1. Scope and Application</h3>
            <p>
              This Privacy Policy describes how the DrugAssist platform collects,
              uses, processes, and protects user information when utilizing our
              prescribing information search and retrieval services.
            </p>
          </section>

          <section className="legal-section">
            <h3>2. Information We Collect</h3>
            <p>We collect only the information required to provide accurate document retrieval:</p>
            <ul>
              <li><strong>Account Credentials:</strong> User email address and securely salted bcrypt password hashes.</li>
              <li><strong>Prescribing Documents:</strong> Official manufacturer package inserts and drug monographs uploaded by authorized users.</li>
              <li><strong>Session and Query Data:</strong> Questions asked within conversation threads to maintain contextual continuity and retrieve relevant document chunks.</li>
            </ul>
          </section>

          <section className="legal-section">
            <h3>3. Health Information and HIPAA Compliance</h3>
            <p>
              DrugAssist is designed strictly for official drug labeling and pharmaceutical documentation.
              We do not solicit, collect, or store Protected Health Information (PHI) as defined under the
              Health Insurance Portability and Accountability Act (HIPAA). Users must not upload individual
              patient medical records or identifiable clinical notes.
            </p>
          </section>

          <section className="legal-section">
            <h3>4. Document Processing and Vector Storage</h3>
            <p>
              Uploaded PDF prescribing information documents are parsed locally into structured sections
              and indexed in isolated vector database namespaces. Document text is used exclusively to provide
              page-accurate citations and evidence-backed answers.
            </p>
          </section>

          <section className="legal-section">
            <h3>5. Data Retention and Deletion</h3>
            <p>
              Users maintain full ownership over their workspace. Any uploaded document, chat thread, or user
              profile can be permanently deleted directly through the application interface or by contacting
              the system administrator.
            </p>
          </section>

          <section className="legal-section">
            <h3>6. Security Measures</h3>
            <p>
              All communications between client and server are transmitted over encrypted TLS connections.
              API authentication tokens employ cryptographically signed JWT tokens with 24-hour expiration windows.
            </p>
          </section>

          <section className="legal-section">
            <h3>7. Contact and Inquiries</h3>
            <p>
              For security disclosures or privacy inquiries, contact the DrugAssist engineering and compliance
              team at <code>compliance@drugassist.internal</code>.
            </p>
          </section>
        </div>

        <div className="legal-footer">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Back to Application
          </button>
        </div>
      </div>
    </div>
  );
}
