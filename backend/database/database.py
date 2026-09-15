import sqlite3
import json
import os
from datetime import datetime, timezone


# ============================================================
# DRUGASSIST DATABASE
# ============================================================
#
# This module provides:
#
#   1. Users
#   2. Chats
#   3. Messages
#   4. Documents
#   5. Audit logs
#   6. Feedback
#   7. Long-term user memory
#   8. Conversation search
#
# IMPORTANT:
# This file stores memory.
# The RAG/agent layer is responsible for deciding when to
# retrieve and use that memory.
#
# ============================================================


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "drugassist.db"
)

USERS_BACKUP_PATH = os.path.join(
    BASE_DIR,
    "users_backup.json"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a SQLite connection.

    Every connection enables foreign-key enforcement.
    Row factory allows dictionary-like access.
    """

    connection = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    return connection


# ============================================================
# GENERAL HELPERS
# ============================================================

def _now():
    """
    Return the current UTC timestamp as an ISO string.

    UTC is used so timestamps remain consistent regardless
    of where the application is running.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _json(value):
    """
    Safely convert Python objects to JSON text
    for SQLite TEXT columns.
    """

    if value is None:
        return "[]"

    if isinstance(value, str):
        return value

    try:
        return json.dumps(
            value,
            ensure_ascii=False
        )

    except Exception:
        return "[]"


def _safe_json(
    value,
    default=None
):
    """
    Safely convert stored JSON back into Python objects.
    """

    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(
        value,
        (list, dict)
    ):
        return value

    try:
        return json.loads(value)

    except Exception:
        return default


def _serialize_optional(
    value,
    default=None
):
    """
    Convert dictionaries/lists/tuples to JSON strings.

    Used for optional TEXT fields.
    """

    if value is None:
        return default

    if isinstance(
        value,
        (dict, list, tuple)
    ):
        try:
            return json.dumps(
                value,
                ensure_ascii=False
            )

        except Exception:
            return default

    return value


def _normalize_grounding_score(
    value
):
    """
    Convert grounding score into a SQLite-compatible REAL.

    Accepts:
        int
        float
        numeric strings
        dictionaries containing a score
    """

    if value is None:
        return None

    if isinstance(
        value,
        bool
    ):
        return float(value)

    if isinstance(
        value,
        (int, float)
    ):
        return float(value)

    if isinstance(
        value,
        dict
    ):

        for key in (
            "grounding_score",
            "score",
            "value"
        ):

            candidate = value.get(
                key
            )

            if isinstance(
                candidate,
                (int, float)
            ):
                return float(candidate)

            if isinstance(
                candidate,
                str
            ):

                try:
                    return float(
                        candidate
                    )

                except Exception:
                    pass

        return None

    if isinstance(
        value,
        str
    ):

        try:
            return float(value)

        except Exception:
            return None

    return None


def _table_columns(
    connection,
    table_name
):
    """
    Return all column names for a SQLite table.
    """

    cursor = connection.cursor()

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    rows = cursor.fetchall()

    return {
        row["name"]
        for row in rows
    }


def _add_column(
    connection,
    table_name,
    column_name,
    column_definition
):
    """
    Add a column only when it does not already exist.
    """

    columns = _table_columns(
        connection,
        table_name
    )

    if column_name in columns:
        return

    cursor = connection.cursor()

    cursor.execute(
        f"""
        ALTER TABLE {table_name}
        ADD COLUMN {column_name}
        {column_definition}
        """
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    try:

        # ====================================================
        # USERS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                email TEXT NOT NULL UNIQUE,

                password_hash TEXT NOT NULL,

                created_at TEXT NOT NULL
            )
            """
        )


        # ====================================================
        # CHATS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                title TEXT NOT NULL
                    DEFAULT 'New chat',

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )


        # ====================================================
        # MESSAGES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                role TEXT NOT NULL,

                content TEXT NOT NULL,

                sources_json TEXT NOT NULL
                    DEFAULT '[]',

                videos_json TEXT NOT NULL
                    DEFAULT '[]',

                evidence_json TEXT NOT NULL
                    DEFAULT '[]',

                confidence TEXT,

                grounding_score REAL,

                attachments_json TEXT NOT NULL
                    DEFAULT '[]',

                mode TEXT,

                image_analysis TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY(chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            )
            """
        )


        # ====================================================
        # DOCUMENTS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                filename TEXT NOT NULL,

                stored_filename TEXT,

                file_path TEXT,

                file_type TEXT
                    DEFAULT 'pdf',

                drug TEXT,

                source TEXT,

                document_id TEXT,

                document_key TEXT,

                pages INTEGER
                    DEFAULT 0,

                chunks INTEGER
                    DEFAULT 0,

                file_size INTEGER
                    DEFAULT 0,

                freshness_status TEXT
                    DEFAULT 'unknown',

                created_at TEXT NOT NULL,

                uploaded_at TEXT,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )


        # ====================================================
        # AUDIT LOGS
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                chat_id INTEGER,

                question TEXT,

                answer TEXT,

                citations_json TEXT
                    DEFAULT '[]',

                confidence TEXT,

                grounding_score REAL,

                mode TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(chat_id)
                    REFERENCES chats(id)
                    ON DELETE SET NULL
            )
            """
        )


        # ====================================================
        # FEEDBACK
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER,

                message_id INTEGER,

                rating INTEGER,

                comment TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(message_id)
                    REFERENCES messages(id)
                    ON DELETE CASCADE
            )
            """
        )


        # ====================================================
        # LONG-TERM USER MEMORY
        # ====================================================
        #
        # This is the important new part.
        #
        # Example:
        #
        # user_id = 1
        # memory_key = "name"
        # memory_value = "Deekshitha"
        #
        # Another example:
        #
        # memory_key = "preferred_language"
        # memory_value = "Telugu"
        #
        # Memory survives:
        #
        #   logout
        #   application restart
        #   next day
        #   opening another chat
        #
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_memories (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                memory_key TEXT NOT NULL,

                memory_value TEXT NOT NULL,

                category TEXT
                    DEFAULT 'general',

                importance REAL
                    DEFAULT 0.5,

                source_chat_id INTEGER,

                source_message_id INTEGER,

                active INTEGER NOT NULL
                    DEFAULT 1,

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL,

                last_accessed_at TEXT,

                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY(source_chat_id)
                    REFERENCES chats(id)
                    ON DELETE SET NULL,

                FOREIGN KEY(source_message_id)
                    REFERENCES messages(id)
                    ON DELETE SET NULL
            )
            """
        )


        # ====================================================
        # MEMORY MIGRATIONS
        # ====================================================

        memory_columns = _table_columns(
            connection,
            "user_memories"
        )

        memory_migrations = [

            (
                "category",
                "TEXT DEFAULT 'general'"
            ),

            (
                "importance",
                "REAL DEFAULT 0.5"
            ),

            (
                "source_chat_id",
                "INTEGER"
            ),

            (
                "source_message_id",
                "INTEGER"
            ),

            (
                "active",
                "INTEGER NOT NULL DEFAULT 1"
            ),

            (
                "created_at",
                "TEXT NOT NULL DEFAULT ''"
            ),

            (
                "updated_at",
                "TEXT NOT NULL DEFAULT ''"
            ),

            (
                "last_accessed_at",
                "TEXT"
            )
        ]

        for (
            column_name,
            definition
        ) in memory_migrations:

            if column_name not in memory_columns:

                _add_column(
                    connection,
                    "user_memories",
                    column_name,
                    definition
                )


        # ====================================================
        # MESSAGE MIGRATIONS
        # ====================================================

        message_columns = _table_columns(
            connection,
            "messages"
        )

        if "sources_json" not in message_columns:

            _add_column(
                connection,
                "messages",
                "sources_json",
                "TEXT NOT NULL DEFAULT '[]'"
            )

        if "videos_json" not in message_columns:

            _add_column(
                connection,
                "messages",
                "videos_json",
                "TEXT NOT NULL DEFAULT '[]'"
            )

        if "evidence_json" not in message_columns:

            _add_column(
                connection,
                "messages",
                "evidence_json",
                "TEXT NOT NULL DEFAULT '[]'"
            )

        if "confidence" not in message_columns:

            _add_column(
                connection,
                "messages",
                "confidence",
                "TEXT"
            )

        if "grounding_score" not in message_columns:

            _add_column(
                connection,
                "messages",
                "grounding_score",
                "REAL"
            )

        if "attachments_json" not in message_columns:

            _add_column(
                connection,
                "messages",
                "attachments_json",
                "TEXT NOT NULL DEFAULT '[]'"
            )

        if "mode" not in message_columns:

            _add_column(
                connection,
                "messages",
                "mode",
                "TEXT"
            )

        if "image_analysis" not in message_columns:

            _add_column(
                connection,
                "messages",
                "image_analysis",
                "TEXT"
            )


        # ====================================================
        # DOCUMENT MIGRATIONS
        # ====================================================

        document_columns = _table_columns(
            connection,
            "documents"
        )

        document_migrations = [

            (
                "stored_filename",
                "TEXT"
            ),

            (
                "file_path",
                "TEXT"
            ),

            (
                "file_type",
                "TEXT DEFAULT 'pdf'"
            ),

            (
                "drug",
                "TEXT"
            ),

            (
                "source",
                "TEXT"
            ),

            (
                "document_id",
                "TEXT"
            ),

            (
                "document_key",
                "TEXT"
            ),

            (
                "pages",
                "INTEGER DEFAULT 0"
            ),

            (
                "chunks",
                "INTEGER DEFAULT 0"
            ),

            (
                "file_size",
                "INTEGER DEFAULT 0"
            ),

            (
                "freshness_status",
                "TEXT DEFAULT 'unknown'"
            ),

            (
                "uploaded_at",
                "TEXT"
            )
        ]

        for (
            column_name,
            definition
        ) in document_migrations:

            if column_name not in document_columns:

                _add_column(
                    connection,
                    "documents",
                    column_name,
                    definition
                )


        # ====================================================
        # INDEXES
        # ====================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chats_user_id
            ON chats(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_messages_chat_id
            ON messages(chat_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_user_id
            ON documents(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_documents_document_id
            ON documents(document_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_audit_user_id
            ON audit_logs(user_id)
            """
        )

        # ----------------------------------------------------
        # MEMORY INDEXES
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_memories_user_id
            ON user_memories(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_memories_user_key
            ON user_memories(user_id, memory_key)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_memories_category
            ON user_memories(user_id, category)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_memories_active
            ON user_memories(user_id, active)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_memories_updated
            ON user_memories(user_id, updated_at)
            """
        )


        connection.commit()

        # Automatically restore/seed persistent accounts from users_backup.json
        _restore_users_from_backup(connection)

    finally:

        connection.close()


# ============================================================
# USER PERSISTENCE & BACKUP HELPERS
# ============================================================

DEFAULT_GITHUB_REPO = "kamaleshsai1/Drug-Assistant-RAG"

def _get_github_token():
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token and token.strip():
        return token.strip()
    try:
        import subprocess
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False
        )
        url = res.stdout.strip()
        if "@" in url and "://" in url:
            creds = url.split("://")[1].split("@")[0]
            if ":" in creds:
                token_val = creds.split(":")[1].strip()
                if token_val:
                    return token_val
    except Exception:
        pass
    return None

def _get_github_repo():
    return os.getenv("GITHUB_REPOSITORY", DEFAULT_GITHUB_REPO).strip()

def _restore_users_from_backup(connection=None):
    """
    Restore registered users from users_backup.json into SQLite.
    Also queries GitHub Contents API to ensure users registered
    during previous Render runs are recovered.
    """
    local_users = []
    if os.path.exists(USERS_BACKUP_PATH):
        try:
            with open(USERS_BACKUP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    local_users = data
        except Exception as e:
            print(f"[DrugAssist Persistence] Error reading users_backup.json: {e}")

    github_token = _get_github_token()
    repo = _get_github_repo()
    url = f"https://api.github.com/repos/{repo}/contents/backend/database/users_backup.json"

    # Try authenticated read first, then unauthenticated public read fallback
    headers_attempts = []
    if github_token:
        headers_attempts.append({
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DrugAssist-Backend"
        })
    headers_attempts.append({
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DrugAssist-Backend"
    })

    for headers in headers_attempts:
        try:
            import urllib.request
            import base64
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    gh_data = json.loads(resp.read().decode("utf-8"))
                    content_str = base64.b64decode(gh_data["content"]).decode("utf-8")
                    remote_users = json.loads(content_str)
                    if isinstance(remote_users, list) and len(remote_users) > 0:
                        merged = {str(u.get("email", "")).strip().lower(): u for u in remote_users if u.get("email")}
                        for lu in local_users:
                            lu_email = str(lu.get("email", "")).strip().lower()
                            if lu_email:
                                merged[lu_email] = lu
                        local_users = list(merged.values())
                        try:
                            with open(USERS_BACKUP_PATH, "w", encoding="utf-8") as f:
                                json.dump(local_users, f, indent=2)
                        except Exception:
                            pass
                        print(f"[DrugAssist Persistence] Restored {len(local_users)} merged users from GitHub cloud backup.")
                        break
        except Exception:
            continue

    if not local_users:
        return

    close_conn = False
    if connection is None:
        connection = get_connection()
        close_conn = True

    cursor = connection.cursor()
    try:
        for u in local_users:
            u_id = u.get("id")
            email = str(u.get("email", "")).strip().lower()
            name = str(u.get("name", "")).strip() or "User"
            pwd_hash = u.get("password_hash", "")
            created_at = u.get("created_at") or _now()

            if not email or not pwd_hash:
                continue

            cursor.execute(
                "SELECT id, password_hash FROM users WHERE LOWER(email) = LOWER(?)",
                (email,)
            )
            existing = cursor.fetchone()
            if not existing:
                if u_id is not None:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO users (id, name, email, password_hash, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (u_id, name, email, pwd_hash, created_at)
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO users (name, email, password_hash, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (name, email, pwd_hash, created_at)
                    )
                print(f"[DrugAssist Persistence] Restored account: {email}")
            elif existing["password_hash"] != pwd_hash:
                cursor.execute(
                    "UPDATE users SET password_hash = ?, name = ? WHERE LOWER(email) = LOWER(?)",
                    (pwd_hash, name, email)
                )
        connection.commit()
    finally:
        if close_conn:
            connection.close()


def _sync_user_to_backup(user_id: int, name: str, email: str, password_hash: str, created_at: str):
    """
    Saves user to users_backup.json and syncs to GitHub API to ensure permanent persistence.
    """
    users_list = []
    if os.path.exists(USERS_BACKUP_PATH):
        try:
            with open(USERS_BACKUP_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    users_list = data
        except Exception:
            users_list = []

    clean_email = email.strip().lower()
    found = False
    for u in users_list:
        if str(u.get("email", "")).strip().lower() == clean_email:
            u["id"] = user_id
            u["name"] = name
            u["password_hash"] = password_hash
            u["created_at"] = created_at
            found = True
            break
    if not found:
        users_list.append({
            "id": user_id,
            "name": name,
            "email": clean_email,
            "password_hash": password_hash,
            "created_at": created_at
        })

    try:
        with open(USERS_BACKUP_PATH, "w", encoding="utf-8") as f:
            json.dump(users_list, f, indent=2)
    except Exception as e:
        print(f"[DrugAssist Persistence] Error writing users_backup.json: {e}")

    # Cloud sync in non-blocking background thread with retries and remote merge
    github_token = _get_github_token()
    if github_token:
        import threading
        def _bg_push():
            try:
                import urllib.request
                import urllib.error
                import base64
                import time

                repo = _get_github_repo()
                url = f"https://api.github.com/repos/{repo}/contents/backend/database/users_backup.json"

                for attempt in range(3):
                    req_get = urllib.request.Request(
                        url,
                        headers={
                            "Authorization": f"token {github_token}",
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "DrugAssist-Backend"
                        }
                    )
                    sha = None
                    remote_users = []
                    try:
                        with urllib.request.urlopen(req_get, timeout=8) as resp:
                            if resp.status == 200:
                                current_file = json.loads(resp.read().decode("utf-8"))
                                sha = current_file.get("sha")
                                raw_c = base64.b64decode(current_file.get("content", "")).decode("utf-8")
                                remote_users = json.loads(raw_c)
                    except Exception as ge:
                        print(f"[DrugAssist Persistence] Notice fetching remote backup: {ge}")

                    merged_map = {}
                    if isinstance(remote_users, list):
                        for ru in remote_users:
                            em = str(ru.get("email", "")).strip().lower()
                            if em:
                                merged_map[em] = ru
                    for lu in users_list:
                        em = str(lu.get("email", "")).strip().lower()
                        if em:
                            merged_map[em] = lu

                    final_users = list(merged_map.values())

                    try:
                        with open(USERS_BACKUP_PATH, "w", encoding="utf-8") as f:
                            json.dump(final_users, f, indent=2)
                    except Exception:
                        pass

                    content_bytes = json.dumps(final_users, indent=2).encode("utf-8")
                    b64_content = base64.b64encode(content_bytes).decode("utf-8")
                    put_data = {
                        "message": f"persist: auto-sync user {clean_email}",
                        "content": b64_content,
                        "branch": "main"
                    }
                    if sha:
                        put_data["sha"] = sha

                    req_put = urllib.request.Request(
                        url,
                        data=json.dumps(put_data).encode("utf-8"),
                        headers={
                            "Authorization": f"token {github_token}",
                            "Accept": "application/vnd.github.v3+json",
                            "Content-Type": "application/json",
                            "User-Agent": "DrugAssist-Backend"
                        },
                        method="PUT"
                    )
                    try:
                        with urllib.request.urlopen(req_put, timeout=10) as put_resp:
                            if put_resp.status in (200, 201):
                                print(f"[DrugAssist Persistence] Synced {clean_email} to GitHub cloud backup: {put_resp.status}")
                                break
                    except urllib.error.HTTPError as he:
                        if he.code == 409 and attempt < 2:
                            time.sleep(1)
                            continue
                        print(f"[DrugAssist Persistence] Notice syncing to GitHub: {he}")
                        break
                    except Exception as pe:
                        print(f"[DrugAssist Persistence] Notice syncing to GitHub: {pe}")
                        break
            except Exception as e:
                print(f"[DrugAssist Persistence] Background push error: {e}")

        threading.Thread(target=_bg_push, daemon=True).start()


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(
    name: str,
    email: str,
    password_hash: str
):

    connection = get_connection()

    cursor = connection.cursor()

    now_time = _now()
    clean_email = email.strip().lower()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                clean_email,
                password_hash,
                now_time
            )
        )

        user_id = cursor.lastrowid

        connection.commit()

        _sync_user_to_backup(
            user_id=user_id,
            name=name,
            email=clean_email,
            password_hash=password_hash,
            created_at=now_time
        )

        return user_id

    finally:

        connection.close()


def get_user_by_email(
    email: str
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        clean_target = str(email or "").strip().lower()

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                password_hash,
                created_at
            FROM users
            WHERE LOWER(email) = ? OR LOWER(name) = ?
            LIMIT 1
            """,
            (
                clean_target,
                clean_target,
            )
        )

        row = cursor.fetchone()

        if not row:
            # On-demand sync/restore from cloud backup in case container was restarted
            _restore_users_from_backup(connection)
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password_hash,
                    created_at
                FROM users
                WHERE LOWER(email) = ? OR LOWER(name) = ?
                LIMIT 1
                """,
                (
                    clean_target,
                    clean_target,
                )
            )
            row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    finally:

        connection.close()


def get_user_by_id(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                created_at
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        )

        row = cursor.fetchone()

        if not row:
            # On-demand sync/restore from cloud backup in case container was restarted
            _restore_users_from_backup(connection)
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    created_at
                FROM users
                WHERE id = ?
                """,
                (
                    user_id,
                )
            )
            row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    finally:

        connection.close()


