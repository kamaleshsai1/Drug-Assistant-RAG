import { useEffect, useRef, useState } from "react";

import {
  Sun,
  Moon,
  Menu,
  Pill,
  FileText,
  ArrowUp,
  X
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import AuthPage from "./components/AuthPage";
import Library from "./components/Library";
import PrivacyPolicy from "./components/PrivacyPolicy";
import TermsAndConditions from "./components/TermsAndConditions";
import FAQAccordion from "./components/FAQAccordion";

import {
  askAURA,
  getDocuments,
  uploadPDF,
  getConversations,
  getConversation,
  deleteConversation,
  deleteAllConversations,
  deletePDF,
  askImage,
  voiceAsk,
  getDocumentPDF,
  getCurrentUser,
  clearAuth
} from "./services/api";


const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


function App() {

  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem("aura_token") || localStorage.getItem("token"))
  );

  const [user, setUser] = useState(() => {
    try {
      const storedUser = localStorage.getItem("aura_user");
      return storedUser ? JSON.parse(storedUser) : null;
    } catch {
      return null;
    }
  });

  const isAuthError = (err) => {
    const msg = String(err?.message || "").toLowerCase();
    // Do NOT treat server cold-starts, gateway errors, or network errors as auth errors
    if (
      msg.includes("failed to fetch") ||
      msg.includes("network error") ||
      msg.includes("load failed") ||
      msg.includes("502") ||
      msg.includes("503") ||
      msg.includes("504") ||
      msg.includes("bad gateway") ||
      msg.includes("gateway timeout")
    ) {
      return false;
    }

    return (
      msg.includes("session expired") ||
      msg.includes("jwt expired") ||
      msg.includes("token has expired") ||
      msg.includes("signature has expired") ||
      msg.includes("invalid authentication token") ||
      msg.includes("could not validate credentials")
    );
  };

  // Verify session with server on startup
  useEffect(() => {
    const token =
      localStorage.getItem("aura_token") ||
      localStorage.getItem("token");

    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      return;
    }

    getCurrentUser()
      .then((userData) => {
        const currentUser = userData?.user || userData;
        if (currentUser?.id || currentUser?.email) {
          setUser(currentUser);
          setIsAuthenticated(true);
          localStorage.setItem(
            "aura_user",
            JSON.stringify(currentUser)
          );
        }
      })
      .catch((err) => {
        if (isAuthError(err)) {
          console.warn("Stored session is invalid, resetting:", err);
          handleLogout();
        } else {
          console.warn("Backend server may be waking up or offline; retaining cached session:", err);
        }
      });
  }, []);


  // ============================================================
  // GENERAL UI
  // ============================================================

  const [currentView, setCurrentView] = useState("chat");
  const [mobileOpen, setMobileOpen] = useState(false);

  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("drugassist_theme") || "light";
  });


  // ============================================================
  // CHAT
  // ============================================================

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);


  // ============================================================
  // CONVERSATIONS
  // ============================================================

  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] =
    useState(null);

  const [loadingConversation, setLoadingConversation] =
    useState(false);


  // ============================================================
  // DOCUMENTS
  // ============================================================

  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  const [selectedDocumentId, setSelectedDocumentId] =
    useState(null);

  const [selectedDocumentName, setSelectedDocumentName] =
    useState("");


  // ============================================================
  // PDF VIEWER
  // ============================================================

  const [pdfViewer, setPdfViewer] = useState({
    open: false,
    url: "",
    page: 1,
    filename: ""
  });

  const [pdfLoading, setPdfLoading] = useState(false);


  // ============================================================
  // IMAGE
  // ============================================================

  const [pendingImage, setPendingImage] = useState(null);
  const [pendingImagePreview, setPendingImagePreview] =
    useState("");


  // ============================================================
  // VOICE
  // ============================================================

  const [isRecording, setIsRecording] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const speechRecognitionRef = useRef(null);


  // ============================================================
  // SCROLL
  // ============================================================

  const chatAreaRef = useRef(null);

  const [scrollProgress, setScrollProgress] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);


  // ============================================================
  // THEME
  // ============================================================

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      theme
    );

    localStorage.setItem(
      "drugassist_theme",
      theme
    );
  }, [theme]);


  const toggleTheme = () => {
    setTheme((previous) =>
      previous === "light"
        ? "dark"
        : "light"
    );
  };


  // ============================================================
  // SCROLL TRACKING
  // ============================================================

  useEffect(() => {

    const element = chatAreaRef.current;

    if (!element) return;

    const handleScroll = () => {

      const {
        scrollTop,
        scrollHeight,
        clientHeight
      } = element;

      const total =
        scrollHeight - clientHeight;

      const progress =
        total > 0
          ? Math.min(
              100,
              Math.max(
                0,
                (scrollTop / total) * 100
              )
            )
          : 0;

      setScrollProgress(progress);

      setShowScrollTop(
        scrollTop > 260
      );
    };


    element.addEventListener(
      "scroll",
      handleScroll,
      { passive: true }
    );


    return () => {
      element.removeEventListener(
        "scroll",
        handleScroll
      );
    };

  }, [currentView, messages.length]);


  const handleScrollToTop = () => {

    if (!chatAreaRef.current) return;

    chatAreaRef.current.scrollTo({
      top: 0,
      behavior: "smooth"
    });
  };


  // ============================================================
  // AUTO SCROLL
  // ============================================================

  useEffect(() => {

    if (!chatAreaRef.current) return;

    const timer = setTimeout(() => {

      chatAreaRef.current.scrollTo({
        top: chatAreaRef.current.scrollHeight,
        behavior: "smooth"
      });

    }, 50);

    return () => clearTimeout(timer);

  }, [
    messages,
    loading,
    voiceStatus
  ]);


  // ============================================================
  // LOAD DATA
  // ============================================================

  useEffect(() => {

    if (!isAuthenticated) return;

    loadConversations();
    loadDocuments();

  }, [isAuthenticated]);


  // ============================================================
  // LOAD CONVERSATIONS
  // ============================================================

  const loadConversations = async () => {

    try {

      const data =
        await getConversations();

      const list =
        Array.isArray(data)
          ? data
          : Array.isArray(data?.conversations)
          ? data.conversations
          : Array.isArray(data?.chats)
          ? data.chats
          : [];

      setConversations(list);

    } catch (error) {

      console.error(
        "CONVERSATIONS ERROR:",
        error
      );

      if (isAuthError(error)) {
        handleLogout();
      }
    }
  };


  // ============================================================
  // LOAD DOCUMENTS
  // ============================================================

  const loadDocuments = async () => {

    try {

      const data =
        await getDocuments();

      const documents =
        Array.isArray(data?.documents)
          ? data.documents
          : [];

      setUploadedDocuments(
        documents
      );

      setUploadedFiles(
        documents.map(
          (document) =>
            document.filename
        )
      );

      if (selectedDocumentId !== null) {

        const selected =
          documents.find(
            (document) =>
              Number(document.id) ===
              Number(selectedDocumentId)
          );

        if (selected) {

          setSelectedDocumentName(
            selected.filename || ""
          );

        } else {

          setSelectedDocumentId(null);
          setSelectedDocumentName("");
        }
      }

    } catch (error) {

      console.error(
        "DOCUMENT ERROR:",
        error
      );

      if (isAuthError(error)) {
        handleLogout();
      }
    }
  };


  // ============================================================
  // OPEN CONVERSATION
  // ============================================================

  const handleOpenConversation = async (
    conversationId
  ) => {

    if (
      !conversationId ||
      loadingConversation
    ) {
      return;
    }

    try {

      setLoadingConversation(true);

      setCurrentConversationId(
        conversationId
      );

      const data =
        await getConversation(
          conversationId
        );

      const conversationMessages =
        Array.isArray(data?.messages)
          ? data.messages
          : [];

      const loadedMessages =
        conversationMessages
          .filter(
            (item) =>
              item &&
              item.role &&
              item.content !== undefined
          )
          .map((item) => ({
            id:
              item.id ||
              `message-${Date.now()}-${Math.random()}`,

            role: item.role,

            content: item.content,

            sources:
              item.sources || [],

            videos:
              item.videos || [],

            attachments:
              item.attachments || [],

            evidence:
              item.evidence || [],

            confidence:
              item.confidence,

            grounding_score:
              item.grounding_score,

            mode:
              item.mode,

            image_analysis:
              item.image_analysis
          }));

      setMessages(
        loadedMessages
      );

      setInput("");

      setPendingImage(null);
      setPendingImagePreview("");

      setCurrentView("chat");

    } catch (error) {

      console.error(
        "OPEN CONVERSATION ERROR:",
        error
      );

      if (isAuthError(error)) {
        handleLogout();
        return;
      }

      setMessages([
        {
          id:
            `conversation-error-${Date.now()}`,

          role: "assistant",

          content:
            error.message ||
            "Unable to open this conversation."
        }
      ]);

    } finally {

      setLoadingConversation(false);
    }
  };


  // ============================================================
  // SELECT DOCUMENT FOR RAG
  // ============================================================

  const handleSelectDocument = (
    documentOrId
  ) => {

    let selected = null;


    if (
      typeof documentOrId === "object" &&
      documentOrId !== null
    ) {

      selected = documentOrId;

    } else {

      selected =
        uploadedDocuments.find(
          (document) =>
            Number(document.id) ===
            Number(documentOrId)
        );
    }


    if (!selected) {

      console.warn(
        "Selected document not found:",
        documentOrId
      );

      return;
    }


    setSelectedDocumentId(
      selected.id
    );

    setSelectedDocumentName(
      selected.filename ||
      "Selected document"
    );


    setUploadedDocuments(
      (previous) => {

        const alreadyExists =
          previous.some(
            (document) =>
              Number(document.id) ===
              Number(selected.id)
          );

        if (alreadyExists) {
          return previous;
        }

        return [
          ...previous,
          selected
        ];
      }
    );


    setCurrentView("chat");
    setInput("");
  };


  // ============================================================
