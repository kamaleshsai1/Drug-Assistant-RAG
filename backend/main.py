import os
import sys

# Ensure backend directory is in python path for Antigravity IDE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Limit internal math/ONNX thread pools for low memory footprint on Render
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["ORT_MAX_THREAD_COUNT"] = "1"
os.environ["ONNXRUNTIME_EXECUTION_PROVIDERS"] = "CPUExecutionProvider"

import shutil
import uuid
import traceback
import json
import hashlib

from fastapi import (
    FastAPI,
    HTTPException,
    UploadFile,
    File,
    Depends,
    Form,
    Request,
)
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from starlette.concurrency import run_in_threadpool

from console import (
    render_backend_console,
    render_health_page,
    render_privacy_page,
    render_terms_page,
    get_privacy_data,
    get_terms_data,
    FAVICON_SVG,
)

from typing import Optional

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, EmailStr

from rag import (
    answer_question,
    analyze_uploaded_image,
)

from pinecone_db import index_pdf

from database.database import (
    init_database,
    create_user,
    get_user_by_email,
    create_chat,
    get_user_chats,
    get_chat,
    get_document,
    delete_chat,
    update_chat_title,
    touch_chat,
    add_message,
    get_messages,
    create_document,
    get_user_documents,
    delete_document,
    get_user_memories,
    upsert_memory,
)


from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="DrugAssist API",
    description="Evidence-first Drug Information RAG Chatbot",
    version="4.0.0",
)


# ============================================================
# CORS
# ============================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://drug-assist-agentic-rag-1.onrender.com",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
)

PDF_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "pdfs",
)

IMAGE_FOLDER = os.path.join(
    UPLOAD_FOLDER,
    "images",
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True,
)

os.makedirs(
    PDF_FOLDER,
    exist_ok=True,
)

os.makedirs(
    IMAGE_FOLDER,
    exist_ok=True,
)


# ============================================================
# TRUSTED MEDICAL PDF REGISTRY & VERIFICATION
# ============================================================

TRUSTED_PDF_REGISTRY = {
    "9f0524388a03e816a19d05845b3a4dce5d6e8b8ba54755480bc1d8ddf2f9d300": {
        "name": "Official RINVOQ Prescribing Information (AbbVie/FDA labeling)",
        "source": "AbbVie/FDA labeling",
        "official_url": "https://www.rxabbvie.com/pdf/rinvoq_pi.pdf",
    },
    "e4bf4bfa91a77b8f6d6cc0b18f3a43910dbf27f031181bc6476ee62917affa20": {
        "name": "Official RINVOQ Prescribing Information (AbbVie/FDA labeling)",
        "source": "AbbVie/FDA labeling",
        "official_url": "https://www.rxabbvie.com/pdf/rinvoq_pi.pdf",
    },
    "49186dafe21cc9c76cf3db949da45149e612cf11354ad50f70c17e5a860b68be": {
        "name": "LOSARTAN POTASSIUM Tablets (FDA labeling)",
        "source": "FDA Prescribing Information",
        "official_url": "https://dailymed.nlm.nih.gov/",
    },
    "6d65738981b232e5ffd674790dbc97bffbef4c3dc69f46faaa7839bf5419242a": {
        "name": "ALLEROFF Prescribing Information",
        "source": "Official Product Monograph",
        "official_url": "https://dailymed.nlm.nih.gov/",
    },
}


