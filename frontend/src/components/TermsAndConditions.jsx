import React from "react";

export default function TermsAndConditions({ onClose }) {
  return (
    <div className="legal-page-overlay">
      <div className="legal-page-modal">
        <div className="legal-header">
          <div>
            <h2>Terms and Conditions of Use</h2>
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
            <h3>1. Purpose and Non-Medical Advice Disclaimer</h3>
            <p>
              DrugAssist is an evidence retrieval assistant designed to help healthcare professionals, researchers,
              and clinicians quickly look up, cross-reference, and locate specific sections of manufacturer drug
              prescribing information and package inserts with page citations.
            </p>
            <p className="legal-alert">
              <strong>Clinical Notice:</strong> DrugAssist is NOT a licensed medical practitioner and does NOT provide
              individualized medical advice, clinical diagnoses, or patient-specific treatment recommendations.
              Licensed healthcare providers must exercise independent clinical judgment before prescribing or administering
              medications.
            </p>
          </section>

          <section className="legal-section">
            <h3>2. Medical Emergencies</h3>
            <p>
              Do not use this system for medical emergencies, acute overdoses, or life-threatening reactions.
              In an emergency, immediately dial 911 (or your local emergency emergency number) or contact the
              Poison Control Center at 1-800-222-1222.
            </p>
          </section>

          <section className="legal-section">
            <h3>3. Source Verification and Citation Requirement</h3>
            <p>
              All responses provided by the system include direct page and section references to the source prescribing
              documents loaded in the user library. Users are expected to verify any critical dosage or contraindication
              information against the primary manufacturer packaging or official drug label.
            </p>
          </section>

          <section className="legal-section">
            <h3>4. Acceptable Use Policy</h3>
            <p>Users agree to:</p>
            <ul>
              <li>Upload only legitimate pharmaceutical, regulatory, or research literature.</li>
              <li>Refrain from attempting to reverse-engineer, overwhelm, or inject unauthorized prompts into the system.</li>
              <li>Maintain the confidentiality of individual user credentials and access tokens.</li>
            </ul>
          </section>

          <section className="legal-section">
            <h3>5. Disclaimer of Warranties and Limitation of Liability</h3>
            <p>
              The platform and all retrieved information are provided on an "as is" and "as available" basis without
              warranties of any kind, whether express or implied. DrugAssist and its operators disclaim any liability
              for clinical decisions, diagnostic oversights, or adverse outcomes resulting from reliance on retrieved information.
            </p>
          </section>

          <section className="legal-section">
            <h3>6. Modifications to Terms</h3>
            <p>
              We reserve the right to revise these terms to maintain alignment with regulatory updates and clinical standards.
              Continued use of the platform constitutes acceptance of any modifications.
            </p>
          </section>
        </div>

        <div className="legal-footer">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Accept & Return
          </button>
        </div>
      </div>
    </div>
  );
}