# ============================================================
# CHAT FUNCTIONS
# ============================================================

def create_chat(
    user_id: int,
    title: str = "New chat"
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        now = _now()

        cursor.execute(
            """
            INSERT INTO chats
            (
                user_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                title or "New chat",
                now,
                now
            )
        )

        chat_id = cursor.lastrowid

        connection.commit()

        return chat_id

    finally:

        connection.close()


def get_user_chats(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at
            FROM chats
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_chat(
    chat_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                title,
                created_at,
                updated_at
            FROM chats
            WHERE id = ?
              AND user_id = ?
            """,
            (
                chat_id,
                user_id
            )
        )

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    finally:

        connection.close()


def delete_chat(
    chat_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM chats
            WHERE id = ?
              AND user_id = ?
            """,
            (
                chat_id,
                user_id
            )
        )

        deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    finally:

        connection.close()


def update_chat_title(
    chat_id: int,
    user_id: int,
    title: str
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE chats
            SET
                title = ?,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                title or "New chat",
                _now(),
                chat_id,
                user_id
            )
        )

        updated = cursor.rowcount > 0

        connection.commit()

        return updated

    finally:

        connection.close()


def touch_chat(
    chat_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE chats
            SET updated_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                _now(),
                chat_id,
                user_id
            )
        )

        updated = cursor.rowcount > 0

        connection.commit()

        return updated

    finally:

        connection.close()


# ============================================================
# MESSAGE FUNCTIONS
# ============================================================

def add_message(
    chat_id: int,
    role: str,
    content: str,
    sources=None,
    videos=None,
    evidence=None,
    confidence=None,
    grounding_score=None,
    attachments=None,
    mode=None,
    image_analysis=None,
    **kwargs
):
    """
    Store a DrugAssist message.

    Supports:
        user
        assistant
        system

    Also stores RAG metadata.
    """

    if sources is None:
        sources = []

    if videos is None:
        videos = []

    if evidence is None:
        evidence = []

    if attachments is None:
        attachments = []


    # --------------------------------------------------------
    # Compatibility aliases
    # --------------------------------------------------------

    if not evidence:

        evidence = kwargs.get(
            "evidence_json",
            []
        )

    if not attachments:

        attachments = kwargs.get(
            "attachments_json",
            []
        )

    if confidence is None:

        confidence = kwargs.get(
            "confidence"
        )

    if grounding_score is None:

        grounding_score = kwargs.get(
            "grounding_score"
        )

    if mode is None:

        mode = kwargs.get(
            "mode"
        )

    if image_analysis is None:

        image_analysis = kwargs.get(
            "image_analysis"
        )


    # --------------------------------------------------------
    # Normalize types
    # --------------------------------------------------------

    confidence = _serialize_optional(
        confidence,
        default=None
    )

    mode = _serialize_optional(
        mode,
        default=None
    )

    image_analysis = _serialize_optional(
        image_analysis,
        default=None
    )

    grounding_score = (
        _normalize_grounding_score(
            grounding_score
        )
    )


    # --------------------------------------------------------
    # Insert message
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO messages
            (
                chat_id,
                role,
                content,
                sources_json,
                videos_json,
                evidence_json,
                confidence,
                grounding_score,
                attachments_json,
                mode,
                image_analysis,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content or "",
                _json(sources),
                _json(videos),
                _json(evidence),
                confidence,
                grounding_score,
                _json(attachments),
                mode,
                image_analysis,
                _now()
            )
        )

        message_id = cursor.lastrowid

        connection.commit()

        return message_id

    finally:

        connection.close()


def get_messages(
    chat_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                sources_json,
                videos_json,
                evidence_json,
                confidence,
                grounding_score,
                attachments_json,
                mode,
                image_analysis,
                created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (
                chat_id,
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_recent_messages(
    chat_id: int,
    limit: int = 20
):
    """
    Return the most recent messages from a chat.

    This will be used by the conversation-memory layer
    to maintain short-term conversational context.
    """

    try:
        limit = int(limit)

    except Exception:
        limit = 20

    limit = max(
        1,
        min(limit, 100)
    )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                sources_json,
                videos_json,
                evidence_json,
                confidence,
                grounding_score,
                attachments_json,
                mode,
                image_analysis,
                created_at
            FROM messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                chat_id,
                limit
            )
        )

        rows = cursor.fetchall()

        result = [
            dict(row)
            for row in rows
        ]

        result.reverse()

        return result

    finally:

        connection.close()


def get_message(
    message_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                chat_id,
                role,
                content,
                sources_json,
                videos_json,
                evidence_json,
                confidence,
                grounding_score,
                attachments_json,
                mode,
                image_analysis,
                created_at
            FROM messages
            WHERE id = ?
            """,
            (
                message_id,
            )
        )

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    finally:

        connection.close()


# ============================================================
# CONVERSATION SEARCH
# ============================================================

def search_user_conversations(
    user_id: int,
    query: str,
    limit: int = 20
):
    """
    Search previous conversations belonging to one user.

    This is intentionally user-scoped.

    Example:
        search_user_conversations(
            user_id=1,
            query="Losartan"
        )

    This allows the future memory layer to find previous
    conversations even when the user starts a new chat.
    """

    query = (
        str(query or "")
        .strip()
    )

    if not query:
        return []

    try:
        limit = int(limit)

    except Exception:
        limit = 20

    limit = max(
        1,
        min(limit, 100)
    )

    # SQLite LIKE wildcard escaping.
    escaped = (
        query
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )

    pattern = f"%{escaped}%"

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                m.id AS message_id,
                m.chat_id,
                c.title AS chat_title,
                m.role,
                m.content,
                m.created_at
            FROM messages m
            INNER JOIN chats c
                ON m.chat_id = c.id
            WHERE c.user_id = ?
              AND m.content LIKE ? ESCAPE '\\'
            ORDER BY m.id DESC
            LIMIT ?
            """,
            (
                user_id,
                pattern,
                limit
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_chat_messages_for_user(
    chat_id: int,
    user_id: int
):
    """
    Securely retrieve messages only when the chat belongs
    to the requested user.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                m.id,
                m.chat_id,
                m.role,
                m.content,
                m.sources_json,
                m.videos_json,
                m.evidence_json,
                m.confidence,
                m.grounding_score,
                m.attachments_json,
                m.mode,
                m.image_analysis,
                m.created_at
            FROM messages m
            INNER JOIN chats c
                ON m.chat_id = c.id
            WHERE m.chat_id = ?
              AND c.user_id = ?
            ORDER BY m.id ASC
            """,
            (
                chat_id,
                user_id
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


# ============================================================
# LONG-TERM MEMORY FUNCTIONS
# ============================================================

def create_memory(
    user_id: int,
    memory_key: str,
    memory_value: str,
    category: str = "general",
    importance: float = 0.5,
    source_chat_id=None,
    source_message_id=None
):
    """
    Create a new long-term memory.

    Example:

        create_memory(
            user_id=1,
            memory_key="name",
            memory_value="Deekshitha",
            category="personal",
            importance=1.0
        )
    """

    memory_key = (
        str(memory_key or "")
        .strip()
        .lower()
    )

    memory_value = (
        str(memory_value or "")
        .strip()
    )

    category = (
        str(category or "general")
        .strip()
        .lower()
    )

    if not memory_key or not memory_value:
        return None

    try:
        importance = float(
            importance
        )

    except Exception:
        importance = 0.5

    importance = max(
        0.0,
        min(importance, 1.0)
    )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        now = _now()

        cursor.execute(
            """
            INSERT INTO user_memories
            (
                user_id,
                memory_key,
                memory_value,
                category,
                importance,
                source_chat_id,
                source_message_id,
                active,
                created_at,
                updated_at,
                last_accessed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                user_id,
                memory_key,
                memory_value,
                category,
                importance,
                source_chat_id,
                source_message_id,
                now,
                now,
                now
            )
        )

        memory_id = cursor.lastrowid

        connection.commit()

        return memory_id

    finally:

        connection.close()


