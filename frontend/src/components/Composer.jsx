import { useEffect, useRef, useState } from "react";
import {
  FileText,
  X,
  ArrowUp,
} from "lucide-react";

function Composer({
  onSend,
  loading = false,
  disabled = false,
}) {
  const textareaRef = useRef(null);
  const pdfInputRef = useRef(null);

  const [attachments, setAttachments] = useState([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [hasText, setHasText] = useState(false);

  const isDisabled = loading || disabled;

  // ============================================================
  // TEXTAREA
  // ============================================================

  const handleInput = (event) => {
    const value = event.currentTarget.value;

    setHasText(value.trim().length > 0);

    event.currentTarget.style.height = "auto";

    const height = Math.min(
      Math.max(event.currentTarget.scrollHeight, 58),
      150
    );

    event.currentTarget.style.height = `${height}px`;
  };

  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSend = async () => {
    if (isDisabled) {
      return;
    }

    const textarea = textareaRef.current;

    if (!textarea) {
      return;
    }

    const question = textarea.value.trim();

    if (
      !question &&
      attachments.length === 0
    ) {
      return;
    }

    const files = attachments.map(
      (item) => item.file
    );

    // Clear composer after capturing the values.
    textarea.value = "";
    textarea.style.height = "58px";

    setHasText(false);
    setMenuOpen(false);

    // Remove previews safely.
    attachments.forEach((item) => {
      if (item.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
      }
    });

    setAttachments([]);

    try {
      await onSend(question, files);
    } catch (error) {
      console.error(
        "COMPOSER SEND ERROR:",
        error
      );
    }

    // Return focus to the input.
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  };

  // ============================================================
  // KEYBOARD
  // ============================================================

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      handleSend();
    }
  };

  // ============================================================
  // ADD FILES
  // ============================================================

  const addFiles = (fileList) => {
    const files = Array.from(fileList || []);

    if (files.length === 0) {
      return;
    }

    const newAttachments = [];

    for (const file of files) {
      const name = file.name.toLowerCase();

      const isPDF =
        file.type === "application/pdf" ||
        name.endsWith(".pdf");

      if (!isPDF) {
        alert(
          `${file.name} is not supported. Please upload a PDF file.`
        );
        continue;
      }

      if (file.size > 15 * 1024 * 1024) {
        alert(
          `${file.name} is larger than 15 MB.`
        );
        continue;
      }

      newAttachments.push({
        file,
        name: file.name,
        type: "pdf",
        previewUrl: null,
      });
    }

    if (newAttachments.length > 0) {
      setAttachments((previous) => [
        ...previous,
        ...newAttachments,
      ]);
    }

    setMenuOpen(false);

    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  };

  // ============================================================
  // PDF
  // ============================================================

  const handlePDFChange = (event) => {
    addFiles(event.target.files);
    event.target.value = "";
  };

  // ============================================================
  // REMOVE FILE
  // ============================================================

  const removeAttachment = (index) => {
    setAttachments((previous) => {
      const item = previous[index];

      if (item?.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
      }

      return previous.filter(
        (_, itemIndex) =>
          itemIndex !== index
      );
    });
  };

  // ============================================================
  // CLEANUP
  // ============================================================

  useEffect(() => {
    return () => {
      attachments.forEach((item) => {
        if (item.previewUrl) {
          URL.revokeObjectURL(item.previewUrl);
        }
      });
    };
  }, []);

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="drugassist-composer-root">

      {/* ========================================================
          ATTACHMENT MENU
      ======================================================== */}

      {menuOpen && (
        <div className="drugassist-attach-menu">

          <button
            type="button"
            onClick={() =>
              pdfInputRef.current?.click()
            }
          >
            <FileText size={17} />
            <span>Upload PDF</span>
          </button>

      {/* ========================================================
          HIDDEN FILE INPUTS
      ======================================================== */}

      <input
        ref={pdfInputRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple
        onChange={handlePDFChange}
        style={{
          display: "none",
        }}
      />

      {/* ========================================================
          COMPOSER
      ======================================================== */}

      <div className="drugassist-composer">

        {/* ======================================================
            ATTACHMENTS
        ====================================================== */}

        {attachments.length > 0 && (
          <div className="drugassist-attachments">

            {attachments.map(
              (attachment, index) => (
                <div
                  className="drugassist-attachment"
                  key={`${attachment.name}-${index}`}
                >

                  <div className="drugassist-file-preview">

                    {attachment.type ===
                      "image" &&
                    attachment.previewUrl ? (
                      <img
                        src={
                          attachment.previewUrl
                        }
                        alt={
                          attachment.name
                        }
                      />
                    ) : (
                      <FileText
                        size={22}
                      />
                    )}

                  </div>

                  <div className="drugassist-file-info">

                    <div
                      className="drugassist-file-name"
                      title={
                        attachment.name
                      }
                    >
                      {attachment.name}
                    </div>

                    <div className="drugassist-file-type">
                      PDF • Ready to send
                    </div>

                  </div>

                  <button
                    type="button"
                    className="drugassist-remove"
                    onClick={() =>
                      removeAttachment(
                        index
                      )
                    }
                    title="Remove attachment"
                    aria-label="Remove attachment"
                  >
                    <X size={15} />
                  </button>

                </div>
              )
            )}

          </div>
        )}

        {/* ======================================================
            INPUT ROW
        ====================================================== */}

        <div className="drugassist-input-row">

          {/* ====================================================
              ATTACH BUTTON
          ==================================================== */}

          <button
            type="button"
            className="drugassist-plus"
            onClick={() =>
              pdfInputRef.current?.click()
            }
            disabled={isDisabled}
            title="Attach Medication PDF"
            aria-label="Attach Medication PDF"
          >
            +
          </button>

        </div>

        {/* ======================================================
            TEXTAREA
        ====================================================== */}

        <textarea
          ref={textareaRef}
          className="drugassist-textarea"
          defaultValue=""
          placeholder="Ask about a medicine, dosage, side effects..."
          rows={1}
          disabled={isDisabled}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
        />

        {/* ======================================================
            TOOLBAR
        ====================================================== */}

        <div className="drugassist-toolbar">

          <button
            type="button"
            className="drugassist-plus"
            onClick={() =>
              setMenuOpen(
                (previous) => !previous
              )
            }
            disabled={isDisabled}
            title="Attach PDF or image"
            aria-label="Attach PDF or image"
          >
            +
          </button>

          <div className="drugassist-toolbar-space" />

          <button
            type="button"
            className={
              "drugassist-send " +
              (
                !hasText &&
                attachments.length === 0
                  ? "drugassist-send-disabled"
                  : ""
              )
            }
            onClick={handleSend}
            disabled={
              isDisabled ||
              (
                !hasText &&
                attachments.length === 0
              )
            }
            title="Send"
            aria-label="Send"
          >
            <ArrowUp
              size={19}
              strokeWidth={2.3}
            />
          </button>

        </div>

      </div>

      {/* ========================================================
          HINT
      ======================================================== */}

      <div className="drugassist-hint">
        Press Enter to send • Shift + Enter for a new line
      </div>

      {/* ========================================================
          STYLES
      ======================================================== */}

      <style>{`

        .drugassist-composer-root {
          position: absolute;
          left: 50%;
          bottom: 17px;
          transform: translateX(-50%);
          width: min(1080px, calc(100% - 48px));
          z-index: 100;
        }

        .drugassist-composer {
          width: 100%;
          box-sizing: border-box;
          background: #ffffff;
          border: 1px solid #cfd0d4;
          border-radius: 21px;
          overflow: hidden;
          box-shadow:
            0 4px 18px rgba(0, 0, 0, 0.06),
            0 1px 3px rgba(0, 0, 0, 0.04);
        }

        .drugassist-composer:focus-within {
          border-color: #aeb0b5;
          box-shadow:
            0 5px 20px rgba(0, 0, 0, 0.07);
        }

        .drugassist-textarea {
          display: block;
          width: 100%;
          min-height: 58px;
          max-height: 150px;
          box-sizing: border-box;
          resize: none;
          border: 0;
          outline: 0;
          background: #ffffff;
          color: #171717 !important;
          caret-color: #171717;
          padding: 14px 16px 7px;
          font-family: inherit;
          font-size: 16px;
          line-height: 1.45;
          overflow-y: auto;
        }

        .drugassist-textarea::placeholder {
          color: #9aa0aa !important;
          opacity: 1;
        }

        .drugassist-textarea:disabled {
          opacity: 0.6;
          cursor: default;
        }

        .drugassist-toolbar {
          height: 47px;
          display: flex;
          align-items: center;
          padding: 3px 9px 8px;
          box-sizing: border-box;
        }

        .drugassist-toolbar-space {
          flex: 1;
        }

        .drugassist-plus {
          width: 38px;
          height: 38px;
          border: 0;
          border-radius: 10px;
          background: #f0f0f2;
          color: #55565b;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 27px;
          font-weight: 300;
          line-height: 1;
          cursor: pointer;
        }

        .drugassist-plus:hover:not(:disabled) {
          background: #e5e5e7;
          color: #222;
        }

        .drugassist-plus:disabled {
          opacity: 0.5;
          cursor: default;
        }

        .drugassist-send {
          width: 38px;
          height: 38px;
          border: 0;
          border-radius: 10px;
          margin-left: 6px;
          background: #171717;
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .drugassist-send:hover:not(:disabled) {
          background: #303030;
        }

        .drugassist-send:disabled,
        .drugassist-send-disabled {
          background: #dfe1e5;
          color: #9da1a8;
          cursor: default;
        }

        .drugassist-attachments {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 10px 12px 2px;
        }

        .drugassist-attachment {
          display: flex;
          align-items: center;
          gap: 9px;
          max-width: 300px;
          min-width: 190px;
          padding: 7px 9px;
          border: 1px solid #e1e2e5;
          border-radius: 11px;
          background: #f8f8f9;
        }

        .drugassist-file-preview {
          width: 40px;
          height: 40px;
          flex-shrink: 0;
          border-radius: 8px;
          background: #eeeeef;
          color: #55565b;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        .drugassist-file-preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .drugassist-file-info {
          min-width: 0;
          flex: 1;
        }

        .drugassist-file-name {
          font-size: 12px;
          font-weight: 600;
          color: #25272c;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .drugassist-file-type {
          margin-top: 3px;
          font-size: 10px;
          color: #9497a0;
        }

        .drugassist-remove {
          width: 27px;
          height: 27px;
          flex-shrink: 0;
          border: 0;
          border-radius: 50%;
          background: transparent;
          color: #777980;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .drugassist-remove:hover:not(:disabled) {
          background: #e7e7e9;
          color: #222;
        }

        .drugassist-attach-menu {
          position: absolute;
          left: 0;
          bottom: calc(100% + 9px);
          width: 190px;
          padding: 6px;
          background: #ffffff;
          border: 1px solid #dedfe2;
          border-radius: 13px;
          box-shadow:
            0 12px 35px rgba(0, 0, 0, 0.12),
            0 2px 6px rgba(0, 0, 0, 0.05);
          z-index: 200;
        }

        .drugassist-attach-menu button {
          width: 100%;
          height: 40px;
          border: 0;
          border-radius: 9px;
          background: transparent;
          color: #25272c;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 11px;
          font-size: 13px;
          cursor: pointer;
          text-align: left;
        }

        .drugassist-attach-menu button:hover {
          background: #f2f2f3;
        }

        .drugassist-hint {
          text-align: center;
          margin-top: 8px;
          font-size: 11px;
          color: #a0a3aa;
        }

        @media (max-width: 800px) {
          .drugassist-composer-root {
            width: calc(100% - 24px);
            bottom: 9px;
          }

          .drugassist-hint {
            display: none;
          }
        }

        @media (max-width: 500px) {
          .drugassist-composer {
            border-radius: 18px;
          }

          .drugassist-attachment {
            min-width: 0;
            width: 100%;
            max-width: 100%;
          }
        }

      `}</style>

    </div>
  );
}

export default Composer;