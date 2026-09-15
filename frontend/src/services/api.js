const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

// =========================================================
// HELPERS
// =========================================================

export function getToken() {
  return (
    localStorage.getItem("token") ||
    localStorage.getItem("aura_token")
  );
}

export function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("aura_token");
  localStorage.removeItem("aura_user");
}

function authHeaders(extra = {}) {
  const token = getToken();

  return {
    ...extra,
    ...(token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {}),
  };
}

async function parseResponse(response) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      data?.detail ||
      data?.message ||
      data?.error ||
      `Request failed with status ${response.status}`;

    const detailStr =
      typeof detail === "string" ? detail : JSON.stringify(detail);

    // Only clear stored auth credentials on explicit session/token expiration,
    // NOT on invalid password during login or on server cold-boot / temporary errors
    if (
      response.status === 401 &&
      (detailStr.toLowerCase().includes("session expired") ||
        detailStr.toLowerCase().includes("invalid authentication token"))
    ) {
      clearAuth();
    }

    if (typeof detail === "string") {
      throw new Error(detail);
    }

    if (Array.isArray(detail)) {
      throw new Error(
        detail
          .map(
            (item) =>
              item?.msg || JSON.stringify(item)
          )
          .join(", ")
      );
    }

    throw new Error(JSON.stringify(detail));
  }

  return data;
}

// =========================================================
// AUTH
// =========================================================

export async function registerUser(
  name,
  email,
  password
) {
  const cleanEmail = (email || "").trim();
  const cleanName = (name || "").trim();

  const response = await fetch(
    `${API_BASE_URL}/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: cleanName,
        email: cleanEmail,
        password,
      }),
    }
  );

  const data = await parseResponse(response);

  const token = data?.access_token || data?.token || data?.jwt;
  if (token) {
    localStorage.setItem("token", token);
    localStorage.setItem("aura_token", token);
  }
  if (data?.user) {
    localStorage.setItem("aura_user", JSON.stringify(data.user));
  }
  if (cleanEmail) {
    localStorage.setItem("drugassist_last_email", cleanEmail);
  }

  return data;
}

export async function loginUser(
  email,
  password
) {
  const cleanId = (email || "").trim();
  const response = await fetch(
    `${API_BASE_URL}/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: cleanId,
        username: cleanId,
        password,
      }),
    }
  );

  const data = await parseResponse(response);

  const token = data?.access_token || data?.token || data?.jwt;
  if (token) {
    localStorage.setItem("token", token);
    localStorage.setItem("aura_token", token);
  }
  if (data?.user) {
    localStorage.setItem("aura_user", JSON.stringify(data.user));
  } else if (cleanId) {
    localStorage.setItem(
      "aura_user",
      JSON.stringify({
        email: cleanId,
      })
    );
  }
  if (cleanId) {
    localStorage.setItem("drugassist_last_email", cleanId);
  }

  return data;
}

export async function getCurrentUser() {
  const response = await fetch(
    `${API_BASE_URL}/me`,
    {
      method: "GET",
      headers: authHeaders(),
    }
  );

  return parseResponse(response);
}

export async function logoutUser() {
  try {
    const response = await fetch(
      `${API_BASE_URL}/logout`,
      {
        method: "POST",
        headers: authHeaders(),
      }
    );

    const data = await parseResponse(response);

    clearAuth();

    return data;
  } catch (error) {
    clearAuth();
    throw error;
  }
}

// =========================================================
// CHATS / CONVERSATIONS
// =========================================================

export async function getConversations() {
  const response = await fetch(
    `${API_BASE_URL}/chats`,
    {
      method: "GET",
      headers: authHeaders(),
    }
  );

  const data = await parseResponse(response);

  return data?.chats || [];
}

export async function createConversation(
  title = "New Chat"
) {
  const response = await fetch(
    `${API_BASE_URL}/chats`,
    {
      method: "POST",
      headers: authHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify({
        title,
      }),
    }
  );

  return parseResponse(response);
}

export async function getConversation(
  chatId
) {
  const response = await fetch(
    `${API_BASE_URL}/chats/${chatId}`,
    {
      method: "GET",
      headers: authHeaders(),
    }
  );

  return parseResponse(response);
}

// =========================================================
// CHAT HISTORY
// =========================================================

export async function getChatHistory(
  chatId
) {
  const data = await getConversation(chatId);

  return data?.messages || [];
}

// =========================================================
// RENAME CHAT
// =========================================================

export async function renameConversation(
  chatId,
  title
) {
  const response = await fetch(
    `${API_BASE_URL}/chats/${chatId}`,
    {
      method: "PATCH",
      headers: authHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify({
        title,
      }),
    }
  );

  return parseResponse(response);
}

// =========================================================
// DELETE CHAT
// =========================================================

export async function deleteConversation(
  chatId
) {
  const response = await fetch(
    `${API_BASE_URL}/chats/${chatId}`,
    {
      method: "DELETE",
      headers: authHeaders(),
    }
  );

  return parseResponse(response);
}

// =========================================================
// DELETE ALL CHATS
// =========================================================