// OPEN PDF FROM CITATION
// ============================================================

const handleOpenSource = async (
  documentId,
  page = 1,
  filename = "Drug Information"
) => {
  console.log("====================================");
  console.log("PDF CITATION CLICKED");
  console.log("Document ID:", documentId);
  console.log("Requested Page:", page);
  console.log("Filename:", filename);
  console.log("====================================");

  if (!documentId) {
    console.error(
      "PDF OPEN ERROR: Missing database document ID."
    );

    alert(
      "This citation does not have a valid PDF document ID."
    );

    return;
  }

  const token =
    localStorage.getItem("aura_token");

  if (!token) {
    console.error(
      "PDF OPEN ERROR: Authentication token missing."
    );

    handleLogout();
    return;
  }

  setPdfLoading(true);

  try {
    const pdfUrl =
      `${API_BASE_URL}/documents/${documentId}/pdf`;

    console.log(
      "Fetching PDF:",
      pdfUrl
    );

    const response = await fetch(
      pdfUrl,
      {
        method: "GET",
        headers: {
          Authorization:
            `Bearer ${token}`
        }
      }
    );

    console.log(
      "PDF response status:",
      response.status
    );

    console.log(
      "PDF content type:",
      response.headers.get(
        "content-type"
      )
    );

    if (!response.ok) {
      let errorMessage =
        `Unable to open PDF (${response.status})`;

      try {
        const errorData =
          await response.json();

        errorMessage =
          errorData.detail ||
          errorData.message ||
          errorMessage;
      } catch {
        // Response was not JSON.
      }

      throw new Error(errorMessage);
    }

    const blob =
      await response.blob();

    console.log(
      "PDF blob type:",
      blob.type
    );

    console.log(
      "PDF blob size:",
      blob.size
    );

    if (
      blob.type !==
      "application/pdf"
    ) {
      throw new Error(
        "The server did not return a PDF file."
      );
    }

    if (blob.size === 0) {
      throw new Error(
        "The PDF file is empty."
      );
    }

    const objectUrl =
      URL.createObjectURL(blob);

    const requestedPage =
      Math.max(
        1,
        Math.floor(
          Number(page) || 1
        )
      );

    console.log(
      "PDF object URL created:",
      objectUrl
    );

    console.log(
      "Opening PDF on page:",
      requestedPage
    );

    setPdfViewer({
      open: true,
      url: objectUrl,
      page: requestedPage,
      filename:
        filename ||
        "Drug Information"
    });

  } catch (error) {
    console.error(
      "PDF OPEN ERROR:",
      error
    );

    alert(
      error.message ||
      "Unable to open the requested PDF."
    );

  } finally {
    setPdfLoading(false);
  }
};

  // ============================================================
  // OPEN PDF FROM LIBRARY
  // ============================================================

  const handleOpenDocument = (
    document,
    page = 1
  ) => {

    if (!document) return;


    handleOpenSource(
      document.id,
      page,
      document.filename ||
      document.source ||
      "Drug Information"
    );
  };


  // ============================================================
  // CLOSE PDF VIEWER
  // ============================================================

  const handleClosePdfViewer = () => {

    setPdfViewer(
      (previous) => {

        if (previous.url) {

          URL.revokeObjectURL(
            previous.url
          );
        }


        return {
          open: false,
          url: "",
          page: 1,
          filename: ""
        };
      }
    );
  };


  // ============================================================
  // PDF CLEANUP
  // ============================================================

  useEffect(() => {

    return () => {

      if (pdfViewer.url) {

        URL.revokeObjectURL(
          pdfViewer.url
        );
      }
    };

  }, [pdfViewer.url]);


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = (authData) => {

    const token =
      authData?.access_token ||
      authData?.token ||
      localStorage.getItem(
        "aura_token"
      ) ||
      localStorage.getItem(
        "token"
      );


    if (!token) {

      console.error(
        "Login completed but token was not found."
      );

      return;
    }

    localStorage.setItem(
      "aura_token",
      token
    );
    localStorage.setItem(
      "token",
      token
    );


    try {

      if (authData?.user) {
        setUser(authData.user);
        localStorage.setItem(
          "aura_user",
          JSON.stringify(authData.user)
        );
      } else {
        const storedUser =
          localStorage.getItem(
            "aura_user"
          );

        setUser(
          storedUser
            ? JSON.parse(storedUser)
            : null
        );
      }

    } catch {

      setUser(null);
    }


    setIsAuthenticated(true);

    setCurrentView("chat");

    setMessages([]);

    setInput("");
  };


  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {

    clearAuth();
    localStorage.removeItem(
      "aura_token"
    );
    localStorage.removeItem(
      "token"
    );
    localStorage.removeItem(
      "aura_user"
    );


    setIsAuthenticated(false);

    setUser(null);

    setCurrentView("chat");

    setMessages([]);

    setInput("");

    setUploadedFiles([]);

    setUploadedDocuments([]);

    setSelectedDocumentId(null);

    setSelectedDocumentName("");

    setPendingImage(null);

    setPendingImagePreview("");

    setIsRecording(false);

    setVoiceStatus("");


    if (speechRecognitionRef.current) {

      try {
        speechRecognitionRef.current.stop();
      } catch {}

      speechRecognitionRef.current =
        null;
    }


    if (mediaRecorderRef.current) {

      try {

        if (
          mediaRecorderRef.current.state !==
          "inactive"
        ) {
          mediaRecorderRef.current.stop();
        }

      } catch {}

      mediaRecorderRef.current =
        null;
    }


    if (streamRef.current) {

      streamRef.current
        .getTracks()
        .forEach(
          (track) =>
            track.stop()
        );

      streamRef.current = null;
    }
  };


  // ============================================================
  // NEW CHAT
  // ============================================================

  const handleNewChat = () => {

    setCurrentConversationId(null);

    setMessages([]);

    setInput("");

    setSelectedDocumentId(null);

    setSelectedDocumentName("");

    setPendingImage(null);

    setPendingImagePreview("");

    setCurrentView("chat");
  };


  // ============================================================
  // LIBRARY
  // ============================================================

  const handleOpenLibrary = () => {
    setCurrentView("library");
  };


  const handleOpenChat = () => {
    setCurrentView("chat");
  };


  // ============================================================
  // DELETE DOCUMENT
  // ============================================================

  const handleDeleteDocument = async (
    documentId
  ) => {

    try {

      await deletePDF(
        documentId
      );


      if (
        Number(selectedDocumentId) ===
        Number(documentId)
      ) {

        setSelectedDocumentId(null);

        setSelectedDocumentName("");
      }


      await loadDocuments();

    } catch (error) {

      console.error(
        "DELETE PDF ERROR:",
        error
      );


      if (isAuthError(error)) {
        handleLogout();
      }
    }
  };


  // ============================================================
  // DELETE CURRENT CHAT
  // ============================================================

  const handleDeleteChat = async () => {

    if (!currentConversationId) {

      handleNewChat();
      return;
    }


    try {

      await deleteConversation(
        currentConversationId
      );


      setConversations(
        (previous) =>
          previous.filter(
            (conversation) =>
              conversation.id !==
              currentConversationId
          )
      );


      handleNewChat();

    } catch (error) {

      console.error(
        "DELETE CHAT ERROR:",
        error
      );


      if (isAuthError(error)) {
        handleLogout();
      }
    }
  };


  // ============================================================
  // DELETE ALL CHATS
  // ============================================================

  const handleDeleteAllConversations =
    async () => {

      try {

        await deleteAllConversations();

        setConversations([]);

        handleNewChat();

      } catch (error) {

        console.error(
          "DELETE ALL CHATS ERROR:",
          error
        );


        if (isAuthError(error)) {
          handleLogout();
        }
      }
    };


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSend = async () => {

    const text =
      input.trim();


    if (
      !text ||
      loading
    ) {
      return;
    }


    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();
      return;
    }


    const imageToSend =
      pendingImage;


    const userMessage = {
      id:
        `user-${Date.now()}`,

      role: "user",

      content: text
    };


    setMessages(
      (previous) => [
        ...previous,
        userMessage
      ]
    );


    setInput("");

    setPendingImage(null);

    setPendingImagePreview("");

    setLoading(true);


    try {

      let data;


      // --------------------------------------------------------
      // IMAGE QUESTION
      // --------------------------------------------------------

      if (imageToSend) {

        data =
          await askImage(
            text,
            imageToSend.file,
            currentConversationId
          );

      }

      // --------------------------------------------------------
      // NORMAL RAG QUESTION
      // --------------------------------------------------------

      else {

        data =
          await askAURA(
            text,
            currentConversationId,
            selectedDocumentId
          );
      }


      if (
        data.chat_id ||
        data.conversation_id
      ) {

        setCurrentConversationId(
          data.chat_id ||
          data.conversation_id
        );
      }


      await loadConversations();


      const assistantMessage = {

        id:
          `assistant-${Date.now()}`,

        role: "assistant",

        content:
          data.answer ||
          "DrugAssist did not return an answer.",

        /*
         * These fields are extremely important.
         * They allow Message.jsx to display
         * clickable citations.
         */

        sources:
          Array.isArray(data.sources)
            ? data.sources
            : [],

        videos:
          Array.isArray(data.videos)
            ? data.videos
            : [],

        attachments:
          Array.isArray(data.attachments)
            ? data.attachments
            : [],

        evidence:
          Array.isArray(data.evidence)
            ? data.evidence
            : [],

        confidence:
          data.confidence ??
          null,

        grounding_score:
          data.grounding_score ??
          null,

        mode:
          data.mode ??
          null,

        image_analysis:
          data.image_analysis ??
          null
      };


      setMessages(
        (previous) => [
          ...previous,
          assistantMessage
        ]
      );


    } catch (error) {

      console.error(
        "DRUGASSIST ERROR:",
        error
      );


      if (isAuthError(error)) {
        handleLogout();
        return;
      }


      setMessages(
        (previous) => [
          ...previous,

          {
            id:
              `error-${Date.now()}`,

            role: "assistant",

            content:
              error.message ||
              "Sorry, something went wrong."
          }
        ]
      );

    } finally {

      setLoading(false);
    }
  };


  // ============================================================
  // FILE UPLOAD
  // ============================================================

  const handleFileUpload = async (
    file,
    isImage = false
  ) => {

    if (!file) return;


    // ----------------------------------------------------------
    // IMAGE
    // ----------------------------------------------------------

    if (isImage) {

      if (
        !file.type.startsWith(
          "image/"
        )
      ) {
        return;
      }


      if (
        file.size >
        15 * 1024 * 1024
      ) {

        setMessages(
          (previous) => [
            ...previous,

            {
              id:
                `image-error-${Date.now()}`,

              role: "assistant",

              content:
                "Please select an image smaller than 15 MB."
            }
          ]
        );

        return;
      }


      if (pendingImagePreview) {

        URL.revokeObjectURL(
          pendingImagePreview
        );
      }


      const previewUrl =
        URL.createObjectURL(
          file
        );


      setPendingImage({
        file,
        name: file.name
      });


      setPendingImagePreview(
        previewUrl
      );


      return;
    }


    // ----------------------------------------------------------
    // PDF
    // ----------------------------------------------------------

    if (
      file.type !==
      "application/pdf"
    ) {

      setMessages(
        (previous) => [
          ...previous,

          {
            id:
              `pdf-error-${Date.now()}`,

            role: "assistant",

            content:
              "Please select a PDF file."
          }
        ]
      );

      return;
    }


    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();
      return;
    }


    setMessages(
      (previous) => [
        ...previous,

        {
          id:
            `upload-${Date.now()}`,

          role: "user",

          content:
            `Uploading ${file.name}...`
        }
      ]
    );


    setLoading(true);


    try {

      /*
       * The BACKEND is responsible for
       * trusted-PDF fingerprint validation.
       *
       * Unknown/fabricated PDFs should be rejected
       * before they become authoritative RAG sources.
       */

      const data =
        await uploadPDF(file);


      console.log(
        "PDF RESPONSE:",
        data
      );


      if (
        data.document_id !==
          undefined &&
        data.document_id !==
          null
      ) {

        setSelectedDocumentId(
          data.document_id
        );

        setSelectedDocumentName(
          data.filename ||
          file.name
        );
      }


      await loadDocuments();


      setMessages(
        (previous) => [
          ...previous,

          {
            id:
              `pdf-success-${Date.now()}`,

            role: "assistant",

            content:
              `${file.name} is ready and selected. Type your question below and press Send.`
          }
        ]
      );


    } catch (error) {

      console.error(
        "PDF ERROR:",
        error
      );


      if (isAuthError(error)) {
        handleLogout();
        return;
      }


      setMessages(
        (previous) => [
          ...previous,

          {
            id:
              `pdf-error-${Date.now()}`,

            role: "assistant",

            content:
              `PDF upload failed.\n\n${error.message}`
          }
        ]
      );

    } finally {

      setLoading(false);
    }
  };


  // ============================================================
  // REMOVE IMAGE
  // ============================================================

  const removePendingImage = () => {

    if (pendingImagePreview) {

      URL.revokeObjectURL(
        pendingImagePreview
      );
    }


    setPendingImage(null);

    setPendingImagePreview("");
  };


  // ============================================================
  // VOICE
  // ============================================================

  const speakAnswer = async (
    answer
  ) => {

    if (!answer) return;


    try {

      if (
        "speechSynthesis" in window
      ) {

        window.speechSynthesis.cancel();


        const cleanText =
          answer
            .replace(
              /\[Source[^\]]*\]/gi,
              ""
            )
            .replace(
              /\[\^?[0-9]+\]/gi,
              ""
            )
            .replace(
              /[*#_`>]/g,
              ""
            )
            .replace(
              /\n+/g,
              " "
            )
            .trim();


        const utterance =
          new SpeechSynthesisUtterance(
            cleanText
          );


        utterance.rate = 1;

        utterance.pitch = 1;


        utterance.onstart = () => {
          setVoiceStatus(
            "Speaking response..."
          );
        };


        utterance.onend = () => {
          setVoiceStatus("");
        };


        utterance.onerror = () => {
          setVoiceStatus("");
        };


        window.speechSynthesis.speak(
          utterance
        );
      }

    } catch (error) {

      console.error(
        "TTS ERROR:",
        error
      );

      setVoiceStatus("");
    }
  };


  const processVoiceRecording =
    async (
      audioBlob
    ) => {

      if (
        !audioBlob ||
        audioBlob.size === 0
      ) {

        throw new Error(
          "No audio was recorded."
        );
      }


      setLoading(true);

      setVoiceStatus(
        "Understanding your voice..."
      );


      try {

        const data =
          await voiceAsk(
            audioBlob,
            "",
            currentConversationId,
            selectedDocumentId
          );


        if (
          data.conversation_id
        ) {

          setCurrentConversationId(
            data.conversation_id
          );
        }


        await loadConversations();


        const transcript =
          data.transcript?.trim();


        const answer =
          data.answer?.trim();


        if (!transcript) {

          throw new Error(
            "DrugAssist could not understand the recording."
          );
        }


        setMessages(
          (previous) => [
            ...previous,

            {
              id:
                `voice-user-${Date.now()}`,

              role: "user",

              content:
                transcript
            },

            {
              id:
                `voice-assistant-${Date.now() + 1}`,

              role: "assistant",

              content:
                answer ||
                "DrugAssist did not return an answer.",

              sources:
                Array.isArray(data.sources)
                  ? data.sources
                  : []
            }
          ]
        );


        setVoiceStatus(
          "Voice response ready."
        );


        if (answer) {

          await speakAnswer(
            answer
          );
        }

      } finally {

        setLoading(false);
      }
    };


  const startRecording = async () => {

    if (
      isRecording ||
      loading
    ) {
      return;
    }


    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;


    // ----------------------------------------------------------
    // BROWSER SPEECH RECOGNITION
    // ----------------------------------------------------------

    if (SpeechRecognition) {

      try {

        const recognition =
          new SpeechRecognition();


        recognition.continuous =
          false;

        recognition.interimResults =
          true;

        recognition.lang =
          "en-US";


        recognition.onstart = () => {

          setIsRecording(true);

          setVoiceStatus(
            "Listening... speak now"
          );
        };


        recognition.onresult =
          (event) => {

            let text = "";

            for (
              let i = 0;
              i < event.results.length;
              i++
            ) {

              text +=
                event.results[i][0]
                  .transcript;
            }


            if (text) {

              setInput(text);
            }
          };


        recognition.onerror =
          (event) => {

            console.warn(
              "Speech recognition:",
              event.error
            );

            setIsRecording(false);

            setVoiceStatus(
              event.error ===
                "not-allowed"
                ? "Microphone access denied."
                : "No speech detected. Please try again."
            );


            setTimeout(
              () => setVoiceStatus(""),
              4000
            );
          };


        recognition.onend = () => {

          setIsRecording(false);

          setVoiceStatus("");

          speechRecognitionRef.current =
            null;
        };


        speechRecognitionRef.current =
          recognition;


        recognition.start();

        return;

      } catch (error) {

        console.warn(
          "SpeechRecognition fallback:",
          error
        );
      }
    }


    // ----------------------------------------------------------
    // MEDIA RECORDER FALLBACK
    // ----------------------------------------------------------

    if (
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {

      setVoiceStatus(
        "Your browser does not support microphone recording."
      );

      return;
    }


    try {

      const stream =
        await navigator.mediaDevices
          .getUserMedia({
            audio: true
          });


      streamRef.current =
        stream;


      audioChunksRef.current =
        [];


      const mimeType =
        MediaRecorder.isTypeSupported(
          "audio/webm;codecs=opus"
        )
          ? "audio/webm;codecs=opus"
          : "audio/webm";


      const recorder =
        new MediaRecorder(
          stream,
          { mimeType }
        );


      mediaRecorderRef.current =
        recorder;


      recorder.ondataavailable =
        (event) => {

          if (
            event.data &&
            event.data.size > 0
          ) {

            audioChunksRef.current.push(
              event.data
            );
          }
        };


      recorder.onstop =
        async () => {

          try {

            const audioBlob =
              new Blob(
                audioChunksRef.current,
                {
                  type:
                    recorder.mimeType ||
                    "audio/webm"
                }
              );


            audioChunksRef.current =
              [];


            if (streamRef.current) {

              streamRef.current
                .getTracks()
                .forEach(
                  (track) =>
                    track.stop()
                );

              streamRef.current =
                null;
            }


            mediaRecorderRef.current =
              null;


            await processVoiceRecording(
              audioBlob
            );

          } catch (error) {

            console.error(
              "VOICE ERROR:",
              error
            );

            setVoiceStatus(
              error.message
            );

            setLoading(false);
          }
        };


      recorder.start();


      setIsRecording(true);

      setVoiceStatus(
        "Listening... click microphone again to stop."
      );

    } catch (error) {

      console.error(
        "MICROPHONE ERROR:",
        error
      );

      setIsRecording(false);

      setVoiceStatus(
        "Unable to access microphone."
      );
    }
  };


  const stopRecording = () => {

    if (
      speechRecognitionRef.current
    ) {

      try {
        speechRecognitionRef.current.stop();
      } catch {}

      speechRecognitionRef.current =
        null;

      setIsRecording(false);

      return;
    }


    const recorder =
      mediaRecorderRef.current;


    if (
      recorder &&
      recorder.state === "recording"
    ) {

      setVoiceStatus(
        "Processing your voice..."
      );

      recorder.stop();

    } else {

      setIsRecording(false);
    }
  };


  const handleVoice = () => {

    if (loading) return;


    if (isRecording) {

      stopRecording();

    } else {

      startRecording();
    }
  };


  // ============================================================
  // CLEANUP
  // ============================================================

  useEffect(() => {

    return () => {

      if (
        mediaRecorderRef.current
      ) {

        try {

          if (
            mediaRecorderRef.current.state !==
            "inactive"
          ) {
            mediaRecorderRef.current.stop();
          }

        } catch {}
      }


      if (streamRef.current) {

        streamRef.current
          .getTracks()
          .forEach(
            (track) =>
              track.stop()
          );
      }


      if (
        speechRecognitionRef.current
      ) {

        try {
          speechRecognitionRef.current.stop();
        } catch {}
      }
    };

  }, []);


  // ============================================================
  // LOGIN PAGE
  // ============================================================

  if (!isAuthenticated) {

    return (
      <AuthPage
        onLogin={handleLogin}
      />
    );
  }


  // ============================================================
  // MAIN APPLICATION
  // ============================================================

  return (

    <div className="app-shell">

      <style>{`

        .chat-area p {
          margin-top: 0;
          margin-bottom: 12px;
        }

        .chat-area ul,
        .chat-area ol {
          margin-top: 8px;
          margin-bottom: 14px;
          padding-left: 24px;
        }

        .chat-area li {
          margin-bottom: 6px;
        }

        .chat-area h1,
        .chat-area h2,
        .chat-area h3,
        .chat-area h4 {
          margin-top: 18px;
          margin-bottom: 8px;
          line-height: 1.3;
        }

        .chat-area .chat-window {
          width: 100% !important;
          height: auto !important;
          min-height: 0 !important;
          overflow: visible !important;
        }

        .chat-area .chat-window .messages {
          width: 100% !important;
          max-width: 980px !important;
          min-height: 0 !important;
          height: auto !important;
          margin: 0 auto !important;
          padding: 28px 24px 40px !important;
          box-sizing: border-box !important;
        }

        .drugassist-empty-state {
          width: 100%;
          min-height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px 24px 120px;
          box-sizing: border-box;
        }

        .drugassist-empty-content {
          width: min(720px, 100%);
          text-align: center;
        }

        .drugassist-empty-title {
          margin: 0 0 10px;
          font-size: 42px;
          line-height: 1.15;
          font-weight: 700;
        }

        .drugassist-empty-subtitle {
          margin: 0;
          font-size: 16px;
          line-height: 1.6;
          color: #777b84;
        }


        /* ======================================================
           PDF VIEWER
        ====================================================== */

        .pdf-viewer-overlay {
          position: fixed;
          inset: 0;
          z-index: 9999;
          background: rgba(0, 0, 0, 0.72);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          box-sizing: border-box;
        }

        .pdf-viewer-container {
          width: min(1200px, 100%);
          height: min(92vh, 900px);
          background: white;
          border-radius: 14px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
        }

        .pdf-viewer-header {
          height: 58px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 16px;
          border-bottom: 1px solid #e5e7eb;
          background: #ffffff;
        }

        .pdf-viewer-title {
          display: flex;
          align-items: center;
          gap: 9px;
          min-width: 0;
          font-weight: 600;
        }

        .pdf-viewer-title span {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .pdf-viewer-page-label {
          font-size: 13px;
          font-weight: 500;
          color: #6b7280;
          flex-shrink: 0;
        }

        .pdf-viewer-close {
          border: 0;
          background: transparent;
          cursor: pointer;
          width: 38px;
          height: 38px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .pdf-viewer-close:hover {
          background: #f3f4f6;
        }

        .pdf-viewer-body {
          flex: 1;
          min-height: 0;
          background: #525659;
        }

        .pdf-viewer-frame {
          width: 100%;
          height: 100%;
          border: 0;
          display: block;
        }

        .pdf-viewer-loading {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: white;
          gap: 12px;
        }

        .pdf-spinner {
          width: 32px;
          height: 32px;
          border: 3px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: pdf-spin 0.8s linear infinite;
        }

        @keyframes pdf-spin {
          to {
            transform: rotate(360deg);
          }
        }


        @media (max-width: 700px) {

          .pdf-viewer-overlay {
            padding: 0;
          }

          .pdf-viewer-container {
            width: 100%;
            height: 100%;
            border-radius: 0;
          }

          .pdf-viewer-header {
            height: 52px;
          }
        }

      `}</style>


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <Sidebar

        user={user}

        chats={conversations}

        activeChatId={
          currentConversationId
        }

        currentView={
          currentView
        }

        onNewChat={
          handleNewChat
        }

        onViewChat={
          handleOpenChat
        }

        onSelectChat={
          handleOpenConversation
        }

        onDeleteChat={
          handleDeleteChat
        }

        onLibrary={
          handleOpenLibrary
        }

        onLogout={
          handleLogout
        }

        mobileOpen={
          mobileOpen
        }

        onClose={() =>
          setMobileOpen(false)
        }

        onOpenPrivacy={() =>
          setShowPrivacy(true)
        }

        onOpenTerms={() =>
          setShowTerms(true)
        }

        conversations={
          conversations
        }

        currentConversationId={
          currentConversationId
        }

        onSelectConversation={
          handleOpenConversation
        }

        uploadedFiles={
          uploadedFiles
        }

        uploadedDocuments={
          uploadedDocuments
        }

        selectedDocumentId={
          selectedDocumentId
        }

        onSelectDocument={
          handleSelectDocument
        }

        onDeleteDocument={
          handleDeleteDocument
        }

        onDeleteAllChats={
          handleDeleteAllConversations
        }
      />


      {/* ======================================================
          MAIN
      ====================================================== */}

      <section
        className="main-shell"
        style={{
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          height: "100vh",
          overflow: "hidden",
          position: "relative"
        }}
      >


        {/* ====================================================
            TOP BAR
        ==================================================== */}

        <header className="topbar">

          <button
            type="button"
            className="mobile-menu-button"
            onClick={() =>
              setMobileOpen(true)
            }
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>


          <div className="mobile-brand">

            <Pill size={16} />

            <span>
              DrugAssist
            </span>

          </div>


          <div className="topbar-spacer" />


          <div className="topbar-actions">

            <button
              type="button"
              className="theme-button"
              onClick={
                toggleTheme
              }
              title={
                theme === "light"
                  ? "Switch to dark mode"
                  : "Switch to light mode"
              }
            >

              {theme === "light" ? (
                <Moon size={18} />
              ) : (
                <Sun size={18} />
              )}

            </button>

          </div>

        </header>


        {/* ====================================================
            SCROLL PROGRESS
        ==================================================== */}

        <div
          className="scroll-progress-bar"
          style={{
            width:
              `${scrollProgress}%`
          }}
        />


        {/* ====================================================
            CONTENT
        ==================================================== */}

        {currentView === "library" ? (

          <Library

            apiUrl={
              API_BASE_URL
            }

            token={
              localStorage.getItem(
                "aura_token"
              )
            }

            onBack={
              handleOpenChat
            }

            selectedDocumentId={
              selectedDocumentId
            }

            onSelectDocument={
              handleSelectDocument
            }

            /*
             * NEW:
             * Library can call this when the
             * user wants to actually OPEN
             * the PDF.
             */
            onOpenDocument={
              handleOpenDocument
            }

          />

        ) : (

          <div
            id="main-chat-area"
            ref={chatAreaRef}
            className="chat-area"
            style={{
              flex: "1 1 auto",
              minHeight: 0,
              overflowY: "auto",
              overflowX: "hidden",
              paddingBottom: "280px",
              scrollBehavior: "smooth"
            }}
          >


            {messages.length === 0 && (

              <div className="welcome-screen">

                <div
                  className="welcome-logo"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}
                >

                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 24 24"
                    fill="none"
                  >

                    <rect
                      x="2"
                      y="2"
                      width="20"
                      height="20"
                      rx="4"
                      fill="#0f172a"
                    />

                    <path
                      d="M12 6v12"
                      stroke="#38bdf8"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />

                    <path
                      d="M6 12h12"
                      stroke="#38bdf8"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                    />

                  </svg>

                </div>


                <h2>
                  Prescribing Information Assistant
                </h2>


                <p>
                  Grounded clinical drug
                  intelligence with official
                  citations. Query indications,
                  dosages, contraindications,
                  boxed warnings, and drug
                  interactions directly from
                  official labeling literature.
                </p>


                <FAQAccordion />

              </div>
            )}


            {messages.length > 0 && (

              <ChatWindow

                messages={
                  messages
                }

                loading={
                  loading
                }

                /*
                 * NEW:
                 * Message.jsx should call this
                 * when a citation is clicked.
                 */
                onOpenSource={
                  handleOpenSource
                }

              />

            )}


          </div>
        )}


        {/* ====================================================
            VOICE STATUS
        ==================================================== */}

        {currentView === "chat" &&
          voiceStatus && (

            <div
              className={
                isRecording
                  ? "voice-status recording"
                  : "voice-status"
              }
            >

              <span>
                {isRecording
                  ? "●"
                  : "◉"}
              </span>

              {voiceStatus}

            </div>
          )}


        {/* ====================================================
            CHAT INPUT
        ==================================================== */}

        {currentView === "chat" && (

          <ChatInput

            value={
              input
            }

            onChange={
              setInput
            }

            onSend={
              handleSend
            }

            onVoice={
              handleVoice
            }

            isRecording={
              isRecording
            }

            voiceStatus={
              voiceStatus
            }

            onFileUpload={
              handleFileUpload
            }

            pendingImage={
              pendingImage
            }

            pendingImagePreview={
              pendingImagePreview
            }

            onRemoveImage={
              removePendingImage
            }

            loading={
              loading
            }

            selectedDocumentName={
              selectedDocumentId
                ? selectedDocumentName
                : null
            }

            onChangeDocument={
              handleOpenLibrary
            }

            onClearDocument={() => {

              setSelectedDocumentId(
                null
              );

              setSelectedDocumentName(
                ""
              );
            }}

          />

        )}

      </section>


      {/* ======================================================
          SCROLL TO TOP
      ====================================================== */}

      {showScrollTop &&
        currentView === "chat" && (

          <button
            type="button"
            className="scroll-to-top-btn"
            onClick={
              handleScrollToTop
            }
            title="Scroll to top"
            aria-label="Scroll to top"
          >
            <ArrowUp
              size={18}
            />
          </button>

        )}


      {/* ======================================================
          PRIVACY
      ====================================================== */}

      {showPrivacy && (

        <PrivacyPolicy
          onClose={() =>
            setShowPrivacy(false)
          }
        />

      )}


      {/* ======================================================
          TERMS
      ====================================================== */}

      {showTerms && (

        <TermsAndConditions
          onClose={() =>
            setShowTerms(false)
          }
        />

      )}


      {/* ======================================================
          PDF VIEWER
      ====================================================== */}

      {pdfViewer.open && (

        <div
          className="pdf-viewer-overlay"
          role="dialog"
          aria-modal="true"
          aria-label="PDF viewer"
        >

          <div className="pdf-viewer-container">


            {/* HEADER */}

            <div className="pdf-viewer-header">

              <div className="pdf-viewer-title">

                <FileText
                  size={18}
                />

                <span
                  title={
                    pdfViewer.filename
                  }
                >
                  {pdfViewer.filename}
                </span>


                <span className="pdf-viewer-page-label">

                  Page{" "}
                  {pdfViewer.page}

                </span>

              </div>


              <button
                type="button"
                className="pdf-viewer-close"
                onClick={
                  handleClosePdfViewer
                }
                aria-label="Close PDF viewer"
              >

                <X
                  size={20}
                />

              </button>

            </div>


            {/* PDF */}

            <div className="pdf-viewer-body">

              {pdfLoading ? (

                <div className="pdf-viewer-loading">

                  <div className="pdf-spinner" />

                  <p>
                    Loading verified PDF...
                  </p>

                </div>

              ) : (

                <iframe

                  className="pdf-viewer-frame"

                  src={
                    `${pdfViewer.url}#page=${pdfViewer.page}`
                  }

                  title={
                    pdfViewer.filename ||
                    "Drug Information PDF"
                  }

                />

              )}

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default App;