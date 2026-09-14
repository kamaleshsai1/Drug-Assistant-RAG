import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from groq import Groq

from pinecone_db import search_pinecone
from image_analyzer import analyze_image


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

FALLBACK_MODEL = os.getenv(
    "GROQ_FALLBACK_MODEL",
    "openai/gpt-oss-120b"
)

RETRIEVAL_K = int(
    os.getenv("RAG_RETRIEVAL_K", "15")
)

CONTEXT_K = int(
    os.getenv("RAG_CONTEXT_K", "8")
)

MIN_SCORE = float(
    os.getenv("RAG_MIN_SCORE", "0.20")
)

MAX_CHUNK_CHARS = int(
    os.getenv("RAG_MAX_CHUNK_CHARS", "3500")
)

MAX_COMPLETION_TOKENS = int(
    os.getenv("GROQ_MAX_COMPLETION_TOKENS", "2048")
)

MAX_HISTORY_MESSAGES = int(
    os.getenv("MAX_CONVERSATION_HISTORY", "12")
)

MAX_MEMORY_ITEMS = int(
    os.getenv("MAX_LONG_TERM_MEMORIES", "20")
)


# ============================================================
# CONSTANTS
# ============================================================

INSUFFICIENT_EVIDENCE = (
    "I couldn't find enough information about that "
    "in the provided drug information."
)

PERSONAL_MEDICAL_RESPONSE = (
    "I can provide general information about medicines "
    "from the supplied prescribing information, but I "
    "cannot provide personalized medical advice or "
    "recommend what you personally should take or change. "
    "Please consult a qualified healthcare professional "
    "for advice specific to you."
)


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_pdf_text(text: Any) -> str:
    if not text:
        return ""

    text = str(text)

    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
        " ",
        text
    )

    text = re.sub(
        r"(?<=\w)-\s*\n\s*(?=\w)",
        "",
        text
    )

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_answer_format(answer: str) -> str:
    if not answer:
        return ""

    answer = normalize_citations(answer)

    # Standardize dashes (replace em dashes and en dashes)
    answer = answer.replace("\u2014", " - ").replace("\u2013", " - ")

    # Strip emoji symbols to maintain clean clinical presentation
    answer = re.sub(
        r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\U0001f300-\U0001f9ff]",
        "",
        answer
    )

    answer = re.sub(
        r"^```(?:markdown|text)?\s*",
        "",
        answer,
        flags=re.IGNORECASE
    )

    answer = re.sub(
        r"\s*```$",
        "",
        answer
    )

    answer = re.sub(
        r"[ \t]+",
        " ",
        answer
    )

    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    )

    return answer.strip()


def normalize_drug_name(drug: Any) -> str:
    if not drug:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(drug).lower()
    )


def normalize_image_context(image_context: Any) -> str:
    if not image_context:
        return ""

    if isinstance(image_context, str):
        return image_context.strip()

    if isinstance(image_context, list):
        parts = []

        for item in image_context:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                text = (
                    item.get("analysis")
                    or item.get("text")
                    or item.get("content")
                    or ""
                )

                if text:
                    parts.append(str(text))

        return "\n".join(parts).strip()

    if isinstance(image_context, dict):
        return str(
            image_context.get("analysis")
            or image_context.get("text")
            or image_context.get("content")
            or ""
        ).strip()

    return str(image_context).strip()


# ============================================================
# PINECONE NORMALIZATION
# ============================================================

def normalize_match(match: Any) -> Optional[Dict[str, Any]]:
    if match is None:
        return None

    if isinstance(match, dict):
        return {
            "id": match.get("id"),
            "score": float(match.get("score", 0) or 0),
            "metadata": match.get("metadata", {}) or {}
        }

    if hasattr(match, "id"):
        return {
            "id": getattr(match, "id", None),
            "score": float(
                getattr(match, "score", 0) or 0
            ),
            "metadata": (
                getattr(match, "metadata", {}) or {}
            )
        }

    return None


def extract_matches(raw_results: Any) -> List[Any]:
    if raw_results is None:
        return []

    if isinstance(raw_results, dict):
        return raw_results.get("matches", []) or []

    if hasattr(raw_results, "matches"):
        return raw_results.matches or []

    return []


# ============================================================
# MEDICAL CONDITIONS MAPPING
# ============================================================

KNOWN_CONDITIONS_MAP = [
    ("atopic dermatitis", ["atopic dermatitis", "eczema", "ezcema", "ad"]),
    ("rheumatoid arthritis", ["rheumatoid arthritis", "ra"]),
    ("psoriatic arthritis", ["psoriatic arthritis", "psa", "psoriasis"]),
    ("ankylosing spondylitis", ["ankylosing spondylitis", "as"]),
    ("non-radiographic axial spondyloarthritis", ["non-radiographic axial spondyloarthritis", "nr-axspa", "axial spondyloarthritis", "axspa"]),
    ("ulcerative colitis", ["ulcerative colitis", "uc"]),
    ("crohn's disease", ["crohn's disease", "crohn's", "crohns disease", "crohns", "crohn", "cd"]),
    ("polyarticular juvenile idiopathic arthritis", ["polyarticular juvenile idiopathic arthritis", "pjia", "juvenile idiopathic arthritis", "jia"]),
    ("giant cell arteritis", ["giant cell arteritis", "gca"]),
    ("renal impairment", ["renal impairment", "kidney impairment", "kidney disease", "renal disease", "egfr", "kidney"]),
    ("hepatic impairment", ["hepatic impairment", "liver impairment", "liver disease", "hepatic"]),
]

def extract_condition_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    for canonical, aliases in KNOWN_CONDITIONS_MAP:
        for alias in sorted(aliases, key=len, reverse=True):
            if re.search(r"\b" + re.escape(alias) + r"\b", t):
                return canonical
    return None


# ============================================================
# QUERY / DRUG DETECTION
# ============================================================

def build_query_variations(question: str) -> List[str]:
    question = (question or "").strip()

    if not question:
        return []

    variations = [
        question,
        f"prescribing information {question}"
    ]

    cond = extract_condition_from_text(question)
    if cond:
        variations.append(f"RINVOQ {cond}")
        variations.append(f"{cond} prescribing information")

    q_lower = question.lower()
    if any(w in q_lower for w in ["dosage", "dose", "dosing", "administration"]):
        variations.append(f"{question} recommended dosage")
        variations.append(f"Section 2 dosage and administration {question}")
        if cond:
            variations.append(f"RINVOQ recommended dosage in {cond}")
    elif any(w in q_lower for w in ["side effect", "adverse", "safety", "reaction"]):
        variations.append(f"Section 6 adverse reactions {question}")
    elif any(w in q_lower for w in ["warning", "precaution", "boxed warning"]):
        variations.append(f"Section 5 warnings and precautions {question}")

    return variations