export async function deleteAllConversations() {
  const conversations =
    await getConversations();

  await Promise.all(
    conversations.map((chat) =>
      deleteConversation(chat.id)
    )
  );

  return {
    success: true,
  };
}

// =========================================================
// DOCUMENTS
// =========================================================

export async function getDocuments() {
  const response = await fetch(
    `${API_BASE_URL}/documents`,
    {
      method: "GET",
      headers: authHeaders(),
    }
  );

  return parseResponse(response);
}

export async function deleteDocument(
  documentId
) {
  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}`,
    {
      method: "DELETE",
      headers: authHeaders(),
    }
  );

  return parseResponse(response);
}

// =========================================================
// OPEN AUTHENTICATED PDF
// =========================================================

export async function getDocumentPDF(
  documentId
) {
  const token = getToken();

  if (!token) {
    throw new Error(
      "You are not logged in."
    );
  }

  if (!documentId) {
    throw new Error(
      "Missing document ID."
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/documents/${documentId}/pdf`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 401) {
    clearAuth();

    throw new Error(
      "Your session has expired. Please log in again."
    );
  }

  if (!response.ok) {
    let message =
      "Unable to open PDF.";

    try {
      const data =
        await response.json();

      message =
        data?.detail ||
        data?.message ||
        message;
    } catch {
      // Ignore JSON parsing failure
    }

    throw new Error(message);
  }

  const blob =
    await response.blob();

  if (
    blob.type &&
    blob.type !== "application/pdf"
  ) {
    throw new Error(
      "The server did not return a PDF file."
    );
  }

  return blob;
}

// =========================================================
// DELETE PDF
// =========================================================

export async function deletePDF(
  documentId
) {
  return deleteDocument(documentId);
}

// =========================================================
// PDF UPLOAD
// =========================================================

export async function uploadPDF(file) {
  if (!file) {
    throw new Error(
      "No PDF file selected."
    );
  }

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_BASE_URL}/upload-pdf`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    }
  );

  return parseResponse(response);
}

// =========================================================
// MAIN CHAT
// =========================================================

export async function askAURA(
  question,
  conversationId = null,
  documentId = null
) {
  const formData =
    new FormData();

  formData.append(
    "question",
    question || ""
  );

  if (
    conversationId !== null &&
    conversationId !== undefined
  ) {
    formData.append(
      "chat_id",
      String(conversationId)
    );
  }

  if (
    documentId !== null &&
    documentId !== undefined
  ) {
    formData.append(
      "document_id",
      String(documentId)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/chat`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    }
  );

  return parseResponse(response);
}

// =========================================================
// VOICE CHAT
// =========================================================

export async function askWithVoice(
  audioFile,
  question = "",
  conversationId = null,
  documentId = null
) {
  // Support both:
  // (audio, question, chatId)
  // and
  // (audio, chatId)

  if (
    typeof question === "number" ||
    (
      typeof question === "string" &&
      question !== "" &&
      !isNaN(Number(question)) &&
      conversationId === null
    )
  ) {
    conversationId = question;
    question = "";
  }

  const formData =
    new FormData();

  if (audioFile) {
    formData.append(
      "audio",
      audioFile
    );
  }

  formData.append(
    "question",
    question || ""
  );

  if (
    conversationId !== null &&
    conversationId !== undefined
  ) {
    formData.append(
      "chat_id",
      String(conversationId)
    );
  }

  if (
    documentId !== null &&
    documentId !== undefined
  ) {
    formData.append(
      "document_id",
      String(documentId)
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/voice-ask`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    }
  );

  return parseResponse(response);
}

// =========================================================
// VOICE COMPATIBILITY
// =========================================================

export async function voiceAsk(
  audioFile,
  question = "",
  conversationId = null,
  documentId = null
) {
  return askWithVoice(
    audioFile,
    question,
    conversationId,
    documentId
  );
}

// =========================================================
// LEGACY / GENERAL ASK
// =========================================================

export async function askQuestion(
  question,
  conversationId = null,
  documentId = null
) {
  const response = await fetch(
    `${API_BASE_URL}/ask`,
    {
      method: "POST",
      headers: authHeaders({
        "Content-Type": "application/json",
      }),
      body: JSON.stringify({
        question,
        conversation_id:
          conversationId,
        document_id:
          documentId,
      }),
    }
  );

  return parseResponse(response);
}

// =========================================================
// HEALTH CHECK
// =========================================================

export async function healthCheck() {
  const response = await fetch(
    `${API_BASE_URL}/health`,
    {
      method: "GET",
    }
  );

  return parseResponse(response);
}

// =========================================================
// DEFAULT EXPORT
// =========================================================

export default {
  // Auth
  registerUser,
  loginUser,
  getCurrentUser,
  logoutUser,
  clearAuth,
  getToken,

  // Chats
  getConversations,
  createConversation,
  getConversation,
  getChatHistory,
  renameConversation,
  deleteConversation,
  deleteAllConversations,

  // Documents
  getDocuments,
  deleteDocument,
  deletePDF,
  uploadPDF,
  getDocumentPDF,

  // Chat
  askAURA,
  askImage,
  askWithImage,
  askWithVoice,
  voiceAsk,
  askQuestion,

  // Health
  healthCheck,
};