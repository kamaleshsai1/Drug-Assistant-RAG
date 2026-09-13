import {
  useEffect,
  useRef,
  useState
} from "react";

import { createPortal } from "react-dom";

import {
  Plus,
  Paperclip,
  Image as ImageIcon,
  Mic,
  ArrowUp,
  X,
  FileText
} from "lucide-react";


function ChatInput({
  value,
  onChange,
  onSend,
  onVoice,
  onFileUpload,
  pendingImage,
  pendingImagePreview,
  onRemoveImage,
  loading,
  selectedDocumentName,
  onChangeDocument,
  onClearDocument,
  isRecording = false,
  voiceStatus = ""
}) {

  // ============================================================
  // REFS
  // ============================================================

  const pdfInputRef = useRef(null);

  const imageInputRef = useRef(null);

  const textareaRef = useRef(null);

  const attachButtonRef = useRef(null);

  const menuRef = useRef(null);


  // ============================================================
  // STATE
  // ============================================================

  const [
    attachmentMenuOpen,
    setAttachmentMenuOpen
  ] = useState(false);

  const [
    menuPosition,
    setMenuPosition
  ] = useState({
    left: 20,
    bottom: 100
  });


  // ============================================================
  // UPDATE MENU POSITION
  // ============================================================

  const updateMenuPosition = () => {

    const button =
      attachButtonRef.current;

    if (!button) {
      return;
    }

    const rect =
      button.getBoundingClientRect();

    const menuWidth = 190;

    const viewportPadding = 12;

    let left = rect.left;

    if (
      left + menuWidth >
      window.innerWidth - viewportPadding
    ) {

      left =
        window.innerWidth -
        menuWidth -
        viewportPadding;

    }

    if (left < viewportPadding) {
      left = viewportPadding;
    }

    const bottom =
      window.innerHeight -
      rect.top +
      8;

    setMenuPosition({
      left,
      bottom
    });
  };


  // ============================================================
  // OPEN / CLOSE MENU
  // ============================================================

  const toggleAttachmentMenu = () => {

    if (loading) {
      return;
    }

    setAttachmentMenuOpen(
      (previous) => !previous
    );

  };


  // ============================================================
  // POSITION MENU WHEN OPEN
  // ============================================================

  useEffect(() => {

    if (!attachmentMenuOpen) {
      return;
    }

    updateMenuPosition();

    const handleResize = () => {
      updateMenuPosition();
    };

    const handleScroll = () => {
      updateMenuPosition();
    };

    window.addEventListener(
      "resize",
      handleResize
    );

    window.addEventListener(
      "scroll",
      handleScroll,
      true
    );

    return () => {

      window.removeEventListener(
        "resize",
        handleResize
      );

      window.removeEventListener(
        "scroll",
        handleScroll,
        true
      );

    };

  }, [attachmentMenuOpen]);


  // ============================================================
  // CLOSE MENU ON OUTSIDE CLICK
  // ============================================================

  useEffect(() => {

    if (!attachmentMenuOpen) {
      return;
    }

    const handleOutsideClick = (event) => {

      const menu =
        menuRef.current;

      const button =
        attachButtonRef.current;

      if (
        menu &&
        menu.contains(event.target)
      ) {
        return;
      }

      if (
        button &&
        button.contains(event.target)
      ) {
        return;
      }

      setAttachmentMenuOpen(false);
    };


    const handleEscape = (event) => {

      if (event.key === "Escape") {
        setAttachmentMenuOpen(false);
      }

    };


    document.addEventListener(
      "mousedown",
      handleOutsideClick
    );

    document.addEventListener(
      "keydown",
      handleEscape
    );


    return () => {

      document.removeEventListener(
        "mousedown",
        handleOutsideClick
      );

      document.removeEventListener(
        "keydown",
        handleEscape
      );

    };

  }, [attachmentMenuOpen]);


  // ============================================================
  // CLOSE MENU WHILE LOADING
  // ============================================================

  useEffect(() => {

    if (loading) {
      setAttachmentMenuOpen(false);
    }

  }, [loading]);


  // ============================================================
  // KEYBOARD SEND
  // ============================================================

  const handleKeyDown = (event) => {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      onSend();

    }

  };


  // ============================================================
  // PDF SELECTION
  // ============================================================

  const handlePdfChange = (event) => {

    const file =
      event.target.files?.[0];

    if (file) {

      onFileUpload(
        file,
        false
      );

    }

    event.target.value = "";

    setAttachmentMenuOpen(false);

  };


  // ============================================================
  // IMAGE SELECTION
  // ============================================================

  const handleImageChange = (event) => {

    const file =
      event.target.files?.[0];

    if (file) {

      onFileUpload(
        file,
        true
      );

      requestAnimationFrame(() => {

        textareaRef.current?.focus();

      });

    }

    event.target.value = "";

    setAttachmentMenuOpen(false);

  };


  // ============================================================
  // ATTACHMENT MENU
  // ============================================================

  const attachmentMenu = attachmentMenuOpen
    ? createPortal(

        <div
          ref={menuRef}
          className="drugassist-attachment-menu"
          style={{
            position: "fixed",
            left: `${menuPosition.left}px`,
            bottom: `${menuPosition.bottom}px`
          }}
        >

          <button
            type="button"
            onClick={() => {

              setAttachmentMenuOpen(false);

              setTimeout(() => {

                pdfInputRef.current?.click();

              }, 0);

            }}
          >

            <Paperclip
              size={18}
              strokeWidth={1.9}
            />

            <span>
              Attach PDF
            </span>

          </button>


          <button
            type="button"
            onClick={() => {

              setAttachmentMenuOpen(false);

              setTimeout(() => {

                imageInputRef.current?.click();

              }, 0);

            }}
          >

            <ImageIcon
              size={18}
              strokeWidth={1.9}
            />

            <span>
              Add image
            </span>

          </button>

        </div>,

        document.body

      )
    : null;


  // ============================================================
  // RENDER
  // ============================================================

  return (
    <>

      <style>{`

        /* ======================================================
           COMPOSER
        ====================================================== */

        .composer-shell {
          position: absolute;
          left: 50%;
          bottom: 18px;
          transform: translateX(-50%);
          width: min(860px, calc(100% - 48px));
          z-index: 1000;
          display: flex;
          flex-direction: column;
          gap: 8px;
          pointer-events: none;
        }

        .composer-shell > * {
          pointer-events: auto;
        }

        .aura-selected-document {
          width: 100%;
          box-sizing: border-box;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 8px 14px;
          border: 1px solid var(--border);
          border-radius: 12px;
          background: var(--surface);
          color: var(--text-secondary);
          font-size: 13px;
          box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
          backdrop-filter: blur(8px);
        }

        [data-theme="dark"] .aura-selected-document {
          box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
        }

        .aura-selected-document-left {
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 0;
          flex: 1;
        }

        .aura-selected-document-icon {
          color: var(--accent);
          flex-shrink: 0;
        }

        .aura-selected-document-text {
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--text-secondary);
        }

        .aura-selected-document-text strong {
          color: var(--text);
          font-weight: 600;
        }

        .aura-selected-document-actions {
          display: flex;
          align-items: center;
          gap: 8px;
          flex-shrink: 0;
        }

        .aura-change-document {
          padding: 4px 10px;
          border-radius: 6px;
          border: 1px solid var(--border);
          background: var(--surface-soft);
          color: var(--text);
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.15s ease;
          white-space: nowrap;
        }

        .aura-change-document:hover {
          background: var(--surface-hover);
          border-color: var(--border-strong);
        }

        .aura-clear-document {
          width: 22px;
          height: 22px;
          border: 0;
          border-radius: 6px;
          background: transparent;
          color: var(--text-muted);
          font-size: 18px;
          line-height: 1;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s ease;
        }

        .aura-clear-document:hover {
          background: var(--surface-hover);
          color: var(--text);
        }


        .composer-box {
          position: relative;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 22px;
          box-shadow:
            0 8px 28px rgba(0,0,0,0.08);
          overflow: visible;
          padding: 10px 12px 9px;
        }


        /* ======================================================
           ATTACHMENT PREVIEW
        ====================================================== */

        .composer-attachment {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 7px 8px 11px 4px;
        }


        .composer-attachment-preview {
          width: 58px;
          height: 58px;
          flex: 0 0 58px;
          border-radius: 11px;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--surface-soft);
          color: var(--text-muted);
        }


        .composer-attachment-preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          display: block;
        }


        .composer-attachment-info {
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }


        .composer-attachment-info strong {
          font-size: 14px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: var(--text);
        }


        .composer-attachment-info span {
          font-size: 13px;
          color: var(--text-muted);
        }


        .composer-remove {
          margin-left: auto;
          width: 34px;
          height: 34px;
          border: 0;
          border-radius: 50%;
          background: transparent;
          color: var(--text-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }


        .composer-remove:hover {
          background: var(--surface-hover);
          color: var(--text);
        }


        /* ======================================================
           TEXTAREA
        ====================================================== */

        .composer-box textarea {
          width: 100%;
          min-height: 52px;
          max-height: 150px;
          resize: none;
          border: 0;
          outline: 0;
          background: transparent;
          padding: 8px 8px 4px;
          box-sizing: border-box;
          font: inherit;
          font-size: 17px;
          line-height: 1.45;
          color: var(--text);
        }


        .composer-box textarea::placeholder {
          color: var(--text-muted);
          opacity: 1;
        }


        /* ======================================================
           TOOLBAR
        ====================================================== */

        .composer-toolbar {
          height: 42px;
          display: flex;
          align-items: center;
          gap: 4px;
        }


        .composer-toolbar-spacer {
          flex: 1;
        }


        .composer-icon-button {
          width: 40px;
          height: 40px;
          padding: 0;
          border: 0;
          background: transparent;
          color: var(--text);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }


        .composer-icon-button:hover:not(:disabled) {
          background: var(--surface-hover);
        }


        .composer-icon-button:disabled {
          cursor: default;
          opacity: 0.55;
        }

        .composer-icon-button.voice-button.recording {
          background: rgba(239, 68, 68, 0.15) !important;
          color: #dc2626 !important;
          animation: voicePulse 1.2s infinite ease-in-out;
        }

        @keyframes voicePulse {
          0% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.45);
            transform: scale(1);
          }
          50% {
            box-shadow: 0 0 0 7px rgba(239, 68, 68, 0);
            transform: scale(1.08);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
            transform: scale(1);
          }
        }

        .composer-listening-bar {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          margin-bottom: 8px;
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.22);
          border-radius: 12px;
          font-size: 13px;
          font-weight: 500;
          color: #dc2626;
        }

        .composer-listening-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #dc2626;
          box-shadow: 0 0 6px #dc2626;
          animation: dotBlink 1s infinite alternate;
        }

        @keyframes dotBlink {
          from { opacity: 1; transform: scale(1); }
          to { opacity: 0.3; transform: scale(0.7); }
        }


        /* ======================================================
           PLUS ICON
        ====================================================== */

        .composer-plus-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
        }


        .composer-plus-icon svg {
          display: block;
        }


        /* ======================================================
           SEND
        ====================================================== */

        .composer-send-button {
          width: 42px;
          height: 42px;
          padding: 0;
          border: 0;
          border-radius: 50%;
          background: #0284c7;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          margin-left: 3px;
        }


        .composer-send-button.inactive {
          background: var(--surface-hover);
          color: var(--text-muted);
          cursor: default;
        }


        /* ======================================================
           ATTACHMENT MENU

           Rendered into document.body using a React portal.
           This prevents the menu from being clipped by the
           chat scrolling container or transformed composer.
        ====================================================== */

        .drugassist-attachment-menu {
          width: 190px;
          box-sizing: border-box;
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 14px;
          box-shadow:
            0 12px 32px rgba(0,0,0,0.25),
            0 2px 8px rgba(0,0,0,0.06);
          padding: 6px;
          z-index: 2147483647;
          animation: drugassistAttachmentMenuIn 0.12s ease-out;
        }


        @keyframes drugassistAttachmentMenuIn {

          from {
            opacity: 0;
            transform: translateY(5px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }

        }


        .drugassist-attachment-menu button {
          width: 100%;
          min-height: 42px;
          box-sizing: border-box;
          border: 0;
          background: transparent;
          border-radius: 9px;
          padding: 10px 11px;
          display: flex;
          align-items: center;
          gap: 11px;
          text-align: left;
          color: var(--text);
          cursor: pointer;
          font-size: 14px;
          font-family: inherit;
        }


        .drugassist-attachment-menu button:hover {
          background: var(--surface-hover);
        }


        .drugassist-attachment-menu button:active {
          background: var(--surface-soft);
        }


        .drugassist-attachment-menu button svg {
          flex: 0 0 auto;
          color: var(--text-secondary);
        }


        .drugassist-attachment-menu button span {
          flex: 1;
        }


        /* ======================================================
           HINT
        ====================================================== */

        .composer-hint {
          text-align: center;
          font-size: 12px;
          color: #9aa0aa;
          margin-top: 10px;
        }


        /* ======================================================
           MOBILE
        ====================================================== */

        @media (max-width: 700px) {

          .composer-shell {
            width: calc(100% - 24px);
            bottom: 10px;
          }


          .composer-attachment-info span {
            display: none;
          }


          .drugassist-attachment-menu {
            width: 180px;
          }

        }

      `}</style>


      {/* ========================================================
          COMPOSER
      ======================================================== */}

      <div className="composer-shell">


        {/* ======================================================
            HIDDEN PDF INPUT
        ====================================================== */}

        <input
          ref={pdfInputRef}
          type="file"
          accept="application/pdf,.pdf"
          onChange={handlePdfChange}
          style={{
            display: "none"
          }}
        />


        {/* ======================================================
            HIDDEN IMAGE INPUT
        ====================================================== */}

        <input
          ref={imageInputRef}
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          style={{
            display: "none"
          }}
        />


        {/* ======================================================
            ACTIVE DOCUMENT BANNER (Cleanly stacked above composer box)
        ====================================================== */}
        {selectedDocumentName && (
          <div
            className="aura-selected-document"
            title="Questions will be answered specifically using this document."
          >
            <div className="aura-selected-document-left">
              <FileText size={15} className="aura-selected-document-icon" />
              <span className="aura-selected-document-text">
                <strong>PDF Active:</strong> {selectedDocumentName}
              </span>
            </div>

            <div className="aura-selected-document-actions">
              <button
                type="button"
                className="aura-change-document"
                onClick={onChangeDocument}
                title="Change document in Library"
              >
                Change
              </button>

              <button
                type="button"
                className="aura-clear-document"
                onClick={onClearDocument}
                title="Clear selection (search all drug information)"
                aria-label="Clear document selection"
              >
                ×
              </button>
            </div>
          </div>
        )}


        {/* ======================================================
            COMPOSER BOX
        ====================================================== */}

        <div className="composer-box">

          {/* ====================================================
              VOICE LISTENING STATUS
          ==================================================== */}
          {isRecording && (
            <div className="composer-listening-bar">
              <span className="composer-listening-dot" />
              <span>{voiceStatus || "Listening... speak now"}</span>
            </div>
          )}


          {/* ====================================================
              PENDING IMAGE
          ==================================================== */}

          {pendingImage && (

            <div className="composer-attachment">

              <div className="composer-attachment-preview">

                {pendingImagePreview ? (

                  <img
                    src={pendingImagePreview}
                    alt="Selected image"
                  />

                ) : (

                  <ImageIcon size={22} />

                )}

              </div>


              <div className="composer-attachment-info">

                <strong>
                  {pendingImage.name}
                </strong>

                <span>
                  Type your question below, then press Send.
                </span>

              </div>


              <button
                type="button"
                className="composer-remove"
                onClick={onRemoveImage}
                disabled={loading}
                title="Remove image"
                aria-label="Remove image"
              >

                <X size={18} />

              </button>

            </div>

          )}


          {/* ====================================================
              TEXTAREA
          ==================================================== */}

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) =>
              onChange(event.target.value)
            }
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            disabled={loading}
            rows={1}
            aria-label="Ask anything"
          />


          {/* ====================================================
              TOOLBAR
          ==================================================== */}

          <div className="composer-toolbar">


            {/* ==================================================
                PLUS BUTTON
            ================================================== */}

            <button
              ref={attachButtonRef}
              type="button"
              className="composer-icon-button"
              onClick={toggleAttachmentMenu}
              disabled={loading}
              title="Attach PDF or image"
              aria-label="Attach PDF or image"
              aria-expanded={
                attachmentMenuOpen
              }
            >

              <span className="composer-plus-icon">

                <Plus
                  size={25}
                  strokeWidth={1.7}
                />

              </span>

            </button>


            <div className="composer-toolbar-spacer" />


            {/* ==================================================
                VOICE
            ================================================== */}

            <button
              type="button"
              className={
                `composer-icon-button voice-button ${
                  isRecording ? "recording" : ""
                } ${
                  loading
                    ? "disabled"
                    : ""
                }`
              }
              onClick={onVoice}
              disabled={loading}
              title={isRecording ? "Stop listening" : "Voice input"}
              aria-label={isRecording ? "Stop listening" : "Voice input"}
            >

              <Mic
                size={22}
                strokeWidth={isRecording ? 2.4 : 1.9}
              />

            </button>


            {/* ==================================================
                SEND
            ================================================== */}

            <button
              type="button"
              className={
                `composer-send-button ${
                  !value.trim() || loading
                    ? "inactive"
                    : ""
                }`
              }
              onClick={onSend}
              disabled={
                !value.trim() ||
                loading
              }
              title="Send"
              aria-label="Send"
            >

              <ArrowUp
                size={24}
                strokeWidth={2.2}
              />

            </button>

          </div>

        </div>


        {/* ======================================================
            HINT
        ====================================================== */}

        <div className="composer-hint">
          DrugAssist can search the web, read documents,
          analyze images and more.
        </div>

      </div>


      {/* ========================================================
          PORTAL ATTACHMENT MENU
      ======================================================== */}

      {attachmentMenu}

    </>
  );
}


export default ChatInput;