def upsert_memory(
    user_id: int,
    memory_key: str,
    memory_value: str,
    category: str = "general",
    importance: float = 0.5,
    source_chat_id=None,
    source_message_id=None
):
    """
    Create or update a memory.

    A user should not end up with dozens of copies of:

        name = Deekshitha

    Instead, the existing memory is updated.

    The unique logical identity is:

        user_id + memory_key
    """

    memory_key = (
        str(memory_key or "")
        .strip()
        .lower()
    )

    memory_value = (
        str(memory_value or "")
        .strip()
    )

    category = (
        str(category or "general")
        .strip()
        .lower()
    )

    if not memory_key or not memory_value:
        return None

    try:
        importance = float(
            importance
        )

    except Exception:
        importance = 0.5

    importance = max(
        0.0,
        min(importance, 1.0)
    )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id
            FROM user_memories
            WHERE user_id = ?
              AND memory_key = ?
              AND active = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                user_id,
                memory_key
            )
        )

        existing = cursor.fetchone()

        now = _now()

        if existing:

            memory_id = existing["id"]

            cursor.execute(
                """
                UPDATE user_memories
                SET
                    memory_value = ?,
                    category = ?,
                    importance = ?,
                    source_chat_id = ?,
                    source_message_id = ?,
                    active = 1,
                    updated_at = ?,
                    last_accessed_at = ?
                WHERE id = ?
                  AND user_id = ?
                """,
                (
                    memory_value,
                    category,
                    importance,
                    source_chat_id,
                    source_message_id,
                    now,
                    now,
                    memory_id,
                    user_id
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO user_memories
                (
                    user_id,
                    memory_key,
                    memory_value,
                    category,
                    importance,
                    source_chat_id,
                    source_message_id,
                    active,
                    created_at,
                    updated_at,
                    last_accessed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    user_id,
                    memory_key,
                    memory_value,
                    category,
                    importance,
                    source_chat_id,
                    source_message_id,
                    now,
                    now,
                    now
                )
            )

            memory_id = cursor.lastrowid

        connection.commit()

        return memory_id

    finally:

        connection.close()


def get_memory(
    user_id: int,
    memory_key: str
):
    """
    Retrieve one memory by its logical key.
    """

    memory_key = (
        str(memory_key or "")
        .strip()
        .lower()
    )

    if not memory_key:
        return None

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                memory_key,
                memory_value,
                category,
                importance,
                source_chat_id,
                source_message_id,
                active,
                created_at,
                updated_at,
                last_accessed_at
            FROM user_memories
            WHERE user_id = ?
              AND memory_key = ?
              AND active = 1
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (
                user_id,
                memory_key
            )
        )

        row = cursor.fetchone()

        if not row:
            return None

        memory = dict(row)

        # Update access timestamp.
        cursor.execute(
            """
            UPDATE user_memories
            SET last_accessed_at = ?
            WHERE id = ?
              AND user_id = ?
            """,
            (
                _now(),
                memory["id"],
                user_id
            )
        )

        connection.commit()

        return memory

    finally:

        connection.close()