def extract_explicit_drug_name(
    question: str
) -> Optional[str]:

    question = (question or "").strip()

    if not question:
        return None

    patterns = [
        (
            r"\b(?:dosage|dose|side\s+effects?|uses?|indications?|warnings?|contraindications?|interactions?)\s+(?:of|for)\s+"
            r"([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)"
            r"(?:\s+for|\s+in|\s*[?.!,]|$)"
        ),
        (
            r"\b(?:of|about|regarding)\s+"
            r"([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)"
            r"(?:\s+for|\s+in|\s*[?.!,]|$)"
        ),
        (
            r"\bwhat\s+is\s+"
            r"([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)"
            r"\s+(?:used\s+for|dosage|dose|side\s+effects|uses|indications|warnings|contraindications|interactions)\b"
        ),
        (
            r"\b(?:tell\s+me\s+about|information\s+about)\s+"
            r"([A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)"
            r"(?:\s*[?.!,]|$)"
        )
    ]

    stop_words = {
        "the", "a", "an", "this", "that", "these", "those",
        "recommended", "patient", "adult", "adults", "pediatric",
        "child", "children", "drug", "medicine", "medication",
        "treatment", "therapy", "induction", "maintenance",
        "disease", "condition", "illness", "infection",
        "what", "how", "when", "why", "where", "which"
    }

    for pattern in patterns:
        match = re.search(
            pattern,
            question,
            re.IGNORECASE
        )

        if not match:
            continue

        candidate = match.group(1).strip(
            " .?!,"
        )

        candidate = re.sub(
            r"\s+(?:tablets?|medication|medicine)\s*$",
            "",
            candidate,
            flags=re.IGNORECASE
        ).strip()

        if candidate and candidate.lower() not in stop_words:
            return candidate

    return None


def detect_drug_from_question(
    question: str,
    initial_matches: Optional[List[Any]] = None
) -> Optional[str]:

    question = (question or "").strip()

    if not question:
        return None

    candidate_drugs = []

    if initial_matches:
        for match in initial_matches:
            normalized = normalize_match(match)

            if not normalized:
                continue

            metadata = normalized.get(
                "metadata",
                {}
            ) or {}

            drug = metadata.get("drug")

            if drug and drug not in candidate_drugs:
                candidate_drugs.append(str(drug))

    explicit_drug = extract_explicit_drug_name(
        question
    )

    if explicit_drug:
        explicit_normalized = normalize_drug_name(
            explicit_drug
        )

        for drug in candidate_drugs:
            if (
                normalize_drug_name(drug)
                == explicit_normalized
            ):
                return drug

        for drug in candidate_drugs:
            indexed = normalize_drug_name(drug)

            if (
                explicit_normalized in indexed
                or indexed in explicit_normalized
            ):
                return drug

        explicit_words = {
            normalize_drug_name(word)
            for word in re.findall(
                r"[A-Za-z0-9]+",
                explicit_drug
            )
            if len(normalize_drug_name(word)) >= 4
        }

        for drug in candidate_drugs:
            indexed_words = {
                normalize_drug_name(word)
                for word in re.findall(
                    r"[A-Za-z0-9]+",
                    drug
                )
                if len(normalize_drug_name(word)) >= 4
            }

            if explicit_words.intersection(
                indexed_words
            ):
                return drug

        best_drug = None
        best_score = 0.0

        for drug in candidate_drugs:
            indexed = normalize_drug_name(drug)

            similarity = SequenceMatcher(
                None,
                explicit_normalized,
                indexed
            ).ratio()

            if similarity > best_score:
                best_score = similarity
                best_drug = drug

        if best_score >= 0.85:
            return best_drug

        return None

    question_normalized = normalize_drug_name(
        question
    )

    for drug in candidate_drugs:
        indexed = normalize_drug_name(drug)

        if (
            indexed
            and indexed in question_normalized
        ):
            return drug

    return None


# ============================================================
# GENERAL CONVERSATION DETECTION
# ============================================================

def is_general_conversation_question(
    question: str
) -> bool:

    q = (question or "").strip().lower()

    if not q:
        return False

    medical_terms = [
        "drug",
        "medicine",
        "medication",
        "tablet",
        "capsule",
        "dose",
        "dosage",
        "prescription",
        "prescribing",
        "side effect",
        "side effects",
        "adverse",
        "indication",
        "contraindication",
        "interaction",
        "hypertension",
        "blood pressure",
        "symptom",
        "symptoms",
        "disease",
        "condition",
        "treatment",
        "diagnosis",
        "overdose",
        "allergy",
        "allergic",
        "pregnant",
        "pregnancy",
        "milligram",
        "milligrams",
        "medical",
        "doctor",
        "pharmacy",
        "pharmacist",
        "losartan",
        "alleroff"
    ]

    if any(term in q for term in medical_terms):
        return False

    patterns = [
        r"^hi[!. ]*$",
        r"^hello[!. ]*$",
        r"^hey[!. ]*$",
        r"^heyy*[!. ]*$",
        r"^good morning[!. ]*$",
        r"^good afternoon[!. ]*$",
        r"^good evening[!. ]*$",
        r"^good night[!. ]*$",
        r"^how are you[?!. ]*$",
        r"^how r u[?!. ]*$",
        r"^what are you[?!. ]*$",
        r"^who are you[?!. ]*$",
        r"^what can you do[?!. ]*$",
        r"^what do you do[?!. ]*$",
        r"^thanks[!. ]*$",
        r"^thank you[!. ]*$",
        r"^thx[!. ]*$",
        r"^bye[!. ]*$",
        r"^goodbye[!. ]*$",
        r"^tell me a joke[?!. ]*$",
        r"^tell me something funny[?!. ]*$",
        r"^make me laugh[?!. ]*$",
        r"^tell me a story[?!. ]*$",
        r"^can you tell me a joke[?!. ]*$",
        r"^can u tell me a joke[?!. ]*$",
        r"^say something funny[?!. ]*$"
    ]

    if any(
        re.search(pattern, q)
        for pattern in patterns
    ):
        return True

    # Casual emotional statements.
    # These are checked before follow-up handling so that a phrase
    # such as "its bad" is not mistaken for a drug follow-up merely
    # because "its" can refer to something mentioned earlier.
    casual_patterns = [
        r"^i('?m| am) (good|fine|okay|ok|bad|sad|happy|tired|bored|upset|angry)\b",
        r"^(it|it\'s|its) (really |very |so |too )?(good|fine|okay|ok|bad|sad|happy|great|terrible|awful|rough)\b",
        r"^(that|that\'s|thats) (really |very |so |too )?(good|fine|okay|ok|bad|sad|happy|great|terrible|awful|rough)\b",
        r"^(today|my day) (is|was|has been)\b",
        r"^my day\b",
        r"^i feel\b",
        r"^i\'m feeling\b",
        r"^im feeling\b",
        r"^i had a\b",
        r"^today was\b",
        r"^life is\b",
        r"^i hate\b",
        r"^i love\b",
        r"^i like\b",
        r"^i don\'t like\b",
        r"^i dont like\b",
        r"^(really |very |so |too )?(good|fine|okay|ok|bad|sad|happy|great|terrible|awful|rough|horrible)\b",

        # Short conversational acknowledgements stay in general chat.
        # They must not trigger drug retrieval just because an earlier
        # message in the conversation mentioned a medicine.
        r"^(yes|yeah|yep|yup|no|nope|okay|ok|alright|all right|sure|fine|thanks|thank you|got it|i see)[!.? ]*$"
    ]

    return any(
        re.search(pattern, q)
        for pattern in casual_patterns
    )


