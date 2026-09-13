import {
  useEffect,
  useRef,
  useState
} from "react";

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
  getChatHistory,
  getDocuments,
  uploadPDF,
  getConversations,
  getConversation,
  deleteConversation,
  deleteAllConversations,
  deletePDF,
  askImage,
  voiceAsk
} from "./services/api";


const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";


function App() {

  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [isAuthenticated, setIsAuthenticated] =
    useState(
      Boolean(
        localStorage.getItem("aura_token")
      )
    );

  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // ============================================================
  // THEME MANAGEMENT (Light / Dark)
  // ============================================================

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("drugassist_theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("drugassist_theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((previous) => (previous === "light" ? "dark" : "light"));
  };

  // Keep the logged-in user available to the Sidebar.
  // AuthPage stores this object in localStorage as "aura_user".
  const [user, setUser] = useState(() => {
    try {
      const storedUser =
        localStorage.getItem("aura_user");

      return storedUser
        ? JSON.parse(storedUser)
        : null;
    } catch (error) {
      console.error("USER PARSE ERROR:", error);
      return null;
    }
  });

  // Current application view.
  const [currentView, setCurrentView] =
    useState("chat");


  // ============================================================
  // CHAT
  // ============================================================

  const [messages, setMessages] =
    useState([]);

  const [input, setInput] =
    useState("");

  const [loading, setLoading] =
    useState(false);


  // ============================================================
  // CONVERSATIONS
  // ============================================================

  const [conversations, setConversations] =
    useState([]);

  const [currentConversationId, setCurrentConversationId] =
    useState(null);

  const [loadingConversation, setLoadingConversation] =
    useState(false);


  // ============================================================
  // UPLOADED FILES
  // ============================================================

  const [uploadedFiles, setUploadedFiles] =
    useState([]);

  const [uploadedDocuments, setUploadedDocuments] =
    useState([]);

  const [selectedDocumentId, setSelectedDocumentId] =
    useState(null);

  const [selectedDocumentName, setSelectedDocumentName] =
    useState("");


  // ============================================================
  // PENDING IMAGE ATTACHMENT
  // ============================================================

  const [pendingImage, setPendingImage] =
    useState(null);

  const [pendingImagePreview, setPendingImagePreview] =
    useState("");


  // ============================================================
  // VOICE
  // ============================================================

  const [isRecording, setIsRecording] =
    useState(false);

  const [voiceStatus, setVoiceStatus] =
    useState("");

  const mediaRecorderRef =
    useRef(null);

  const audioChunksRef =
    useRef([]);

  const streamRef =
    useRef(null);

  const speechRecognitionRef =
    useRef(null);


  // ============================================================
  // CHAT SCROLL
  // ============================================================

  const chatEndRef =
    useRef(null);

  const chatAreaRef =
    useRef(null);

  // Scroll & UTM tracking
  const [scrollProgress, setScrollProgress] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);

  // UTM Tracking (Item 14)
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const utmSource = params.get("utm_source");
      const utmMedium = params.get("utm_medium");
      const utmCampaign = params.get("utm_campaign");
      if (utmSource || utmMedium || utmCampaign) {
        sessionStorage.setItem(
          "drugassist_utm",
          JSON.stringify({
            source: utmSource || "",
            medium: utmMedium || "",
            campaign: utmCampaign || "",
            timestamp: new Date().toISOString()
          })
        );
      }
    } catch (e) {}
  }, []);

  // Scroll tracking on chatAreaRef (Items 4 & 8)
  useEffect(() => {
    const el = chatAreaRef.current;
    if (!el) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      const total = scrollHeight - clientHeight;
      const progress = total > 0 ? Math.min(100, Math.max(0, (scrollTop / total) * 100)) : 0;
      setScrollProgress(progress);
      setShowScrollTop(scrollTop > 260);
    };

    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, [currentView, messages.length]);

  const handleScrollToTop = () => {
    if (chatAreaRef.current) {
      chatAreaRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleDismissBanner = () => {
    setShowBanner(false);
    sessionStorage.setItem("drugassist_dismiss_banner", "true");
  };


  // ============================================================
  // AUTO-SCROLL CHAT
  // ============================================================

  useEffect(() => {
    /*
      The .chat-area element is the ONLY scrolling container.
      ChatWindow itself is forced to be content-sized below, so the
      browser does not have two competing scrollbars.
    */
    let frame1;
    let frame2;

    frame1 = requestAnimationFrame(() => {
      frame2 = requestAnimationFrame(() => {
        const chatArea = chatAreaRef.current;

        if (chatArea) {
          chatArea.scrollTo({
            top: chatArea.scrollHeight,
            behavior: "smooth"
          });
        }
      });
    });

    return () => {
      cancelAnimationFrame(frame1);
      if (frame2) {
        cancelAnimationFrame(frame2);
      }
    };
  }, [
    messages,
    loading,
    voiceStatus,
    currentConversationId
  ]);


  // ============================================================
  // LOAD DATA AFTER LOGIN
  // ============================================================

  useEffect(() => {

    if (!isAuthenticated) {
      return;
    }

    loadConversations();
    loadDocuments();

  }, [isAuthenticated]);


  // ============================================================
  // CLEANUP MICROPHONE
  // ============================================================

  useEffect(() => {

    return () => {

      if (mediaRecorderRef.current) {

        try {

          if (
            mediaRecorderRef.current.state !==
            "inactive"
          ) {
            mediaRecorderRef.current.stop();
          }

        } catch (error) {
          console.error(
            "Recorder cleanup error:",
            error
          );
        }

      }


      if (streamRef.current) {

        streamRef.current
          .getTracks()
          .forEach(
            (track) => track.stop()
          );

      }

    };

  }, []);


  // ============================================================
  // CLEANUP IMAGE PREVIEW
  // ============================================================

  useEffect(() => {
    return () => {
      if (pendingImagePreview) {
        URL.revokeObjectURL(pendingImagePreview);
      }
    };
  }, [pendingImagePreview]);


  // ============================================================
  // LOAD CONVERSATIONS
  // ============================================================

  const loadConversations = async () => {

    try {

      const data =
        await getConversations();

      const list = Array.isArray(data)
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

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
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
        data.messages || [];

      // Backend returns one database message per record:
      // { id, role, content, sources, videos, ... }.
      // Do not convert each record into question/answer pairs;
      // doing that was the reason old chats appeared empty.
      const loadedMessages = conversationMessages
        .filter((item) => item && item.role && item.content !== undefined)
        .map((item) => ({
          id: item.id || `message-${Date.now()}-${Math.random()}`,
          role: item.role,
          content: item.content,
          sources: item.sources || [],
          attachments: item.attachments || [],
          evidence: item.evidence || [],
          confidence: item.confidence,
          grounding_score: item.grounding_score,
          mode: item.mode,
          image_analysis: item.image_analysis
        }));

      setMessages(
        loadedMessages
      );

      setInput("");

      setPendingImage(null);
      setPendingImagePreview("");

    } catch (error) {

      console.error(
        "OPEN CONVERSATION ERROR:",
        error
      );

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
        handleLogout();
        return;
      }

      setMessages([
        {
          id:
            `conversation-error-${Date.now()}`,
          role:
            "assistant",
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
  // LOAD DOCUMENTS
  // ============================================================

  const loadDocuments = async () => {

    try {

      const data =
        await getDocuments();

      const documents =
        data.documents || [];

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
        const selected = documents.find(
          (document) =>
            Number(document.id) ===
            Number(selectedDocumentId)
        );

        if (selected) {
          setSelectedDocumentName(
            selected.filename
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


      if (
        error.message?.includes(
          "session has expired"
        )
      ) {

        handleLogout();

      }

    }

  };


  // ============================================================
  // DELETE PDF
  // ============================================================

  const handleDeleteDocument = async (documentId) => {

    try {
      await deletePDF(documentId);

      if (Number(selectedDocumentId) === Number(documentId)) {
        setSelectedDocumentId(null);
        setSelectedDocumentName("");
      }

      await loadDocuments();

    } catch (error) {

      console.error("DELETE PDF ERROR:", error);

      if (error.message?.includes("session has expired")) {
        handleLogout();
      }

    }
  };


  // ============================================================
  // SELECT PDF
  // ============================================================

  const handleSelectDocument = (
    documentOrId
  ) => {
    if (typeof documentOrId === "object" && documentOrId !== null) {
      setSelectedDocumentId(documentOrId.id);
      setSelectedDocumentName(
        documentOrId.filename || "Selected document"
      );

      setUploadedDocuments((previous) => {
        if (
          previous.some(
            (doc) => Number(doc.id) === Number(documentOrId.id)
          )
        ) {
          return previous;
        }
        return [...previous, documentOrId];
      });

      setCurrentView("chat");
      setInput("");
      return;
    }

    const documentId = documentOrId;
    const selected = uploadedDocuments.find(
      (document) =>
        Number(document.id) ===
        Number(documentId)
    );

    if (selected) {
      setSelectedDocumentId(
        selected.id
      );

      setSelectedDocumentName(
        selected.filename
      );
    } else {
      setSelectedDocumentId(documentId);
    }

    setCurrentView("chat");
    setInput("");
  };


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = () => {

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      console.error(
        "Login completed but token was not found."
      );

      return;

    }


    try {
      const storedUser =
        localStorage.getItem("aura_user");

      setUser(
        storedUser
          ? JSON.parse(storedUser)
          : null
      );
    } catch (error) {
      console.error("USER PARSE ERROR:", error);
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

    localStorage.removeItem(
      "aura_token"
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


    // Stop microphone if active

    if (mediaRecorderRef.current) {

      try {

        if (
          mediaRecorderRef.current.state !==
          "inactive"
        ) {
          mediaRecorderRef.current.stop();
        }

      } catch (error) {
        console.error(
          "Recorder logout error:",
          error
        );
      }

    }


    if (streamRef.current) {

      streamRef.current
        .getTracks()
        .forEach(
          (track) => track.stop()
        );

      streamRef.current = null;

    }


    setIsRecording(false);
    setVoiceStatus("");

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
        "DELETE CONVERSATION ERROR:",
        error
      );

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
        handleLogout();
      }

    }

  };


  // ============================================================
  // DELETE ALL CONVERSATIONS
  // ============================================================

  const handleDeleteAllConversations = async () => {

    try {

      await deleteAllConversations();

      setConversations([]);
      handleNewChat();

    } catch (error) {

      console.error(
        "DELETE ALL CONVERSATIONS ERROR:",
        error
      );

      if (
        error.message?.includes(
          "session has expired"
        )
      ) {
        handleLogout();
      }

    }

  };


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSend = async () => {

    const text = input.trim();

    if (!text || loading) {
      return;
    }

    const token =
      localStorage.getItem("aura_token");

    if (!token) {
      handleLogout();
      return;
    }

    const imageToSend = pendingImage;
    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text
    };

    setMessages((previous) => [
      ...previous,
      userMessage
    ]);

    setInput("");
    setPendingImage(null);
    setPendingImagePreview("");
    setLoading(true);

    try {

      if (imageToSend) {

        const data =
          await askImage(
            text,
            imageToSend.file,
            currentConversationId
          );

        if (data.chat_id || data.conversation_id) {
          setCurrentConversationId(
            data.chat_id || data.conversation_id
          );
        }

        await loadConversations();

        setMessages((previous) => [
          ...previous,
          {
            id:
              `assistant-${Date.now()}`,
            role:
              "assistant",
            content:
              data.answer ||
              "DrugAssist could not generate an image analysis."
          }
        ]);

      } else {

        const data =
          await askAURA(
            text,
            currentConversationId,
            selectedDocumentId
          );

        if (data.chat_id || data.conversation_id) {
          setCurrentConversationId(
            data.chat_id || data.conversation_id
          );
        }

        await loadConversations();

        setMessages((previous) => [
          ...previous,
          {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content:
              data.answer ||
              "DrugAssist did not return an answer."
          }
        ]);

      }

    } catch (error) {

      console.error("DRUGASSIST ERROR:", error);

      if (
        error.message?.includes("session has expired")
      ) {
        handleLogout();
        return;
      }

      setMessages((previous) => [
        ...previous,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            error.message ||
            "Sorry, something went wrong."
        }
      ]);

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

    if (!file) {
      return;
    }


    // ==========================================================
    // IMAGE - OCR + VISION
    // ==========================================================

    if (isImage) {

      const token =
        localStorage.getItem("aura_token");

      if (!token) {
        handleLogout();
        return;
      }

      if (!file.type.startsWith("image/")) {
        return;
      }

      if (file.size > 15 * 1024 * 1024) {
        setMessages((previous) => [
          ...previous,
          {
            id: `image-error-${Date.now()}`,
            role: "assistant",
            content: "Please select an image smaller than 15 MB."
          }
        ]);
        return;
      }

      if (pendingImagePreview) {
        URL.revokeObjectURL(pendingImagePreview);
      }

      const previewUrl = URL.createObjectURL(file);

      setPendingImage({
        file,
        name: file.name
      });
      setPendingImagePreview(previewUrl);

      return;

    }


    // ==========================================================

    // ==========================================================

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

            role:
              "assistant",

            content:
              "Please select a PDF file."

          }

        ]
      );


      return;

    }


    // ==========================================================
    // AUTH CHECK
    // ==========================================================

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();

      return;

    }


    // ==========================================================
    // SHOW UPLOADING
    // ==========================================================

    setMessages(
      (previous) => [
        ...previous,

        {

          id:
            `upload-${Date.now()}`,

          role:
            "user",

          content:
            `Uploading ${file.name}...`

        }

      ]
    );


    setLoading(true);


    try {

      const data =
        await uploadPDF(file);


      console.log(
        "PDF RESPONSE:",
        data
      );


      if (
        data.document_id !== undefined &&
        data.document_id !== null
      ) {
        setSelectedDocumentId(
          data.document_id
        );

        setSelectedDocumentName(
          data.filename || file.name
        );
      }

      await loadDocuments();


      setMessages(
        (previous) => [
          ...previous,
          {
            id:
              `pdf-success-${Date.now()}`,
            role:
              "assistant",
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


      if (
        error.message?.includes(
          "session has expired"
        )
      ) {

        handleLogout();

        return;

      }


      setMessages(
        (previous) => [
          ...previous,

          {

            id:
              `pdf-error-${Date.now()}`,

            role:
              "assistant",

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
  // REMOVE PENDING IMAGE
  // ============================================================

  const removePendingImage = () => {
    if (pendingImagePreview) {
      URL.revokeObjectURL(pendingImagePreview);
    }

    setPendingImage(null);
    setPendingImagePreview("");
  };


  // ============================================================
  // VOICE - GET AUTH TOKEN
  // ============================================================

  const getVoiceToken = () => {

    const token =
      localStorage.getItem(
        "aura_token"
      );


    if (!token) {

      handleLogout();

      throw new Error(
        "Your session has expired. Please log in again."
      );

    }


    return token;

  };


  // ============================================================
  // VOICE - TEXT TO SPEECH
  // ============================================================

  const speakAnswer = async (
    answer
  ) => {

    if (!answer) {
      return;
    }

    try {
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const cleanText = answer
          .replace(/\[Source[^\]]*\]/gi, "")
          .replace(/\[\^?[0-9]+\]/gi, "")
          .replace(/[*#_`>]/g, "")
          .replace(/\n+/g, " ")
          .trim();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.onstart = () => {
          setVoiceStatus("Speaking response...");
        };
        utterance.onend = () => {
          setVoiceStatus("");
        };
        utterance.onerror = () => {
          setVoiceStatus("");
        };
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      console.error("TEXT TO SPEECH ERROR:", error);
      setVoiceStatus("");
    }
  };


  // ============================================================
  // VOICE - SEND RECORDED AUDIO TO BACKEND
  // ============================================================

  const processVoiceRecording = async (
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


    const token =
      getVoiceToken();


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

      if (data.conversation_id) {
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


      // ----------------------------------------------------------
      // ADD TRANSCRIPT TO CHAT
      // ----------------------------------------------------------

      setMessages(
        (previous) => [

          ...previous,

          {

            id:
              `voice-user-${Date.now()}`,

            role:
              "user",

            content:
              transcript

          },

          {

            id:
              `voice-assistant-${Date.now() + 1}`,

            role:
              "assistant",

            content:
              answer ||
              "DrugAssist did not return an answer."

          }

        ]
      );


      setVoiceStatus(
        "Voice response ready."
      );


      // ----------------------------------------------------------
      // SPEAK ANSWER
      // ----------------------------------------------------------

      if (answer) {

        await speakAnswer(
          answer
        );

      }


    } finally {

      setLoading(false);

    }

  };


  // ============================================================
  // VOICE - START RECORDING
  // ============================================================

  const startRecording = async () => {

    if (
      isRecording ||
      loading
    ) {
      return;
    }

    // 1. Try native Web Speech API (real-time voice typing)
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        recognition.onstart = () => {
          setIsRecording(true);
          setVoiceStatus("Listening... speak now");
        };

        recognition.onresult = (event) => {
          let text = "";
          for (let i = 0; i < event.results.length; i++) {
            text += event.results[i][0].transcript;
          }
          if (text) {
            setInput(text);
          }
        };

        recognition.onerror = (event) => {
          console.warn("Speech recognition notice:", event.error);
          setIsRecording(false);
          if (event.error === "not-allowed") {
            setVoiceStatus("Microphone access denied. Please allow microphone permissions in browser.");
          } else if (event.error === "no-speech") {
            setVoiceStatus("No speech detected. Please click mic and try again.");
          } else {
            setVoiceStatus(`Microphone notice: ${event.error}`);
          }
          setTimeout(() => setVoiceStatus(""), 4500);
        };

        recognition.onend = () => {
          setIsRecording(false);
          setVoiceStatus("");
          speechRecognitionRef.current = null;
        };

        speechRecognitionRef.current = recognition;
        recognition.start();
        return;
      } catch (err) {
        console.warn("SpeechRecognition fallback to MediaRecorder:", err);
      }
    }

    // 2. Fallback: MediaRecorder + Groq Whisper
    if (
      !navigator.mediaDevices ||
      !navigator.mediaDevices.getUserMedia
    ) {

      setVoiceStatus(
        "Your browser does not support microphone recording."
      );
      setTimeout(() => setVoiceStatus(""), 4000);

      return;

    }


    try {

      getVoiceToken();


      setVoiceStatus(
        "Requesting microphone access..."
      );


      const stream =
        await navigator.mediaDevices
          .getUserMedia({
            audio: true
          });


      streamRef.current =
        stream;


      audioChunksRef.current =
        [];


      let mimeType =
        "audio/webm";


      if (
        MediaRecorder.isTypeSupported(
          "audio/webm;codecs=opus"
        )
      ) {

        mimeType =
          "audio/webm;codecs=opus";

      } else if (
        MediaRecorder.isTypeSupported(
          "audio/webm"
        )
      ) {

        mimeType =
          "audio/webm";

      } else if (
        MediaRecorder.isTypeSupported(
          "audio/ogg;codecs=opus"
        )
      ) {

        mimeType =
          "audio/ogg;codecs=opus";

      } else {

        mimeType =
          "";

      }


      const recorder =
        mimeType
          ? new MediaRecorder(
              stream,
              {
                mimeType
              }
            )
          : new MediaRecorder(
              stream
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


      recorder.onerror =
        (event) => {

          console.error(
            "MEDIA RECORDER ERROR:",
            event
          );

          setVoiceStatus(
            "Microphone recording failed."
          );
          setIsRecording(false);

        };


      recorder.onstop =
        async () => {

          try {

            const actualMimeType =
              recorder.mimeType ||
              mimeType ||
              "audio/webm";


            const audioBlob =
              new Blob(
                audioChunksRef.current,
                {
                  type:
                    actualMimeType
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
              "VOICE PROCESSING ERROR:",
              error
            );


            setVoiceStatus(
              `Voice input failed: ${error.message}`
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

      if (
        error.name ===
        "NotAllowedError"
      ) {

        setVoiceStatus(
          "Microphone permission was denied. Please allow microphone access in your browser."
        );

      } else if (
        error.name ===
        "NotFoundError"
      ) {

        setVoiceStatus(
          "No microphone was found."
        );

      } else {

        setVoiceStatus(
          `Unable to start microphone: ${error.message}`
        );

      }
      setTimeout(() => setVoiceStatus(""), 4500);

    }

  };


  // ============================================================
  // VOICE - STOP RECORDING
  // ============================================================

  const stopRecording = () => {

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch (err) {
        // ignore
      }
      speechRecognitionRef.current = null;
    }

    const recorder =
      mediaRecorderRef.current;


    if (recorder && recorder.state === "recording") {

      setIsRecording(false);

      setVoiceStatus(
        "Processing your voice..."
      );


      recorder.stop();

    } else {
      setIsRecording(false);
    }

  };


  // ============================================================
  // VOICE BUTTON
  // ============================================================

  const handleVoice = () => {

    if (loading) {
      return;
    }


    if (isRecording) {

      stopRecording();

    } else {

      startRecording();

    }

  };


  // ============================================================
  // LOGIN PAGE
  // ============================================================

  if (!isAuthenticated) {

    return (
      <AuthPage
        onLogin={
          handleLogin
        }
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

        .chat-area h1:first-child,
        .chat-area h2:first-child,
        .chat-area h3:first-child,
        .chat-area h4:first-child {
          margin-top: 0;
        }

        .chat-area > * {
          max-width: 100%;
        }
        /*
          CHAT SCROLL FIX
          ----------------------------------------------------------
          .chat-area is the only scrollable element. ChatWindow's
          original height/overflow rules are overridden here so the
          message list grows naturally and the outer chat area can
          always scroll to the newest message.
        */
        .chat-area .chat-window {
          width: 100% !important;
          height: auto !important;
          min-height: 0 !important;
          overflow: visible !important;
          display: block !important;
        }

        .chat-area .chat-window .messages {
          width: 100% !important;
          max-width: 980px !important;
          min-height: 0 !important;
          height: auto !important;
          margin: 0 auto !important;
          padding: 28px 24px 40px !important;
          box-sizing: border-box !important;
          overflow: visible !important;
        }

        /*
          CLEAN NEW-CHAT SCREEN
          ----------------------------------------------------------
          No Web Search / PDF / SQL / Image cards.
          The capabilities remain available through the composer
          and backend; they are simply not displayed as cards.
        */
        .drugassist-empty-state {
          width: 100%;
          min-height: 100%;
          box-sizing: border-box;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px 24px 120px;
        }

        .drugassist-empty-content {
          width: min(720px, 100%);
          text-align: center;
          margin-top: -80px;
        }

        .drugassist-empty-title {
          margin: 0 0 10px;
          font-size: clamp(30px, 4vw, 42px);
          line-height: 1.15;
          font-weight: 700;
          letter-spacing: -0.8px;
          color: #171717;
        }

        .drugassist-empty-subtitle {
          margin: 0;
          font-size: 16px;
          line-height: 1.6;
          color: #777b84;
        }

        @media (max-width: 900px) {
          .chat-area {
            padding-left: 20px !important;
            padding-right: 20px !important;
          }
        }
      `}</style>


      {/* Skip to content link (Item 12: A11y) */}
      <a href="#main-chat-area" className="skip-to-content">
        Skip to main content ↓
      </a>

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <Sidebar
        user={user}
        chats={conversations}
        activeChatId={currentConversationId}
        currentView={currentView}
        onNewChat={handleNewChat}
        onViewChat={handleOpenChat}
        onSelectChat={handleOpenConversation}
        onDeleteChat={handleDeleteChat}
        onLibrary={handleOpenLibrary}
        onLogout={handleLogout}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
        onOpenPrivacy={() => setShowPrivacy(true)}
        onOpenTerms={() => setShowTerms(true)}

        /* Keep these props for compatibility with the existing
           document-selection implementation. */
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleOpenConversation}
        uploadedFiles={uploadedFiles}
        uploadedDocuments={uploadedDocuments}
        selectedDocumentId={selectedDocumentId}
        onSelectDocument={handleSelectDocument}
        onDeleteDocument={handleDeleteDocument}
        onDeleteAllChats={handleDeleteAllConversations}
      />


      {/* ======================================================
          MAIN AREA
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
            onClick={() => setMobileOpen(true)}
            aria-label="Open sidebar"
          >
            <Menu size={18} />
          </button>

          <div className="mobile-brand">
            <Pill size={16} />
            <span>DrugAssist</span>
          </div>

          <div className="topbar-spacer" />

          <div className="topbar-actions">

            <button
              type="button"
              className="theme-button"
              onClick={toggleTheme}
              title={
                theme === "light"
                  ? "Switch to dark mode"
                  : "Switch to light mode"
              }
              aria-label={
                theme === "light"
                  ? "Switch to dark mode"
                  : "Switch to light mode"
              }
            >
              {theme === "light" ? (
                <Moon size={18} strokeWidth={2} />
              ) : (
                <Sun size={18} strokeWidth={2} />
              )}
            </button>

          </div>

        </header>

        {/* Scroll Progress Bar (Item 8) */}
        <div
          className="scroll-progress-bar"
          style={{ width: `${scrollProgress}%` }}
          aria-hidden="true"
        />


        {/* ====================================================
            CONTENT
        ==================================================== */}

        {currentView === "library" ? (
          <Library
            apiUrl={API_BASE_URL}
            token={localStorage.getItem("aura_token")}
            onBack={handleOpenChat}
            selectedDocumentId={selectedDocumentId}
            onSelectDocument={handleSelectDocument}
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
                <div className="welcome-logo" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
                    <rect x="2" y="2" width="20" height="20" rx="4" fill="#0f172a" />
                    <path d="M12 6v12" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
                    <path d="M6 12h12" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                </div>

                <h2>
                  Prescribing Information Assistant
                </h2>

                <p>
                  Grounded clinical drug intelligence with official citations. Query indications, dosages, contraindications, boxed warnings, and drug interactions directly from official labeling literature.
                </p>

                {/* Expandable Clinical FAQ (Item 19) */}
                <FAQAccordion />
              </div>
            )}

            {messages.length > 0 && (
              <ChatWindow
                messages={messages}
                loading={loading}
              />
            )}

            <div
              ref={chatEndRef}
              aria-hidden="true"
              style={{
                height: "1px",
                width: "100%"
              }}
            />

          </div>
        )}


        {/* ====================================================
            VOICE STATUS
        ==================================================== */}

        {currentView === "chat" && voiceStatus && (

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
            value={input}
            onChange={setInput}
            onSend={handleSend}
            onVoice={handleVoice}
            isRecording={isRecording}
            voiceStatus={voiceStatus}
            onFileUpload={handleFileUpload}
            pendingImage={pendingImage}
            pendingImagePreview={pendingImagePreview}
            onRemoveImage={removePendingImage}
            loading={loading}
            selectedDocumentName={
              selectedDocumentId ? selectedDocumentName : null
            }
            onChangeDocument={handleOpenLibrary}
            onClearDocument={() => {
              setSelectedDocumentId(null);
              setSelectedDocumentName("");
            }}
          />
        )}

      </section>

      {/* Floating Scroll-to-Top Button (Item 4) */}
      {showScrollTop && currentView === "chat" && (
        <button
          type="button"
          className="scroll-to-top-btn"
          onClick={handleScrollToTop}
          title="Scroll to top"
          aria-label="Scroll to top"
        >
          <ArrowUp size={18} strokeWidth={2.4} />
        </button>
      )}

      {showPrivacy && (
        <PrivacyPolicy onClose={() => setShowPrivacy(false)} />
      )}

      {showTerms && (
        <TermsAndConditions onClose={() => setShowTerms(false)} />
      )}



    </div>

  );

}


export default App;