def get_user_memories(
    user_id: int,
    category=None,
    limit: int = 100
):
    """
    Return active long-term memories for a user.
    """

    try:
        limit = int(limit)

    except Exception:
        limit = 100

    limit = max(
        1,
        min(limit, 500)
    )

    connection = get_connection()

    cursor = connection.cursor()

    try:

        if category:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    memory_key,
                    memory_value,
                    category,
                    importance,
                    source_chat_id,
                    source_message_id,
                    active,
                    created_at,
                    updated_at,
                    last_accessed_at
                FROM user_memories
                WHERE user_id = ?
                  AND category = ?
                  AND active = 1
                ORDER BY
                    importance DESC,
                    updated_at DESC
                LIMIT ?
                """,
                (
                    user_id,
                    category,
                    limit
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    memory_key,
                    memory_value,
                    category,
                    importance,
                    source_chat_id,
                    source_message_id,
                    active,
                    created_at,
                    updated_at,
                    last_accessed_at
                FROM user_memories
                WHERE user_id = ?
                  AND active = 1
                ORDER BY
                    importance DESC,
                    updated_at DESC
                LIMIT ?
                """,
                (
                    user_id,
                    limit
                )
            )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def search_user_memories(
    user_id: int,
    query: str,
    limit: int = 20
):
    """
    Search long-term memories using simple SQLite text matching.

    The later RAG/agent layer can combine this with more
    intelligent memory selection.

    Search checks:

        memory_key
        memory_value
        category
    """

    query = (
        str(query or "")
        .strip()
    )

    if not query:
        return []

    try:
        limit = int(limit)

    except Exception:
        limit = 20

    limit = max(
        1,
        min(limit, 100)
    )

    escaped = (
        query
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )

    pattern = f"%{escaped}%"

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                memory_key,
                memory_value,
                category,
                importance,
                source_chat_id,
                source_message_id,
                active,
                created_at,
                updated_at,
                last_accessed_at
            FROM user_memories
            WHERE user_id = ?
              AND active = 1
              AND (
                    memory_key LIKE ? ESCAPE '\\'
                    OR memory_value LIKE ? ESCAPE '\\'
                    OR category LIKE ? ESCAPE '\\'
              )
            ORDER BY
                importance DESC,
                updated_at DESC
            LIMIT ?
            """,
            (
                user_id,
                pattern,
                pattern,
                pattern,
                limit
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def update_memory(
    memory_id: int,
    user_id: int,
    memory_value=None,
    category=None,
    importance=None
):
    """
    Update an existing memory.

    Only the owner of the memory can modify it.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        fields = []
        values = []

        if memory_value is not None:

            fields.append(
                "memory_value = ?"
            )

            values.append(
                str(memory_value).strip()
            )

        if category is not None:

            fields.append(
                "category = ?"
            )

            values.append(
                str(category)
                .strip()
                .lower()
            )

        if importance is not None:

            try:
                importance = float(
                    importance
                )

            except Exception:
                importance = 0.5

            importance = max(
                0.0,
                min(importance, 1.0)
            )

            fields.append(
                "importance = ?"
            )

            values.append(
                importance
            )

        if not fields:
            return False

        fields.append(
            "updated_at = ?"
        )

        values.append(
            _now()
        )

        values.extend(
            [
                memory_id,
                user_id
            ]
        )

        query = f"""
            UPDATE user_memories
            SET {", ".join(fields)}
            WHERE id = ?
              AND user_id = ?
              AND active = 1
        """

        cursor.execute(
            query,
            tuple(values)
        )

        updated = (
            cursor.rowcount > 0
        )

        connection.commit()

        return updated

    finally:

        connection.close()