# ============================================================
# FOLLOW-UP DETECTION
# ============================================================

def is_follow_up_question(
    question: str
) -> bool:

    q = (question or "").strip().lower()

    if not q:
        return False

    patterns = [
        r"^what about\b",
        r"^how about\b",
        r"^and\b",
        r"^also\b",
        r"^what else\b",
        r"^anything else\b",
        r"^tell me more\b",
        r"^explain more\b",
        r"^more about\b",
        r"^why\b",
        r"^how\b",
        r"^which one\b",
        r"^that one\b",
        r"^this one\b",
        r"^it\b",
        r"^its\b",
        r"^they\b",
        r"^them\b",
        r"^another one\b",
        r"^one more\b",
        r"^again\b",
        r"^what about it\b",
        r"^and then\b",
        r"\b(?:this|that|these|those|the same)\s+(?:drug|medicine|medication|condition|disease|patient|dose|dosage|indication|illness)\b",
        r"\b(?:its|their)\s+(?:dose|dosage|side effects?|uses?|warnings?|contraindications?|safety)\b",
        r"\b(?:for|in|of|about|with)\s+this\s+condition\b",
        r"\b(?:for|of|in|about|with)\s+(?:that|this|it|the same)\b",
        r"\b(?:for|of)\s+(?:that|this|it)\b",
        r"^(?:what\s+is\s+the\s+)?(?:recommended\s+)?(?:dosage|dose|dosing|administration)(?:\s+(?:for|of|in|about)\s+(?:that|this|it))?\??$",
        r"^(?:what\s+are\s+the\s+)?(?:side\s+effects?|adverse\s+reactions?|warnings?|precautions?|contraindications?)(?:\s+(?:for|of|in|about)\s+(?:that|this|it))?\??$",
        r"^(?:how\s+to\s+take|how\s+should\s+it\s+be\s+taken|how\s+much\s+to\s+take)(?:\s+(?:for|of|in|about)\s+(?:that|this|it))?\??$",
        r"\b(?:dose|dosage|side\s+effects?|safety|warnings?)\s+(?:of|for)\s+(?:it|that|this)\b"
    ]

    return any(
        re.search(pattern, q)
        for pattern in patterns
    )


# ============================================================
# EMERGENCY / MEDICAL SAFETY
# ============================================================

def is_emergency_question(question: str) -> bool:

    q = (question or "").lower()

    patterns = [
        "overdose",
        "overdosed",
        "took too much",
        "taken too much",
        "can't breathe",
        "cannot breathe",
        "difficulty breathing",
        "chest pain",
        "unconscious",
        "passed out",
        "seizure",
        "severe allergic reaction",
        "swelling of the face",
        "swelling of throat"
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


def emergency_response() -> str:
    return (
        "This may require urgent medical attention. "
        "If someone has taken too much medicine, is having "
        "difficulty breathing, has severe chest pain, is "
        "unconscious, or is experiencing another serious "
        "reaction, contact local emergency services or a "
        "poison-control service immediately. Do not rely on "
        "this chatbot for emergency treatment decisions."
    )


def is_personal_medical_question(
    question: str
) -> bool:

    q = (question or "").lower()

    patterns = [
        "should i take",
        "can i take",
        "can i use",
        "should i use",
        "is it safe for me",
        "what should i take",
        "which medicine should i take",
        "what medicine should i take",
        "my symptoms",
        "my condition",
        "my disease",
        "for me",
        "for my",
        "i am pregnant",
        "i'm pregnant",
        "my pregnancy",
        "my blood pressure",
        "my dosage",
        "increase my dose",
        "decrease my dose",
        "stop taking",
        "should i stop",
        "can i stop",
        "change my dose",
        "change my medication",
        "prescribe me",
        "write me a prescription",
        "give me a prescription",
        "can you prescribe",
        "diagnose me",
        "what disease do i have",
        "do i have",
        "recommend a medication for me",
        "how much should i take",
        "how many should i take"
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


# ============================================================
# LONG-TERM MEMORY
# ============================================================

def load_long_term_memories(
    user_id: Optional[int]
) -> List[Dict[str, Any]]:

    if not user_id:
        return []

    try:
        try:
            from database.database import get_user_memories
        except ImportError:
            from database import get_user_memories

        memories = get_user_memories(
            user_id
        )

        if not memories:
            return []

        return memories[:MAX_MEMORY_ITEMS]

    except Exception as error:
        print(
            "[Memory] Could not load memories:",
            repr(error)
        )
        return []


def format_memories(
    memories: Optional[List[Dict[str, Any]]]
) -> str:

    if not memories:
        return ""

    lines = []

    for memory in memories:
        if not isinstance(memory, dict):
            continue

        key = memory.get("memory_key")
        value = memory.get("memory_value")

        if not key or not value:
            continue

        lines.append(
            f"- {key}: {value}"
        )

    return "\n".join(lines)


def detect_memory_candidates(
    question: str
) -> List[Dict[str, str]]:

    q = (question or "").strip()

    memories = []

    patterns = [
        (
            r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,80})",
            "name",
            "personal"
        ),
        (
            r"\bcall me\s+([A-Za-z][A-Za-z .'-]{1,80})",
            "name",
            "personal"
        ),
        (
            r"\bi am\s+([A-Za-z][A-Za-z .'-]{1,50})",
            "name",
            "personal"
        ),
        (
            r"\bi'm\s+([A-Za-z][A-Za-z .'-]{1,50})",
            "name",
            "personal"
        )
    ]

    for pattern, key, category in patterns:
        match = re.search(
            pattern,
            q,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(1).strip(
            " .,!?"
        )

        # Avoid storing obvious emotional/state statements.
        bad_values = {
            "good",
            "fine",
            "okay",
            "ok",
            "sad",
            "happy",
            "tired",
            "bored",
            "angry",
            "having",
            "feeling"
        }

        if value.lower() in bad_values:
            continue

        if len(value) <= 60:
            memories.append(
                {
                    "memory_key": key,
                    "memory_value": value,
                    "category": category,
                    "importance": "1.0"
                }
            )

        break

    return memories


def save_memory_candidates(
    user_id: Optional[int],
    question: str,
    chat_id: Optional[int] = None
) -> None:

    if not user_id:
        return

    candidates = detect_memory_candidates(
        question
    )

    if not candidates:
        return

    try:
        try:
            from database.database import upsert_memory
        except ImportError:
            from database import upsert_memory

        for item in candidates:
            upsert_memory(
                user_id,
                item["memory_key"],
                item["memory_value"],
                item["category"],
                float(item["importance"])
            )

            print(
                "[Memory] Saved:",
                item["memory_key"],
                "=",
                item["memory_value"]
            )

    except Exception as error:
        print(
            "[Memory] Save failed:",
            repr(error)
        )


# ============================================================
# CONVERSATION HISTORY
# ============================================================

def normalize_history(
    history: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, str]]:

    if not history:
        return []

    result = []

    for item in history:
        if not isinstance(item, dict):
            continue

        role = item.get("role")

        if role not in {
            "user",
            "assistant",
            "system"
        }:
            continue

        content = (
            item.get("content")
            or item.get("answer")
            or item.get("text")
            or ""
        )

        if not content:
            continue

        result.append(
            {
                "role": role,
                "content": str(content)
            }
        )

    return result[-MAX_HISTORY_MESSAGES:]


