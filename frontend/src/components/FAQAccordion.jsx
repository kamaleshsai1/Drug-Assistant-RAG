import React, { useState } from "react";
import { ChevronDown, HelpCircle } from "lucide-react";

const FAQ_DATA = [
  {
    id: "faq-sources",
    question: "What sources does DrugAssist use for drug information?",
    answer:
      "DrugAssist references official manufacturer Prescribing Information documents (package inserts), highlights of prescribing information, boxed warnings, and clinical labeling literature.",
  },
  {
    id: "faq-citations",
    question: "How do bracket citations like [Source 1, Page 9] work?",
    answer:
      "Citations indicate the exact source document and page number in the uploaded prescribing information where the dosage, indication, or warning is documented. You can cross-reference the evidence cards displayed directly below each response.",
  },
  {
    id: "faq-upload",
    question: "Can I upload my own drug prescribing information PDFs?",
    answer:
      "Yes. Use the paperclip attachment icon or the Library tab to upload official drug prescribing PDFs. The system will automatically index its clinical sections and allow you to ask targeted questions about that medicine.",
  },
  {
    id: "faq-medical-advice",
    question: "Does DrugAssist provide personalized medical diagnosis or prescriptions?",
    answer:
      "No. DrugAssist is strictly a reference tool. It does not replace professional clinical judgment or provide personal medical advice. Always consult a licensed physician or pharmacist for medical decisions.",
  },
];

function FAQAccordion() {
  const [openId, setOpenId] = useState(null);

  const toggle = (id) => {
    setOpenId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="faq-section">
      <div className="faq-header">
        <div className="faq-title-wrap">
          <HelpCircle size={18} className="faq-icon" />
          <h3 className="faq-title">Frequently Asked Questions</h3>
        </div>
      </div>

      <div className="faq-list">
        {FAQ_DATA.map((item) => {
          const isOpen = openId === item.id;
          return (
            <div
              key={item.id}
              className={`faq-item ${isOpen ? "open" : ""}`}
            >
              <button
                type="button"
                className="faq-question-btn"
                onClick={() => toggle(item.id)}
                aria-expanded={isOpen}
                aria-controls={`faq-answer-${item.id}`}
              >
                <span>{item.question}</span>
                <ChevronDown
                  size={16}
                  className={`faq-arrow ${isOpen ? "rotated" : ""}`}
                />
              </button>
              {isOpen && (
                <div
                  id={`faq-answer-${item.id}`}
                  className="faq-answer-panel"
                >
                  <p>{item.answer}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default FAQAccordion;