def delete_memory(
    memory_id: int,
    user_id: int
):
    """
    Soft-delete a memory.

    The row remains in the database for auditability,
    but it will no longer be used as active memory.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE user_memories
            SET
                active = 0,
                updated_at = ?
            WHERE id = ?
              AND user_id = ?
              AND active = 1
            """,
            (
                _now(),
                memory_id,
                user_id
            )
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

        return deleted

    finally:

        connection.close()


def delete_memory_by_key(
    user_id: int,
    memory_key: str
):
    """
    Soft-delete a memory using its key.
    """

    memory_key = (
        str(memory_key or "")
        .strip()
        .lower()
    )

    if not memory_key:
        return False

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE user_memories
            SET
                active = 0,
                updated_at = ?
            WHERE user_id = ?
              AND memory_key = ?
              AND active = 1
            """,
            (
                _now(),
                user_id,
                memory_key
            )
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

        return deleted

    finally:

        connection.close()


def touch_memory(
    memory_id: int,
    user_id: int
):
    """
    Update the last-accessed timestamp for a memory.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE user_memories
            SET last_accessed_at = ?
            WHERE id = ?
              AND user_id = ?
              AND active = 1
            """,
            (
                _now(),
                memory_id,
                user_id
            )
        )

        updated = (
            cursor.rowcount > 0
        )

        connection.commit()

        return updated

    finally:

        connection.close()


# ============================================================
# MEMORY FORMATTING
# ============================================================

def format_memories_for_prompt(
    memories
):
    """
    Convert database memory records into a compact text
    representation for the LLM.

    Example:

        User name: Deekshitha
        Preferred language: Telugu

    This function does NOT decide which memories should be
    retrieved. The RAG/agent layer decides that.
    """

    if not memories:
        return ""

    lines = []

    for memory in memories:

        if not isinstance(
            memory,
            dict
        ):
            continue

        key = (
            memory.get("memory_key")
            or ""
        ).strip()

        value = (
            memory.get("memory_value")
            or ""
        ).strip()

        category = (
            memory.get("category")
            or "general"
        ).strip()

        if not key or not value:
            continue

        if category == "personal":

            label = key.replace(
                "_",
                " "
            ).title()

        else:

            label = key.replace(
                "_",
                " "
            ).title()

        lines.append(
            f"{label}: {value}"
        )

    return "\n".join(lines)


# ============================================================
# DOCUMENT FUNCTIONS
# ============================================================

def create_document(
    user_id: int,
    filename: str,
    stored_filename: str = None,
    file_path: str = None,
    drug: str = None,
    source: str = None,
    document_id: str = None,
    pages: int = 0,
    chunks: int = 0,
    file_type: str = "pdf",
    document_key: str = None,
    file_size: int = 0,
    freshness_status: str = "unknown",
    **kwargs
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        if drug is None:

            drug = kwargs.get(
                "drug"
            )

        if source is None:

            source = kwargs.get(
                "source"
            )

        if document_id is None:

            document_id = kwargs.get(
                "document_id"
            )

        if pages is None:

            pages = kwargs.get(
                "pages",
                0
            )

        if chunks is None:

            chunks = kwargs.get(
                "chunks",
                0
            )

        if document_key is None:

            document_key = kwargs.get(
                "document_key"
            )

        if file_size is None:

            file_size = kwargs.get(
                "file_size",
                0
            )

        if freshness_status is None:

            freshness_status = kwargs.get(
                "freshness_status",
                "unknown"
            )

        now = _now()

        cursor.execute(
            """
            INSERT INTO documents
            (
                user_id,
                filename,
                stored_filename,
                file_path,
                file_type,
                drug,
                source,
                document_id,
                document_key,
                pages,
                chunks,
                file_size,
                freshness_status,
                created_at,
                uploaded_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                user_id,
                filename,
                stored_filename,
                file_path,
                file_type or "pdf",
                drug,
                source,
                document_id,
                document_key,
                pages or 0,
                chunks or 0,
                file_size or 0,
                freshness_status or "unknown",
                now,
                now
            )
        )

        database_id = cursor.lastrowid

        connection.commit()

        return database_id

    finally:

        connection.close()