def history_to_text(
    history: Optional[List[Dict[str, Any]]]
) -> str:

    normalized = normalize_history(
        history
    )

    if not normalized:
        return ""

    lines = []

    for item in normalized:
        role = item["role"].upper()
        content = item["content"]

        lines.append(
            f"{role}: {content}"
        )

    return "\n".join(lines)


# ============================================================
# CONTEXT-AWARE QUERY REFORMULATION
# ============================================================

def build_contextual_question(
    question: str,
    history: Optional[List[Dict[str, Any]]] = None
) -> str:

    question = (question or "").strip()

    if not question:
        return ""

    if not history:
        return question

    if not is_follow_up_question(question):
        return question

    # Extract last user and assistant turns
    last_user = ""
    last_assistant = ""
    for item in reversed(history):
        role = str(item.get("role", "")).lower()
        content = str(item.get("content", ""))
        if role == "user" and not last_user:
            last_user = content
        elif role == "assistant" and not last_assistant:
            last_assistant = content
        if last_user and last_assistant:
            break

    # Determine drug from question or history (default RINVOQ)
    drug = (
        extract_explicit_drug_name(question)
        or extract_explicit_drug_name(last_user)
        or detect_drug_from_question(question)
        or detect_drug_from_question(last_user)
        or "RINVOQ"
    )

    # Check for known medical condition
    cond = (
        extract_condition_from_text(question)
        or extract_condition_from_text(last_user)
        or extract_condition_from_text(last_assistant)
    )

    q_lower = question.lower()
    is_dosage = any(w in q_lower for w in ["dosage", "dose", "dosing", "how much", "administration", "take it", "how to take"])
    is_safety = any(w in q_lower for w in ["side effect", "side effects", "adverse", "reaction", "safety", "risk", "safe"])
    is_warning = any(w in q_lower for w in ["warning", "warnings", "contraindication", "contraindications", "precaution"])

    if cond:
        extra_label = " eczema" if cond == "atopic dermatitis" else ""
        if is_dosage:
            return f"{drug} recommended dosage in {cond}{extra_label}"
        elif is_safety:
            return f"{drug} adverse reactions side effects {cond}{extra_label}"
        elif is_warning:
            return f"{drug} warnings precautions {cond}{extra_label}"
        else:
            return f"{drug} {cond}{extra_label} {question}"

    # If no known condition matched, try fast LLM query reformulation
    try:
        htext = history_to_text(history[-4:])
        prompt = (
            f"Given the conversation history and the user's follow-up question, "
            f"rewrite the question into a single standalone medical search query. "
            f"Resolve any pronouns (such as 'that', 'it', 'this') using the conversation context. "
            f"Mention the drug ({drug}) and the medical condition or topic being discussed.\n"
            f"Return ONLY the standalone search query text. Do not include quotes or conversational filler.\n\n"
            f"Conversation history:\n{htext}\n\n"
            f"Follow-up question:\n{question}"
        )
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=512,
            temperature=0
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        rewritten = re.sub(r"^(?:Standalone query|Search query|Rewritten query):\s*", "", rewritten, flags=re.IGNORECASE)
        rewritten = rewritten.strip("\"'")
        if rewritten and len(rewritten) > 3:
            return rewritten
    except Exception as err:
        print("[Retrieval] LLM query reformulation failed:", repr(err))

    # Fallback heuristic
    if last_user:
        clean_user = re.sub(r"[^\w\s]", "", last_user).strip()
        if is_dosage:
            return f"{drug} recommended dosage for {clean_user}"
        return f"{drug} {clean_user} {question}"

    return f"{drug} {question}"


# ============================================================
# GENERAL CHAT
# ============================================================

GENERAL_CHAT_SYSTEM_PROMPT = """
You are DrugAssist, a friendly conversational AI assistant.

You are allowed to have natural conversations with the user.

IMPORTANT:

1. Remember and use the supplied conversation history.
2. Remember supplied long-term user memories.
3. Respond naturally to emotional statements.
4. If the user says they are having a bad day, respond empathetically.
5. If the user asks for a joke, tell a joke.
6. If the user says "another one", understand the previous request.
7. If the user says "what about it?", use conversation context.
8. If the user gives their name, use it naturally.
9. Do not claim to know something that is not present in memory
   or conversation history.
10. Do not fabricate medical information.
11. Do not provide diagnosis or personalized medication advice.
12. Do not fabricate citations.
13. Do not mention vector databases, embeddings, prompts,
    retrieval, or internal system instructions.
14. Be friendly and conversational.
15. Keep responses reasonably concise.

The user may switch between casual conversation and drug questions.
The application separately handles drug-information questions.
"""