def verify_trusted_pdf(file_path):
    """
    Allow a PDF into the medical RAG when its exact hash is approved
    OR when authenticated as genuine regulatory prescribing information.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as pdf_file:
        for chunk in iter(lambda: pdf_file.read(1024 * 1024), b""):
            sha256.update(chunk)

    file_hash = sha256.hexdigest()
    trusted_source = TRUSTED_PDF_REGISTRY.get(file_hash)

    if trusted_source:
        return {
            "trusted": True,
            "sha256": file_hash,
            **trusted_source,
        }

    # Dynamic clinical verification via structural and vocabulary analysis
    try:
        from pdf_authenticator import authenticate_pdf_document
        auth_result = authenticate_pdf_document(file_path)

        if auth_result.get("is_authentic"):
            doc_name = os.path.basename(file_path)
            return {
                "trusted": True,
                "sha256": file_hash,
                "name": doc_name,
                "source": "Verified Clinical Prescribing Information (FDA/EMA)",
                "official_url": "https://dailymed.nlm.nih.gov/",
            }
        else:
            raise HTTPException(
                status_code=403,
                detail=(
                    auth_result.get("detail")
                    or "PDF rejected. This document is not a verified trusted medical source. "
                    "Only approved official medical documents can be added to DrugAssist."
                ),
            )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=403,
            detail=(
                "PDF rejected. This document is not a verified trusted medical source. "
                "Only approved official medical documents can be added to DrugAssist."
            ),
        )


# ============================================================
# ALLOWED IMAGE TYPES
# ============================================================

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".jfif",
}


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():

    # Initialize SQLite database and create
    # all required tables if they do not exist.
    init_database()

    print()
    print("=" * 70)
    print("DRUGASSIST API")
    print("=" * 70)
    print("Database initialized.")
    print("Authentication enabled.")
    print("RAG engine loaded.")
    print("PDF upload enabled.")
    print("Image analysis enabled.")
    print("=" * 70)

# ============================================================
# REQUEST MODELS
# ============================================================

class RegisterRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class ChatCreateRequest(BaseModel):
    title: str = "New chat"


class ChatRenameRequest(BaseModel):
    title: str


class AskRequest(BaseModel):
    question: str


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health(request: Request):

    accept = request.headers.get("accept", "").lower()
    format_param = request.query_params.get("format", "").lower()

    if format_param == "json" or (
        "application/json" in accept and "text/html" not in accept
    ):
        return JSONResponse(
            content={
                "status": "healthy",
                "message": "DrugAssist API is running",
                "version": "4.0.0",
            }
        )

    return HTMLResponse(
        content=render_health_page(),
        status_code=200,
    )


# ============================================================
# ROOT & CONSOLE
# ============================================================

@app.get("/")
def root(request: Request):

    accept = request.headers.get("accept", "").lower()
    format_param = request.query_params.get("format", "").lower()

    if format_param == "json" or (
        "application/json" in accept and "text/html" not in accept
    ):
        return JSONResponse(
            content={
                "name": "DrugAssist",
                "description": (
                    "Evidence-first drug information "
                    "assistant with multimodal RAG"
                ),
                "status": "running",
                "version": "4.0.0",
            }
        )

    return HTMLResponse(
        content=render_backend_console(),
        status_code=200,
    )


@app.get("/privacy")
def privacy(request: Request):

    accept = request.headers.get("accept", "").lower()
    format_param = request.query_params.get("format", "").lower()

    if format_param == "json" or (
        "application/json" in accept and "text/html" not in accept
    ):
        return JSONResponse(content=get_privacy_data())

    return HTMLResponse(
        content=render_privacy_page(),
        status_code=200,
    )


@app.get("/terms")
def terms(request: Request):

    accept = request.headers.get("accept", "").lower()
    format_param = request.query_params.get("format", "").lower()

    if format_param == "json" or (
        "application/json" in accept and "text/html" not in accept
    ):
        return JSONResponse(content=get_terms_data())

    return HTMLResponse(
        content=render_terms_page(),
        status_code=200,
    )


@app.get("/favicon.ico")
def favicon():

    return Response(
        content=FAVICON_SVG,
        media_type="image/svg+xml",
    )


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register(
    request: RegisterRequest,
):

    raw_name = request.name or request.username or ""
    name = raw_name.strip()

    email = (
        str(request.email)
        .strip()
        .lower()
    )

    password = request.password

    if not name:

        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty.",
        )

    if len(name) < 2:

        raise HTTPException(
            status_code=400,
            detail="Name must contain at least 2 characters.",
        )

    if len(password) < 6:

        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain "
                "at least 6 characters."
            ),
        )

    existing_user = get_user_by_email(
        email
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this "
                "email already exists."
            ),
        )

    password_hash = hash_password(
        password
    )

    user_id = create_user(
        name=name,
        email=email,
        password_hash=password_hash,
    )

    token = create_access_token(
        user_id
    )

    return {
        "success": True,
        "message": "Registration successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": name,
            "email": email,
        },
    }


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    request: LoginRequest,
):

    login_id = (
        str(request.email or request.username or "")
        .strip()
        .lower()
    )

    password = request.password

    if not login_id:
        raise HTTPException(
            status_code=400,
            detail="Email or username is required.",
        )

    user = get_user_by_email(
        login_id
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    valid_password = verify_password(
        password,
        user["password_hash"],
    )

    if not valid_password:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user["id"]
    )

    return {
        "success": True,
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

@app.get("/me")
def me(
    user=Depends(get_current_user),
):

    return {
        "success": True,
        "user": user,
    }


# ============================================================
# LOGOUT
# ============================================================

@app.post("/logout")
def logout(
    user=Depends(get_current_user),
):

    return {
        "success": True,
        "message": "Logged out successfully.",
    }


# ============================================================
# GET USER CHATS
# ============================================================

@app.get("/chats")
def get_chats(
    user=Depends(get_current_user),
):

    user_chats = get_user_chats(
        user["id"]
    )

    return {
        "success": True,
        "chats": user_chats,
    }


# ============================================================
# CREATE NEW CHAT
# ============================================================

@app.post("/chats")
def create_new_chat(
    request: ChatCreateRequest,
    user=Depends(get_current_user),
):

    title = (
        request.title.strip()
        or "New chat"
    )

    chat_id = create_chat(
        user["id"],
        title,
    )

    return {
        "success": True,
        "chat_id": chat_id,
        "title": title,
    }


# ============================================================
# RENAME CHAT
# ============================================================

@app.patch("/chats/{chat_id}")
def rename_chat(
    chat_id: int,
    request: ChatRenameRequest,
    user=Depends(get_current_user),
):

    title = request.title.strip()

    if not title:

        raise HTTPException(
            status_code=400,
            detail="Chat title cannot be empty.",
        )

    chat = get_chat(
        chat_id,
        user["id"],
    )

    if not chat:

        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    try:

        update_chat_title(
            chat_id,
            user["id"],
            title,
        )

    except TypeError:

        try:

            update_chat_title(
                chat_id,
                title,
            )

        except Exception as error:

            raise HTTPException(
                status_code=500,
                detail=str(error),
            )

    return {
        "success": True,
        "chat_id": chat_id,
        "title": title,
    }


# ============================================================
# GET SINGLE CHAT
# ============================================================

@app.get("/chats/{chat_id}")
def get_single_chat(
    chat_id: int,
    user=Depends(get_current_user),
):

    chat = get_chat(
        chat_id,
        user["id"],
    )

    if not chat:

        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    messages = get_messages(
        chat_id
    )

    formatted_messages = []

    for message in messages:

        # --------------------------------------------
        # SOURCES
        # --------------------------------------------

        try:

            sources = json.loads(
                message.get(
                    "sources_json",
                    "[]",
                )
            )

        except Exception:

            sources = []

        # --------------------------------------------
        # VIDEOS
        # --------------------------------------------

        try:

            videos = json.loads(
                message.get(
                    "videos_json",
                    "[]",
                )
            )

        except Exception:

            videos = []

        # --------------------------------------------
        # ATTACHMENTS
        # --------------------------------------------

        try:

            attachments = json.loads(
                message.get(
                    "attachments_json",
                    "[]",
                )
            )

        except Exception:

            attachments = []

        # --------------------------------------------
        # EVIDENCE
        # --------------------------------------------

        try:

            evidence = json.loads(
                message.get(
                    "evidence_json",
                    "[]",
                )
            )

        except Exception:

            evidence = []

        formatted_messages.append(
            {
                "id": message["id"],
                "role": message["role"],
                "content": message["content"],
                "sources": sources,
                "videos": videos,
                "attachments": attachments,
                "evidence": evidence,
                "confidence": message.get(
                    "confidence"
                ),
                "grounding_score": message.get(
                    "grounding_score"
                ),
                "mode": message.get(
                    "mode"
                ),
                "image_analysis": message.get(
                    "image_analysis"
                ),
                "created_at": message["created_at"],
            }
        )

    return {
        "success": True,
        "chat": chat,
        "messages": formatted_messages,
    }


# ============================================================
# DELETE CHAT
# ============================================================

@app.delete("/chats/{chat_id}")
def remove_chat(
    chat_id: int,
    user=Depends(get_current_user),
):

    deleted = delete_chat(
        chat_id,
        user["id"],
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Chat not found.",
        )

    return {
        "success": True,
        "message": "Chat deleted successfully.",
    }


# ============================================================
# LIBRARY - GET DOCUMENTS
# ============================================================

@app.get("/documents")
def documents(
    user=Depends(get_current_user),
):

    user_documents = get_user_documents(
        user["id"]
    )

    return {
        "success": True,
        "documents": user_documents,
    }

@app.get("/documents/{document_id}/pdf")
def get_document_pdf(
    document_id: int,
    user=Depends(get_current_user),
):

    document = get_document(
        document_id,
        user["id"],
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if str(document.get("file_type", "")).lower() != "pdf":
        raise HTTPException(
            status_code=400,
            detail="Document is not a PDF.",
        )

    file_path = os.path.realpath(
        document.get("file_path", "")
    )

    pdf_root = os.path.realpath(
        PDF_FOLDER
    )

    if os.path.commonpath(
        [file_path, pdf_root]
    ) != pdf_root:
        raise HTTPException(
            status_code=403,
            detail="Invalid document path.",
        )

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found.",
        )

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=document.get("filename") or os.path.basename(file_path),
    )
# ============================================================
# LIBRARY - DELETE DOCUMENT
# ============================================================

@app.delete("/documents/{document_id}")
def remove_document(
    document_id: int,
    user=Depends(get_current_user),
):

    deleted = delete_document(
        document_id,
        user["id"],
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "success": True,
        "message": "Document removed from library.",
    }


# ============================================================
# BASIC ASK ENDPOINT
# ============================================================

@app.post("/ask")
def ask(
    request: AskRequest,
    user=Depends(get_current_user),
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:

        user_memories = get_user_memories(
            user["id"]
        )

        result = answer_question(
            question,
            conversation_history=[],
            memories=user_memories,
            user_id=user["id"],
            chat_id=None,
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {}

        return {
            "success": result.get(
                "success",
                True,
            ),
            "question": question,
            "answer": result.get(
                "answer",
                "",
            ),
            "sources": result.get(
                "sources",
                [],
            ),
            "videos": result.get(
                "videos",
                [],
            ),
            "confidence": result.get(
                "confidence",
                {
                    "label": "not_applicable",
                    "score": 0.0,
                    "grounding_score": 0.0,
                },
            ),
            "grounding_score": result.get(
                "grounding_score",
                0.0,
            ),
            "evidence": result.get(
                "evidence",
                [],
            ),
            "image_analysis": result.get(
                "image_analysis",
                "",
            ),
        }

    except Exception as error:

        print()
        print("=" * 70)
        print("ASK ERROR")
        print("=" * 70)
        print(repr(error))
        traceback.print_exc()
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail="Unable to process the question.",
        )


# ============================================================
# SAVE PDF DOCUMENT
# ============================================================

def save_pdf_document(
    user_id,
    filename,
    file_path,
    stored_filename,
    upload_result,
):

    upload_result = (
        upload_result
        if isinstance(upload_result, dict)
        else {}
    )

    drug = upload_result.get(
        "drug"
    )

    source = upload_result.get(
        "source"
    )

    document_key = upload_result.get(
        "document_id"
    )

    pages = upload_result.get(
        "pages"
    )

    chunks = upload_result.get(
        "chunks"
    )

    # --------------------------------------------------------
    # New database schema
    # --------------------------------------------------------

    try:

        return create_document(
            user_id=user_id,
            filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type="pdf",
            drug=drug,
            source=source,
            document_id=document_key,
            pages=pages,
            chunks=chunks,
        )

    except TypeError:

        pass

    # --------------------------------------------------------
    # Older database schema compatibility
    # --------------------------------------------------------

    try:

        return create_document(
            user_id=user_id,
            filename=filename,
            drug=drug,
            source=source,
            document_id=document_key,
            pages=pages,
            chunks=chunks,
        )

    except TypeError:

        pass

    # --------------------------------------------------------
    # Minimal compatibility
    # --------------------------------------------------------

    return create_document(
        user_id,
        filename,
        stored_filename,
        file_path,
    )


# ============================================================
# SAVE IMAGE DOCUMENT
# ============================================================

def save_image_document(
    user_id,
    filename,
    file_path,
    stored_filename,
):

    # --------------------------------------------------------
    # New database schema
    # --------------------------------------------------------

    try:

        return create_document(
            user_id=user_id,
            filename=filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type="image",
            drug=None,
            source="Uploaded Image",
            document_id=str(
                uuid.uuid4()
            ),
            pages=1,
            chunks=0,
        )

    except TypeError:

        pass

    # --------------------------------------------------------
    # Older database compatibility
    # --------------------------------------------------------

    try:

        return create_document(
            user_id=user_id,
            filename=filename,
            drug=None,
            source="Uploaded Image",
            document_id=str(
                uuid.uuid4()
            ),
            pages=1,
            chunks=0,
        )

    except TypeError:

        pass

    return create_document(
        user_id,
        filename,
        stored_filename,
        file_path,
    )


# ============================================================
# PDF UPLOAD
# ============================================================

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    original_filename = os.path.basename(
        file.filename
    )

    if not original_filename.lower().endswith(
        ".pdf"
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    stored_filename = (
        str(uuid.uuid4())
        + "_"
        + original_filename
    )

    file_path = os.path.join(
        PDF_FOLDER,
        stored_filename,
    )

    try:

        with open(
            file_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

        print()
        print("=" * 70)
        print("PDF UPLOAD")
        print("=" * 70)
        print(
            "USER:",
            user["email"],
        )
        print(
            "FILENAME:",
            original_filename,
        )

        # ----------------------------------------------------
        # VERIFY TRUSTED MEDICAL SOURCE
        # ----------------------------------------------------

        verify_trusted_pdf(file_path)

        # ----------------------------------------------------
        # INDEX PDF
        # ----------------------------------------------------

        result = await run_in_threadpool(
            index_pdf,
            file_path,
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {}

        # ----------------------------------------------------
        # SAVE LIBRARY RECORD
        # ----------------------------------------------------

        document_id = save_pdf_document(
            user["id"],
            original_filename,
            file_path,
            stored_filename,
            result,
        )

        print(
            "DOCUMENT ID:",
            document_id,
        )

        print("=" * 70)

        return {
            "success": True,
            "message": (
                "PDF uploaded and "
                "indexed successfully."
            ),
            "filename": original_filename,
            "stored_filename": stored_filename,
            "document_id": document_id,
            "drug": result.get(
                "drug"
            ),
            "source": result.get(
                "source"
            ),
            "pages": result.get(
                "pages"
            ),
            "chunks": result.get(
                "chunks"
            ),
        }

    except Exception as error:

        print()
        print("=" * 70)
        print("PDF UPLOAD ERROR")
        print("=" * 70)
        print(
            repr(error)
        )
        traceback.print_exc()
        print("=" * 70)

        if os.path.exists(
            file_path
        ):

            try:

                os.remove(
                    file_path
                )

            except Exception:

                pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process PDF: "
                + str(error)
            ),
        )

    finally:

        await file.close()


# ============================================================
# IMAGE VALIDATION
# ============================================================

def validate_image_file(
    filename,
    content_type,
):

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension in ALLOWED_IMAGE_EXTENSIONS:

        return True

    if (
        content_type
        and content_type.lower().startswith(
            "image/"
        )
    ):

        return True

    return False


# ============================================================
# CONVERSATION IMAGE MEMORY
# ============================================================

def get_previous_image_context(
    messages,
):

    if not messages:

        return ""

    image_seen = False

    for message in reversed(
        messages
    ):

        role = message.get(
            "role",
            "",
        )

        content = str(
            message.get(
                "content",
                "",
            )
        )

        if role == "user":

            lower_content = content.lower()

            attachment_marker = (
                "attachments:"
            )

            if attachment_marker in lower_content:

                attachment_part = (
                    lower_content.split(
                        attachment_marker,
                        1,
                    )[1]
                )

                if any(
                    attachment_part.endswith(
                        ext
                    )
                    or f"{ext}," in attachment_part
                    or f"{ext} " in attachment_part
                    for ext in ALLOWED_IMAGE_EXTENSIONS
                ):

                    image_seen = True
                    continue

                # A later PDF attachment means the
                # previous image is no longer active.

                if ".pdf" in attachment_part:

                    return ""

        elif (
            role == "assistant"
            and image_seen
        ):

            if content.strip():

                return (
                    "Previous image analysis "
                    "from this conversation:\n"
                    + content.strip()
                )

    return ""



# ============================================================
# CONVERSATION MEMORY HELPERS
# ============================================================

def build_conversation_history(messages, max_messages=12):
    """Convert stored chat messages into LLM conversation history.

    The current user message is not included here because this helper
    is called before the new user message is saved.
    """
    history = []

    if not messages:
        return history

    for message in messages[-max_messages:]:
        if not isinstance(message, dict):
            continue

        role = message.get("role")

        if role not in {"user", "assistant"}:
            continue

        content = (
            message.get("content")
            or ""
        )

        if not str(content).strip():
            continue

        history.append(
            {
                "role": role,
                "content": str(content).strip(),
            }
        )

    return history


def get_long_term_memory_for_user(user_id):
    """Safely load persistent memories for the authenticated user."""
    try:
        memories = get_user_memories(user_id)

        if isinstance(memories, list):
            return memories

    except Exception as error:
        print(
            "LONG-TERM MEMORY LOAD ERROR:",
            repr(error),
        )
        traceback.print_exc()

    return []


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat")
async def chat(

    question: str = Form(""),

    chat_id: int | None = Form(None),

    document_id: int | None = Form(None),

    files: list[UploadFile] | None = File(None),

    user=Depends(get_current_user),

):

    question = question.strip()

    # ========================================================
    # VALIDATION
    # ========================================================

    if not question and not files:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please enter a question "
                "or attach a file."
            ),
        )

    user_id = user["id"]

    # ========================================================
    # GET OR CREATE CHAT
    # ========================================================

    current_chat_id = chat_id

    if current_chat_id is not None:

        chat_record = get_chat(
            current_chat_id,
            user_id,
        )

        if not chat_record:

            raise HTTPException(
                status_code=404,
                detail="Chat not found.",
            )

    else:

        title = (
            question[:60]
            if question
            else "New chat"
        )

        current_chat_id = create_chat(
            user_id,
            title,
        )

    # ========================================================
    # RESOLVE SELECTED LIBRARY DOCUMENT
    # ========================================================
    # document_id is the SQLite documents.id sent by the frontend.
    # Pinecone uses the separate documents.document_id value, so
    # resolve it here before calling the RAG layer.
    selected_rag_document_id = None

    if document_id is not None:
        selected_document = get_document(
            document_id,
            user_id,
        )

        if not selected_document:
            raise HTTPException(
                status_code=404,
                detail="Selected document not found.",
            )

        if selected_document.get("file_type") != "pdf":
            raise HTTPException(
                status_code=400,
                detail="Only PDF documents can be used for drug questions.",
            )

        selected_rag_document_id = selected_document.get(
            "document_id"
        )

        if not selected_rag_document_id:
            raise HTTPException(
                status_code=500,
                detail="Selected document is missing its RAG document ID.",
            )

    # ========================================================
    # PROCESS ATTACHMENTS
    # ========================================================

    processed_files = []

    image_contexts = []

    if files:

        for uploaded_file in files:

            if not uploaded_file.filename:

                continue

            filename = os.path.basename(
                uploaded_file.filename
            )

            extension = os.path.splitext(
                filename
            )[1].lower()

            # ==================================================
            # PDF
            # ==================================================

            if extension == ".pdf":

                stored_filename = (
                    str(uuid.uuid4())
                    + "_"
                    + filename
                )

                file_path = os.path.join(
                    PDF_FOLDER,
                    stored_filename,
                )

                try:

                    with open(
                        file_path,
                        "wb",
                    ) as buffer:

                        shutil.copyfileobj(
                            uploaded_file.file,
                            buffer,
                        )

                    print()
                    print("=" * 70)
                    print("CHAT PDF ATTACHMENT")
                    print("=" * 70)
                    print(
                        "USER:",
                        user["email"],
                    )
                    print(
                        "FILENAME:",
                        filename,
                    )
                    print(
                        "CHAT ID:",
                        current_chat_id,
                    )

                    # ------------------------------------------
                    # VERIFY TRUSTED MEDICAL SOURCE
                    # ------------------------------------------

                    verify_trusted_pdf(file_path)

                    # ------------------------------------------
                    # INDEX PDF
                    # ------------------------------------------

                    upload_result = await run_in_threadpool(
                        index_pdf,
                        file_path,
                    )

                    if not isinstance(
                        upload_result,
                        dict,
                    ):

                        upload_result = {}

                    # ------------------------------------------
                    # SAVE LIBRARY RECORD
                    # ------------------------------------------

                    database_document_id = save_pdf_document(
                        user_id,
                        filename,
                        file_path,
                        stored_filename,
                        upload_result,
                    )

                    # If the PDF was attached directly to this chat request,
                    # use its Pinecone document ID for this question.
                    selected_rag_document_id = upload_result.get(
                        "document_id"
                    ) or selected_rag_document_id

                    processed_files.append(
                        {
                            "filename": filename,
                            "type": "pdf",
                            "status": "indexed",
                            "document_id": database_document_id,
                            "drug": upload_result.get(
                                "drug"
                            ),
                            "source": upload_result.get(
                                "source"
                            ),
                            "pages": upload_result.get(
                                "pages"
                            ),
                            "chunks": upload_result.get(
                                "chunks"
                            ),
                        }
                    )

                    print(
                        "PDF indexed successfully."
                    )
                    print("=" * 70)

                except Exception as error:

                    print()
                    print(
                        "CHAT PDF ERROR:",
                        repr(error),
                    )

                    traceback.print_exc()

                    if os.path.exists(
                        file_path
                    ):

                        try:

                            os.remove(
                                file_path
                            )

                        except Exception:

                            pass

                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"Unable to process PDF "
                            f"'{filename}': "
                            f"{str(error)}"
                        ),
                    )

                finally:

                    await uploaded_file.close()

            # ==================================================
            # IMAGE
            # ==================================================

            elif validate_image_file(
                filename,
                uploaded_file.content_type,
            ):

                stored_filename = (
                    str(uuid.uuid4())
                    + "_"
                    + filename
                )

                file_path = os.path.join(
                    IMAGE_FOLDER,
                    stored_filename,
                )

                try:

                    print()
                    print("=" * 70)
                    print("CHAT IMAGE ATTACHMENT")
                    print("=" * 70)
                    print(
                        "USER:",
                        user["email"],
                    )
                    print(
                        "FILENAME:",
                        filename,
                    )
                    print(
                        "CHAT ID:",
                        current_chat_id,
                    )

                    # ------------------------------------------
                    # SAVE IMAGE
                    # ------------------------------------------

                    with open(
                        file_path,
                        "wb",
                    ) as buffer:

                        shutil.copyfileobj(
                            uploaded_file.file,
                            buffer,
                        )

                    # ------------------------------------------
                    # ANALYZE IMAGE
                    # ------------------------------------------

                    image_observation = (
                        analyze_uploaded_image(
                            file_path,
                            question=question,
                        )
                    )

                    if image_observation:

                        image_contexts.append(
                            image_observation
                        )

                    # ------------------------------------------
                    # SAVE IMAGE TO LIBRARY
                    # ------------------------------------------

                    document_id = save_image_document(
                        user_id,
                        filename,
                        file_path,
                        stored_filename,
                    )

                    processed_files.append(
                        {
                            "filename": filename,
                            "type": "image",
                            "status": (
                                "analyzed"
                                if image_observation
                                else "analysis_failed"
                            ),
                            "document_id": document_id,
                            "analysis": (
                                image_observation
                                or ""
                            ),
                        }
                    )

                    print(
                        "Image analysis completed."
                    )
                    print("=" * 70)

                except Exception as error:

                    print()
                    print(
                        "CHAT IMAGE ERROR:",
                        repr(error),
                    )

                    traceback.print_exc()

                    processed_files.append(
                        {
                            "filename": filename,
                            "type": "image",
                            "status": "analysis_failed",
                            "error": str(error),
                        }
                    )

                finally:

                    await uploaded_file.close()

            # ==================================================
            # UNSUPPORTED
            # ==================================================

            else:

                await uploaded_file.close()

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported file type: "
                        f"{filename}"
                    ),
                )

    # ========================================================
    # COMBINE IMAGE OBSERVATIONS
    # ========================================================

    combined_image_context = ""

    if image_contexts:

        combined_image_context = (
            "\n\n".join(
                image_contexts
            )
        )

    # ========================================================
    # GET EXISTING MESSAGES
    # ========================================================

    previous_messages = get_messages(
        current_chat_id
    )


    # ========================================================
    # RECOVER PREVIOUS IMAGE
    # ========================================================

    previous_image_context = ""

    if not combined_image_context:

        previous_image_context = (
            get_previous_image_context(
                previous_messages
            )
        )

    effective_image_context = (
        combined_image_context
        if combined_image_context
        else previous_image_context
    )

    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    user_message_content = question

    if processed_files:

        attachment_names = [
            item["filename"]
            for item in processed_files
        ]

        attachment_text = (
            "\n\nAttachments: "
            + ", ".join(
                attachment_names
            )
        )

        if user_message_content:

            user_message_content += (
                attachment_text
            )

        else:

            user_message_content = (
                attachment_text.strip()
            )

    if user_message_content.strip():

        add_message(
            chat_id=current_chat_id,
            role="user",
            content=user_message_content,
            sources=[],
            videos=[],
        )

    # ========================================================
    # FILE ONLY REQUEST
    # ========================================================

    if not question:

        if image_contexts:

            answer = (
                "I analyzed the uploaded image. "
                "Please ask a question about the "
                "information shown in the image."
            )

        else:

            answer = (
                "Your file has been received. "
                "Please ask a question about it."
            )

        add_message(
            chat_id=current_chat_id,
            role="assistant",
            content=answer,
            sources=[],
            videos=[],
        )

        touch_chat(
            current_chat_id,
            user_id,
        )

        return {
            "success": True,
            "chat_id": current_chat_id,
            "question": question,
            "answer": answer,
            "sources": [],
            "videos": [],
            "files": processed_files,
            "confidence": {
                "label": "not_applicable",
                "score": 0.0,
                "grounding_score": 0.0,
            },
            "grounding_score": 0.0,
            "evidence": [],
            "image_analysis": combined_image_context,
        }

    # ========================================================
    # RUN RAG
    # ========================================================

    try:

        print()
        print("=" * 70)
        print("CHAT REQUEST")
        print("=" * 70)

        print(
            "USER:",
            user["email"],
        )

        print(
            "USER ID:",
            user_id,
        )

        print(
            "CHAT ID:",
            current_chat_id,
        )

        print(
            "QUESTION:",
            question,
        )

        print(
            "PREVIOUS MESSAGES:",
            len(previous_messages),
        )

        if effective_image_context:

            print(
                "IMAGE CONTEXT AVAILABLE: YES"
            )

        else:

            print(
                "IMAGE CONTEXT AVAILABLE: NO"
            )

        print("=" * 70)

        # ----------------------------------------------------
        # CALL RAG
        # ----------------------------------------------------

        # ----------------------------------------------------
        # CONVERSATION MEMORY
        # ----------------------------------------------------
        # previous_messages was loaded BEFORE the current user
        # message was saved, so it contains only the earlier
        # conversation. This is exactly what the LLM needs as
        # short-term conversation context.
        conversation_history = build_conversation_history(
            previous_messages,
            max_messages=12,
        )

        # Persistent memory belongs to the authenticated user,
        # not to one particular chat. Therefore memories survive
        # new chats and future sessions.
        long_term_memories = get_long_term_memory_for_user(
            user_id
        )

        print(
            "CONVERSATION HISTORY:",
            len(conversation_history),
        )

        print(
            "LONG-TERM MEMORIES:",
            len(long_term_memories),
        )

        result = await run_in_threadpool(
            answer_question,
            question,
            image_context=effective_image_context,
            conversation_history=conversation_history,
            memories=long_term_memories,
            user_id=user_id,
            chat_id=current_chat_id,
            document_id=selected_rag_document_id,
        )

        if not isinstance(
            result,
            dict,
        ):

            result = {}

        # ----------------------------------------------------
        # RESPONSE DATA
        # ----------------------------------------------------

        answer = result.get(
            "answer",
            "",
        )

        sources = result.get(
            "sources",
            [],
        )

        if document_id is not None:
            for source_item in sources:
                source_item["database_document_id"] = document_id

        videos = result.get(
            "videos",
            [],
        )

        confidence = result.get(
            "confidence",
            {
                "label": "not_applicable",
                "score": 0.0,
                "grounding_score": 0.0,
            },
        )

        grounding_score = result.get(
            "grounding_score",
            confidence.get(
                "grounding_score",
                0.0,
            )
            if isinstance(
                confidence,
                dict,
            )
            else 0.0,
        )

        evidence = result.get(
            "evidence",
            [],
        )

        returned_image_analysis = result.get(
            "image_analysis",
            effective_image_context,
        )

        if not answer:

            answer = (
                "I couldn't generate an answer "
                "from the available evidence."
            )

        # ====================================================
        # SAVE DURABLE USER MEMORY
        # ====================================================
        # rag.py normally performs this automatically. We repeat the
        # simple memory extraction here only as a defensive layer so
        # explicit statements such as "my name is Deekshitha" are
        # persisted even if a future RAG path changes.
        try:
            memory_match = None

            import re as _memory_re

            memory_match = _memory_re.search(
                r"\\bmy name is\\s+([A-Za-z][A-Za-z .'-]{1,60})",
                question,
                _memory_re.IGNORECASE,
            )

            if memory_match:
                memory_name = memory_match.group(1).strip(
                    " .,!?"
                )

                if memory_name:
                    upsert_memory(
                        user_id,
                        "name",
                        memory_name,
                        "personal",
                        1.0,
                    )

                    print(
                        "LONG-TERM MEMORY SAVED:",
                        "name =",
                        memory_name,
                    )

        except Exception as memory_error:
            print(
                "LONG-TERM MEMORY SAVE ERROR:",
                repr(memory_error),
            )

        # ====================================================
        # SAVE ASSISTANT MESSAGE
        # ====================================================

        try:

            add_message(
                chat_id=current_chat_id,
                role="assistant",
                content=answer,
                sources=sources,
                videos=videos,
                evidence=evidence,
                confidence=confidence,
                grounding_score=grounding_score,
                attachments=processed_files,
                mode=result.get(
                    "mode"
                ),
                image_analysis=returned_image_analysis,
            )

        except TypeError:

            # Compatibility with older database.py

            add_message(
                chat_id=current_chat_id,
                role="assistant",
                content=answer,
                sources=sources,
                videos=videos,
            )

        # ====================================================
        # UPDATE CHAT
        # ====================================================

        touch_chat(
            current_chat_id,
            user_id,
        )

        print()
        print(
            "ANSWER GENERATED SUCCESSFULLY."
        )
        print(
            "SOURCES:",
            len(sources),
        )
        print(
            "GROUNDING SCORE:",
            grounding_score,
        )
        print("=" * 70)

        # ====================================================
        # RESPONSE
        # ====================================================

        return {
            "success": result.get(
                "success",
                True,
            ),
            "chat_id": current_chat_id,
            "question": question,
            "answer": answer,
            "sources": sources,
            "videos": videos,
            "files": processed_files,
            "confidence": confidence,
            "grounding_score": grounding_score,
            "evidence": evidence,
            "mode": result.get(
                "mode"
            ),
            "image_analysis": returned_image_analysis,
        }

    except HTTPException:

        raise

    except Exception as error:

        print()
        print("=" * 70)
        print("CHAT ERROR")
        print("=" * 70)
        print(
            repr(error)
        )

        traceback.print_exc()

        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process "
                "the question: "
                + str(error)
            ),
        )


# ============================================================
# VOICE ASK ENDPOINT
# ============================================================

@app.post("/voice-ask")
async def voice_ask_endpoint(
    audio: UploadFile = File(...),
    question: str = Form(""),
    chat_id: int | None = Form(None),
    document_id: int | None = Form(None),
    user=Depends(get_current_user),
):
    """
    Transcribes audio using Groq Whisper and queries the RAG system.
    """
    try:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file was empty.")

        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")

        from groq import Groq
        groq_client = Groq(api_key=groq_api_key)

        filename = audio.filename or "recording.webm"
        if not any(filename.endswith(ext) for ext in [".webm", ".wav", ".mp3", ".ogg", ".m4a"]):
            filename = "recording.webm"

        transcription = groq_client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            response_format="text",
        )

        transcribed_text = transcription.strip() if isinstance(transcription, str) else str(transcription).strip()

        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Could not detect speech in the audio recording.")

        effective_question = transcribed_text
        if question and question.strip() and question.strip() != transcribed_text:
            effective_question = f"{question.strip()} {transcribed_text}"

        chat_response = await chat(
            question=effective_question,
            chat_id=chat_id,
            document_id=document_id,
            files=None,
            user=user,
        )

        chat_response["transcript"] = transcribed_text
        chat_response["conversation_id"] = chat_response.get("chat_id")
        return chat_response

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


class SpeakRequest(BaseModel):
    text: str

@app.post("/speak")
def speak_endpoint(
    request: SpeakRequest,
    user=Depends(get_current_user),
):
    return {
        "success": True,
        "text": request.text,
    }