def update_document_metadata(
    database_row_id: int,
    **metadata
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        allowed = {
            "drug",
            "source",
            "document_id",
            "document_key",
            "pages",
            "chunks",
            "file_size",
            "file_type",
            "freshness_status"
        }

        fields = []
        values = []

        for key, value in metadata.items():

            if key not in allowed:
                continue

            fields.append(
                f"{key} = ?"
            )

            values.append(
                value
            )

        if not fields:
            return False

        values.append(
            database_row_id
        )

        query = f"""
            UPDATE documents
            SET {", ".join(fields)}
            WHERE id = ?
        """

        cursor.execute(
            query,
            tuple(values)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        connection.close()


def get_user_documents(
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                stored_filename,
                file_path,
                file_type,
                drug,
                source,
                document_id,
                document_key,
                pages,
                chunks,
                file_size,
                freshness_status,
                created_at,
                uploaded_at
            FROM documents
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (
                user_id,
            )
        )

        rows = cursor.fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()


def get_document(
    document_database_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT *
            FROM documents
            WHERE id = ?
              AND user_id = ?
            """,
            (
                document_database_id,
                user_id
            )
        )

        row = cursor.fetchone()

        if not row:
            return None

        return dict(row)

    finally:

        connection.close()


def delete_document(
    document_id: int,
    user_id: int
):

    connection = get_connection()

    cursor = connection.cursor()

    file_path = None

    deleted = False

    try:

        cursor.execute(
            """
            SELECT
                file_path
            FROM documents
            WHERE id = ?
              AND user_id = ?
            """,
            (
                document_id,
                user_id
            )
        )

        document = cursor.fetchone()

        if not document:
            return False

        file_path = document["file_path"]

        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = ?
              AND user_id = ?
            """,
            (
                document_id,
                user_id
            )
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

    finally:

        connection.close()

    if deleted and file_path:

        try:

            if os.path.exists(
                file_path
            ):

                os.remove(
                    file_path
                )

        except Exception as error:

            print(
                "DOCUMENT FILE DELETE ERROR:",
                repr(error)
            )

    return deleted


# ============================================================
# AUDIT LOGGING
# ============================================================

def create_audit_log(
    user_id=None,
    chat_id=None,
    question="",
    answer="",
    citations=None,
    confidence=None,
    grounding_score=None,
    mode=None
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        confidence = _serialize_optional(
            confidence,
            default=None
        )

        mode = _serialize_optional(
            mode,
            default=None
        )

        grounding_score = (
            _normalize_grounding_score(
                grounding_score
            )
        )

        cursor.execute(
            """
            INSERT INTO audit_logs
            (
                user_id,
                chat_id,
                question,
                answer,
                citations_json,
                confidence,
                grounding_score,
                mode,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                chat_id,
                question or "",
                answer or "",
                _json(citations),
                confidence,
                grounding_score,
                mode,
                _now()
            )
        )

        audit_id = cursor.lastrowid

        connection.commit()

        return audit_id

    finally:

        connection.close()


# ============================================================
# FEEDBACK
# ============================================================

def create_feedback(
    user_id,
    message_id,
    rating,
    comment=""
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO feedback
            (
                user_id,
                message_id,
                rating,
                comment,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                message_id,
                rating,
                comment or "",
                _now()
            )
        )

        feedback_id = cursor.lastrowid

        connection.commit()

        return feedback_id

    finally:

        connection.close()


# ============================================================
# ANALYTICS
# ============================================================

def get_analytics(
    user_id=None
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        if user_id is None:

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_messages
                FROM messages
                WHERE role = 'user'
                """
            )

        else:

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_messages
                FROM messages m
                JOIN chats c
                    ON m.chat_id = c.id
                WHERE m.role = 'user'
                  AND c.user_id = ?
                """,
                (
                    user_id,
                )
            )

        row = cursor.fetchone()

        total_messages = (
            row["total_messages"]
            if row
            else 0
        )


        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_feedback
            FROM feedback
            """
        )

        row = cursor.fetchone()

        total_feedback = (
            row["total_feedback"]
            if row
            else 0
        )


        cursor.execute(
            """
            SELECT
                AVG(rating) AS average_rating
            FROM feedback
            """
        )

        row = cursor.fetchone()

        average_rating = (
            row["average_rating"]
            if row
            else None
        )


        return {
            "total_messages":
                total_messages or 0,

            "total_feedback":
                total_feedback or 0,

            "average_rating":
                average_rating
        }

    finally:

        connection.close()


# ============================================================
# PDF DOCUMENT HELPER
# ============================================================

def save_pdf_document(
    user_id,
    filename,
    file_path,
    stored_filename,
    upload_result=None
):

    if not isinstance(
        upload_result,
        dict
    ):

        upload_result = {}

    file_size = 0

    if (
        file_path
        and os.path.exists(file_path)
    ):

        try:

            file_size = os.path.getsize(
                file_path
            )

        except Exception:

            file_size = 0

    return create_document(
        user_id=user_id,
        filename=filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type="pdf",
        drug=upload_result.get(
            "drug"
        ),
        source=upload_result.get(
            "source"
        ),
        document_id=upload_result.get(
            "document_id"
        ),
        pages=upload_result.get(
            "pages",
            0
        ),
        chunks=upload_result.get(
            "chunks",
            0
        ),
        file_size=file_size,
        freshness_status=upload_result.get(
            "freshness_status",
            "unknown"
        )
    )





# ============================================================
# DATABASE MEMORY SUMMARY
# ============================================================

def get_memory_summary(
    user_id: int
):
    """
    Return a compact summary of the user's persistent
    memory state.

    Useful for debugging and future profile screens.
    """

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_memories
            FROM user_memories
            WHERE user_id = ?
              AND active = 1
            """,
            (
                user_id,
            )
        )

        row = cursor.fetchone()

        total_memories = (
            row["total_memories"]
            if row
            else 0
        )


        cursor.execute(
            """
            SELECT
                category,
                COUNT(*) AS count
            FROM user_memories
            WHERE user_id = ?
              AND active = 1
            GROUP BY category
            ORDER BY count DESC
            """,
            (
                user_id,
            )
        )

        category_rows = cursor.fetchall()

        categories = {
            row["category"]:
                row["count"]
            for row in category_rows
        }


        return {
            "user_id": user_id,
            "total_memories": total_memories,
            "categories": categories
        }

    finally:

        connection.close()


# ============================================================
# STARTUP
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("DRUGASSIST DATABASE")
    print("=" * 60)

    print(
        f"Database path: {DB_PATH}"
    )

    init_database()

    print(
        "Database initialized successfully."
    )

    print(
        "Long-term memory table ready."
    )

    print(
        "Conversation search ready."
    )

    print("=" * 60)