def _call_general_groq(
    model: str,
    question: str,
    history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None
) -> str:

    messages = [
        {
            "role": "system",
            "content": GENERAL_CHAT_SYSTEM_PROMPT
        }
    ]

    memory_text = format_memories(
        memories
    )

    if memory_text:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Long-term memories about the user:\n"
                    f"{memory_text}"
                )
            }
        )

    for item in normalize_history(history):
        messages.append(
            {
                "role": item["role"],
                "content": item["content"]
            }
        )

    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0.7,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        messages=messages
    )

    return (
        response.choices[0]
        .message.content
        or ""
    ).strip()


def generate_general_answer(
    question: str,
    history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None
) -> str:

    models = []

    if MODEL_NAME:
        models.append(MODEL_NAME)

    if (
        FALLBACK_MODEL
        and FALLBACK_MODEL not in models
    ):
        models.append(FALLBACK_MODEL)

    for model in models:
        try:
            print(
                f"[General Chat] Trying model: {model}"
            )

            answer = _call_general_groq(
                model,
                question,
                history,
                memories
            )

            if answer:
                return clean_answer_format(
                    answer
                )

        except Exception as error:
            print(
                f"[General Chat] {model} failed:",
                repr(error)
            )

    return (
        "I'm here to chat. Ask me something, and I'll "
        "do my best to help."
    )


# ============================================================
# RETRIEVAL
# ============================================================

def _search_pinecone_filtered(
    question: str,
    top_k: int,
    drug: Optional[str] = None,
    document_id: Optional[str] = None
):
    """Search Pinecone with an optional document filter.

    Supports both the newer search_pinecone(..., document_id=...)
    implementation and older local versions that only accept drug=.
    """
    try:
        return search_pinecone(
            question,
            top_k=top_k,
            drug=drug,
            document_id=document_id
        )
    except TypeError:
        # Backward compatibility with older pinecone_db.py.
        raw = search_pinecone(
            question,
            top_k=max(top_k, 50) if document_id else top_k,
            drug=drug
        )

        if not document_id:
            return raw

        matches = extract_matches(raw)
        filtered = []

        for match in matches:
            normalized = normalize_match(match)
            if not normalized:
                continue

            metadata = normalized.get("metadata", {}) or {}
            if str(metadata.get("document_id", "")) == str(document_id):
                filtered.append(match)

        return {"matches": filtered[:top_k]}


def retrieve_documents(
    question: str,
    image_context: Any = None,
    document_id: Optional[str] = None
) -> List[Dict[str, Any]]:

    question = (question or "").strip()

    if not question:
        return []

    image_text = normalize_image_context(
        image_context
    )

    retrieval_question = question

    if image_text:
        retrieval_question = (
            f"{question}\n\n"
            "Visible information from uploaded image:\n"
            f"{image_text[:2500]}"
        )

    print()
    print("=" * 60)
    print("DRUGASSIST RETRIEVAL")
    print("=" * 60)

    try:
        initial_results = _search_pinecone_filtered(
            retrieval_question,
            top_k=RETRIEVAL_K,
            document_id=document_id
        )

        initial_matches = extract_matches(
            initial_results
        )

    except Exception as error:
        print(
            "[Retrieval] Initial search failed:",
            repr(error)
        )
        initial_matches = []

    detected_drug = detect_drug_from_question(
        question,
        initial_matches
    )

    if not detected_drug and retrieval_question != question:
        detected_drug = detect_drug_from_question(
            retrieval_question,
            initial_matches
        )

    explicit_drug = extract_explicit_drug_name(
        question
    )

    if not explicit_drug and retrieval_question != question:
        explicit_drug = extract_explicit_drug_name(
            retrieval_question
        )

    if explicit_drug and not detected_drug:
        print(
            f"[Retrieval] Drug candidate '{explicit_drug}' not strictly mapped; falling back to dense semantic retrieval."
        )

    if detected_drug:
        print(
            "[Retrieval] Drug:",
            detected_drug
        )

    queries = build_query_variations(
        retrieval_question
    )

    all_matches = {}

    for query in queries:

        try:
            raw_results = _search_pinecone_filtered(
                query,
                top_k=RETRIEVAL_K,
                drug=detected_drug,
                document_id=document_id
            )

        except Exception as error:
            print(
                "[Retrieval] Search failed:",
                repr(error)
            )
            continue

        matches = extract_matches(
            raw_results
        )

        for match in matches:

            normalized = normalize_match(
                match
            )

            if not normalized:
                continue

            match_id = normalized.get("id")

            score = float(
                normalized.get("score", 0) or 0
            )

            metadata = (
                normalized.get("metadata", {})
                or {}
            )

            if score < MIN_SCORE:
                continue

            if not metadata.get("document_id"):
                continue

            if not metadata.get("text"):
                continue

            if detected_drug:

                result_drug = str(
                    metadata.get("drug", "")
                )

                # Skip only if result_drug is clearly a different known drug
                if (
                    result_drug
                    and result_drug.lower() not in {"unknown", "warning", "recent major changes"}
                    and normalize_drug_name(result_drug) != normalize_drug_name(detected_drug)
                    and normalize_drug_name(detected_drug) not in normalize_drug_name(result_drug)
                    and normalize_drug_name(result_drug) not in normalize_drug_name(detected_drug)
                ):
                    continue

            if not match_id:
                continue

            # Deduplicate semantically identical chunks across duplicate document uploads
            content_key = (
                str(metadata.get("page", "")),
                str(metadata.get("section", "")),
                clean_pdf_text(metadata.get("text", ""))[:200]
            )

            if (
                content_key not in all_matches
                or score >
                all_matches[content_key]["score"]
            ):
                all_matches[content_key] = normalized

    sorted_matches = sorted(
        all_matches.values(),
        key=lambda item: item.get(
            "score",
            0
        ),
        reverse=True
    )

    final_matches = sorted_matches[
        :CONTEXT_K
    ]

    print(
        f"[Retrieval] Valid matches: "
        f"{len(sorted_matches)}"
    )

    print(
        f"[Retrieval] Context matches: "
        f"{len(final_matches)}"
    )

    return final_matches


# ============================================================
# CONTEXT BUILDING
# ============================================================

def build_context(
    matches: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:

    context_parts = []
    sources = []

    seen_chunks = set()
    source_number = 1

    for match in matches:

        metadata = (
            match.get("metadata", {})
            or {}
        )

        text = clean_pdf_text(
            metadata.get("text", "")
        )

        page = metadata.get("page")
        source = metadata.get(
            "source",
            "Unknown source"
        )
        drug = metadata.get(
            "drug",
            "Unknown drug"
        )
        document_id = metadata.get(
            "document_id"
        )
        section = metadata.get(
            "section",
            ""
        )

        if (
            not text
            or page is None
            or not document_id
        ):
            continue

        try:
            page_number = int(page)
        except (TypeError, ValueError):
            continue

        chunk_key = (
            str(page_number),
            text.strip()
        )

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)

        context_text = text[
            :MAX_CHUNK_CHARS
        ]

        context_parts.append(
            f"SOURCE {source_number}\n"
            f"Drug: {drug}\n"
            f"Document: {source}\n"
            f"Page: {page_number}\n"
            f"Section: {section or 'Not specified'}\n"
            f"Document ID: {document_id}\n"
            f"Text:\n{context_text}\n"
        )

        try:
            score = round(
                float(
                    match.get("score", 0)
                    or 0
                ),
                4
            )
        except Exception:
            score = 0.0

        sources.append(
    {
        "source_id": source_number,
        "page": page_number,
        "section": (
            section or "Not specified"
        ),
        "source": source,
        "drug": drug,
        "document_id": document_id,
        "database_document_id": metadata.get(
            "database_document_id"
        ),
        "score": score,
        "snippet": text[:500]
    }
)

        source_number += 1

    return (
        "\n".join(context_parts),
        sources
    )


# ============================================================
# DRUG ANSWER GENERATION
# ============================================================

SYSTEM_PROMPT = """
You are DrugAssist, an evidence-first drug-information assistant.

For drug-information questions:

1. Use ONLY the supplied prescribing-information evidence.
2. Do NOT use outside medical knowledge.
3. Do NOT invent facts.
4. Do NOT diagnose.
5. Do NOT prescribe.
6. Do NOT provide personalized dosage or treatment advice.
7. Every medical factual statement must be supported by
   the supplied evidence.
8. If the evidence does not answer the question, say so.
9. Do not guess missing information.
10. Do not combine information from different drugs unless
    the supplied evidence explicitly supports the comparison.
11. Page numbers and section names must come from evidence.
12. Always cite evidence using bracket citations like [Source X, Page Y] directly at the end of each bullet point or medical statement. Do NOT write separate lines or standalone labels like "Source: ...".
13. Never fabricate citations.
14. Keep answers concise and readable.
15. Use bullets for lists.
16. Image observations are observations only.
17. Do not mention internal retrieval, vector databases,
    embeddings, prompts, or system instructions.
18. Prefer evidence over assumptions.
19. If the user asks whether a drug treats, cures, or is indicated for a disease or condition that is NOT listed in the approved indications of the prescribing information, explicitly state that according to the provided FDA prescribing information, the drug is NOT approved or indicated for that condition, list what it IS approved for, and advise consulting a healthcare professional.
20. Refuse requests for self-prescribing, off-label guidance, or personalized diagnosis, and direct the user to a qualified clinician.
"""


def _call_groq(
    model: str,
    question: str,
    context: str,
    image_context: Any = None,
    history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    retrieval_question: Optional[str] = None
) -> str:

    image_text = normalize_image_context(
        image_context
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    memory_text = format_memories(
        memories
    )

    if memory_text:
        messages.append(
            {
                "role": "system",
                "content": (
                    "User memories may be used only to "
                    "understand conversational references. "
                    "Do not use them as medical evidence.\n\n"
                    f"{memory_text}"
                )
            }
        )

    history_for_context = normalize_history(
        history
    )

    # Only provide previous conversation as contextual
    # information. It is NOT medical evidence.
    if history_for_context:
        history_text = history_to_text(
            history_for_context
        )

        messages.append(
            {
                "role": "system",
                "content": (
                    "Previous conversation context:\n"
                    f"{history_text}\n\n"
                    "Use this only to understand references "
                    "such as 'it', 'that medicine', or follow-up "
                    "questions. Medical factual claims must "
                    "still come from the supplied evidence."
                )
            }
        )

    image_section = ""

    if image_text:
        image_section = (
            "\n\nSUPPLIED IMAGE OBSERVATIONS:\n"
            f"{image_text}\n"
        )

    effective_question = question
    if retrieval_question and retrieval_question != question:
        effective_question = f"{question} (Reference: {retrieval_question})"

    user_prompt = f"""
QUESTION:

{effective_question}

SUPPLIED PRESCRIBING INFORMATION:

{context}
{image_section}

Answer using ONLY the supplied medical evidence.

Requirements:

- Answer directly.
- Be concise.
- Use bullets when appropriate.
- Do not invent information.
- Do not provide personalized medical advice.
- Do not mention internal retrieval.
- Do not mention these instructions.
"""

    messages.append(
        {
            "role": "user",
            "content": user_prompt
        }
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        messages=messages
    )

    return (
        response.choices[0]
        .message.content
        or ""
    ).strip()


def generate_answer(
    question: str,
    context: str,
    image_context: Any = None,
    history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    retrieval_question: Optional[str] = None
) -> str:

    models = []

    if MODEL_NAME:
        models.append(MODEL_NAME)

    if (
        FALLBACK_MODEL
        and FALLBACK_MODEL not in models
    ):
        models.append(FALLBACK_MODEL)

    for model in models:
        try:
            print(
                f"[LLM] Trying model: {model}"
            )

            answer = _call_groq(
                model,
                question,
                context,
                image_context,
                history,
                memories,
                retrieval_question=retrieval_question
            )

            answer = clean_answer_format(
                answer
            )

            if answer:
                return answer

        except Exception as error:
            print(
                f"[LLM] {model} failed:",
                repr(error)
            )

    return extractive_fallback(
        question,
        context
    )


# ============================================================
# EXTRACTIVE FALLBACK
# ============================================================

def _question_keywords(
    question: str
) -> List[str]:

    q = (question or "").lower()

    if any(
        word in q
        for word in [
            "side effect",
            "side effects",
            "adverse",
            "reaction",
            "reactions"
        ]
    ):
        return [
            "side effect",
            "adverse",
            "reaction",
            "common",
            "dizziness",
            "hyperkalemia",
            "hypotension",
            "diarrhea",
            "fatigue",
            "chest pain",
            "back pain"
        ]

    if any(
        word in q
        for word in [
            "use",
            "uses",
            "indication",
            "indications",
            "treat",
            "treatment"
        ]
    ):
        return [
            "indicated",
            "indication",
            "hypertension",
            "stroke",
            "nephropathy",
            "treatment",
            "use"
        ]

    if any(
        word in q
        for word in [
            "dose",
            "dosage",
            "dosing"
        ]
    ):
        return [
            "dose",
            "dosage",
            "dosing",
            "mg",
            "administration"
        ]

    stopwords = {
        "what",
        "does",
        "this",
        "that",
        "about",
        "tell",
        "give",
        "with",
        "from",
        "drug",
        "medicine",
        "medication",
        "please",
        "show",
        "explain",
        "the",
        "are",
        "is",
        "for"
    }

    return [
        word
        for word in re.findall(
            r"[a-z]{4,}",
            q
        )
        if word not in stopwords
    ]


def _extract_context_blocks(
    context: str
) -> List[Tuple[int, int, str]]:

    pattern = re.compile(
        r"SOURCE\s+(\d+)\s+"
        r"Drug:\s*(.*?)\s+"
        r"Document:\s*(.*?)\s+"
        r"Page:\s*(\d+)\s+"
        r"Section:\s*(.*?)\s+"
        r"Document ID:\s*(.*?)\s+"
        r"Text:\s*(.*?)(?=\nSOURCE\s+\d+\s*$|\Z)",
        re.IGNORECASE | re.DOTALL
    )

    blocks = []

    for match in pattern.finditer(context):

        try:
            source_id = int(match.group(1))
            page = int(match.group(4))
            text = match.group(7).strip()

            blocks.append(
                (
                    source_id,
                    page,
                    text
                )
            )

        except (
            TypeError,
            ValueError
        ):
            continue

    return blocks


def split_evidence_units(
    text: str
) -> List[str]:

    text = clean_pdf_text(text)

    if not text:
        return []

    paragraphs = re.split(
        r"\n\s*\n+",
        text
    )

    units = []

    for paragraph in paragraphs:

        paragraph = re.sub(
            r"\s+",
            " ",
            paragraph
        ).strip()

        if not paragraph:
            continue

        pieces = re.split(
            r"(?<=[.!?])\s+(?=[A-Z0-9\"(])",
            paragraph
        )

        for piece in pieces:

            piece = piece.strip()

            if len(piece) >= 25:
                units.append(piece)

    return units


def extractive_fallback(
    question: str,
    context: str
) -> str:

    keywords = _question_keywords(
        question
    )

    blocks = _extract_context_blocks(
        context
    )

    candidates = []

    for source_id, page, text in blocks:

        for unit in split_evidence_units(text):

            low = unit.lower()

            score = sum(
                1
                for keyword in keywords
                if keyword in low
            )

            if score > 0:
                candidates.append(
                    {
                        "source_id": source_id,
                        "page": page,
                        "text": unit,
                        "score": score
                    }
                )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    selected = []
    seen = set()

    for item in candidates:

        normalized = re.sub(
            r"\s+",
            " ",
            item["text"].lower()
        )

        if normalized in seen:
            continue

        seen.add(normalized)
        selected.append(item)

        if len(selected) >= 5:
            break

    if not selected:
        return (
            "I found relevant evidence, but the AI service "
            "is temporarily unavailable and the retrieved "
            "passages do not support a safe extractive answer."
        )

    lines = [
        "The available prescribing information states:"
    ]

    for item in selected:
        lines.append(
            f"- {item['text']} "
            f"[Source {item['source_id']}, "
            f"Page {item['page']}]"
        )

    return "\n\n".join(lines)


# ============================================================
# CITATIONS
# ============================================================

def normalize_citations(
    answer: str
) -> str:

    if not answer:
        return answer

    answer = re.sub(
        r"【\s*Source\s+(\d+)\s*,\s*Page\s+(\d+)\s*】",
        r"[Source \1, Page \2]",
        answer,
        flags=re.IGNORECASE
    )

    answer = re.sub(
        r"\(\s*Source\s+(\d+)\s*,\s*Page\s+(\d+)\s*\)",
        r"[Source \1, Page \2]",
        answer,
        flags=re.IGNORECASE
    )

    # Normalize [Source 1, Page 2, Section General] -> [Source 1, Page 2]
    answer = re.sub(
        r"\[\s*Source\s+(\d+)\s*,\s*Page\s+(\d+)[^\]]*\]",
        r"[Source \1, Page \2]",
        answer,
        flags=re.IGNORECASE
    )

    # Clean dangling or broken source remnants from text
    answer = re.sub(r"(?im)^\s*[\*\-•]?\s*Source:\s*(?:and|[.,\s])*$", "", answer)
    answer = re.sub(r"(?im)\bSource:\s*and\.\s*", "", answer)
    answer = re.sub(r"(?im)\bSource:\s*and\b", "", answer)

    return answer


def validate_citations(
    answer: str,
    sources: List[Dict[str, Any]]
) -> str:

    if not answer:
        return answer

    valid_sources = {}

    for source in sources:

        try:
            source_id = int(
                source["source_id"]
            )

            page = int(
                source["page"]
            )

            valid_sources[source_id] = page

        except (
            KeyError,
            TypeError,
            ValueError
        ):
            continue

    pattern = re.compile(
        r"\[Source\s+(\d+),\s*Page\s+(\d+)\]",
        re.IGNORECASE
    )

    def replace_invalid(match):

        source_id = int(match.group(1))
        page = int(match.group(2))

        if source_id not in valid_sources:
            return ""

        if valid_sources[source_id] != page:
            return ""

        return (
            f"[Source {source_id}, "
            f"Page {page}]"
        )

    return pattern.sub(
        replace_invalid,
        answer
    )


def remove_inline_citations(
    answer: str
) -> str:

    if not answer:
        return answer

    return re.sub(
        r"\s*[\[\(【]\s*Source\s+\d+\s*,\s*"
        r"Page\s+\d+\s*[\]\)】]",
        "",
        answer,
        flags=re.IGNORECASE
    ).strip()



# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(
    matches: List[Dict[str, Any]],
    answer: str
) -> Dict[str, Any]:

    if not matches:
        return {
            "label": "not_found",
            "score": 0.0,
            "grounding_score": 0.0
        }

    scores = []

    for match in matches:
        try:
            scores.append(
                float(
                    match.get("score", 0)
                    or 0
                )
            )
        except Exception:
            pass

    if not scores:
        return {
            "label": "not_found",
            "score": 0.0,
            "grounding_score": 0.0
        }

    best_score = max(scores)

    average_score = (
        sum(scores) / len(scores)
    )

    grounding_score = min(
        1.0,
        (
            best_score * 0.65
            +
            average_score * 0.35
        )
    )

    if grounding_score >= 0.72:
        label = "directly_supported"

    elif grounding_score >= 0.50:
        label = "partially_supported"

    else:
        label = "weakly_supported"

    return {
        "label": label,
        "score": round(
            grounding_score,
            4
        ),
        "grounding_score": round(
            grounding_score,
            4
        )
    }


# ============================================================
# MAIN RAG PIPELINE
# ============================================================

def answer_question(
    question: str,
    previous_videos: Optional[List[Dict[str, Any]]] = None,
    image_context: Any = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None,
    document_id: Optional[str] = None
) -> Dict[str, Any]:

    question = (question or "").strip()

    previous_videos = previous_videos or []

    conversation_history = normalize_history(
        conversation_history
    )

    # If memories weren't explicitly supplied,
    # load them automatically when user_id is available.
    if memories is None:
        memories = load_long_term_memories(
            user_id
        )

    # Save obvious durable memories such as:
    # "My name is Deekshitha."
    save_memory_candidates(
        user_id,
        question,
        chat_id
    )


    if not question:
        return {
            "success": False,
            "question": "",
            "answer": "Please enter a question.",
            "sources": [],
            "videos": [],
            "image_analysis": "",
            "confidence": {
                "label": "not_found",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    # --------------------------------------------------------
    # EMERGENCY
    # --------------------------------------------------------

    if is_emergency_question(question):

        return {
            "success": True,
            "question": question,
            "answer": emergency_response(),
            "sources": [],
            "videos": [],
            "image_analysis": "",
            "confidence": {
                "label": "emergency",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    # --------------------------------------------------------
    # PERSONALIZED MEDICAL SAFETY
    # --------------------------------------------------------

    if is_personal_medical_question(question):

        return {
            "success": True,
            "question": question,
            "answer": PERSONAL_MEDICAL_RESPONSE,
            "sources": [],
            "videos": [],
            "image_analysis": "",
            "confidence": {
                "label": "not_applicable",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    # --------------------------------------------------------
    # GENERAL CONVERSATION
    # --------------------------------------------------------

    if is_general_conversation_question(
        question
    ):

        answer = generate_general_answer(
            question,
            history=conversation_history,
            memories=memories
        )

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "sources": [],
            "videos": [],
            "image_analysis": "",
            "confidence": {
                "label": "not_applicable",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    normalized_image_context = (
        normalize_image_context(
            image_context
        )
    )


    # --------------------------------------------------------
    # CONTEXTUAL QUESTION
    # --------------------------------------------------------

    retrieval_question = build_contextual_question(
        question,
        conversation_history
    )

    # --------------------------------------------------------
    # NORMAL RAG
    # --------------------------------------------------------

    matches = retrieve_documents(
        retrieval_question,
        image_context=normalized_image_context,
        document_id=document_id
    )

    if not matches:

        return {
            "success": True,
            "question": question,
            "answer": INSUFFICIENT_EVIDENCE,
            "sources": [],
            "videos": [],
            "image_analysis": normalized_image_context,
            "confidence": {
                "label": "not_found",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    context, sources = build_context(
        matches
    )

    if not context or not sources:

        return {
            "success": True,
            "question": question,
            "answer": INSUFFICIENT_EVIDENCE,
            "sources": [],
            "videos": [],
            "image_analysis": normalized_image_context,
            "confidence": {
                "label": "not_found",
                "score": 0.0,
                "grounding_score": 0.0
            },
            "grounding_score": 0.0
        }

    # Pass both user's question and retrieval_question so that follow-up
    # questions have exact contextual reference for the LLM.
    answer = generate_answer(
        question,
        context,
        image_context=normalized_image_context,
        history=conversation_history,
        memories=memories,
        retrieval_question=retrieval_question
    )

    answer = normalize_citations(
        answer
    )

    answer = validate_citations(
        answer,
        sources
    )

    answer = clean_answer_format(
        answer
    )

    if not answer:

        answer = extractive_fallback(
            question,
            context
        )

        answer = clean_answer_format(
            answer
        )

    confidence = calculate_confidence(
        matches,
        answer
    )

    return {
        "success": True,
        "question": question,
        "answer": answer,
        "sources": sources,
        "videos": [],
        "image_analysis": normalized_image_context,
        "confidence": confidence,
        "grounding_score": confidence.get(
            "grounding_score",
            0.0
        )
    }


# ============================================================
# IMAGE + RAG
# ============================================================

def analyze_uploaded_image(
    image_path: str,
    question: str = ""
) -> str:

    if not image_path:
        return ""

    try:

        result = analyze_image(
            image_path,
            question=question
        )

        return normalize_image_context(
            result
        )

    except Exception as error:

        print(
            "[Image] Analysis failed:",
            repr(error)
        )

        return ""


def answer_question_with_image(
    question: str,
    image_path: str,
    previous_videos: Optional[List[Dict[str, Any]]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[int] = None,
    chat_id: Optional[int] = None
) -> Dict[str, Any]:

    image_analysis = analyze_uploaded_image(
        image_path,
        question=question
    )

    result = answer_question(
        question,
        previous_videos=previous_videos,
        image_context=image_analysis,
        conversation_history=conversation_history,
        memories=memories,
        user_id=user_id,
        chat_id=chat_id
    )

    result["image_analysis"] = image_analysis

    return result


# ============================================================
# DEBUG
# ============================================================

def debug_retrieval(
    question: str
) -> None:

    matches = retrieve_documents(
        question
    )

    print()
    print("=" * 60)
    print("RETRIEVAL DEBUG")
    print("=" * 60)

    print(
        f"Question: {question}"
    )

    print(
        f"Matches: {len(matches)}"
    )

    for index_number, match in enumerate(
        matches,
        start=1
    ):

        metadata = (
            match.get("metadata", {})
            or {}
        )

        print()
        print("-" * 60)

        print(
            f"Match: {index_number}"
        )

        print(
            f"Score: "
            f"{match.get('score', 0)}"
        )

        print(
            f"Drug: "
            f"{metadata.get('drug', 'Unknown')}"
        )

        print(
            f"Source: "
            f"{metadata.get('source', 'Unknown')}"
        )

        print(
            f"Page: "
            f"{metadata.get('page', 'Unknown')}"
        )

        print(
            f"Section: "
            f"{metadata.get('section', 'Unknown')}"
        )

        print(
            f"Document ID: "
            f"{metadata.get('document_id', 'Unknown')}"
        )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("DRUGASSIST RAG TEST")
    print("=" * 60)

    print()
    print("Testing general conversation...")

    test_history = [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": (
                "Hello! How are you doing today?"
            )
        }
    ]

    result = answer_question(
        "I'm having a bad day.",
        conversation_history=test_history
    )

    print()
    print("ANSWER:")
    print(result["answer"])

    print()
    print("=" * 60)
    print("RAG TEST COMPLETED")
    print("=" * 60)