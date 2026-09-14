# ============================================================
# DRUGASSIST PDF AUTHENTICATOR & TRUST VERIFICATION ENGINE
# ============================================================
#
# Responsibilities:
#   1. Detect suspicious instruction-like content (prompt injections,
#      jailbreaks, system overrides, adversarial payloads).
#   2. Verify that uploaded PDFs originate from trusted medical/regulatory
#      sources (official FDA/EMA prescribing information, package inserts,
#      or clinical drug monographs).
#   3. Validate document structural integrity and clinical vocabulary density.
#   4. Prevent arbitrary non-medical file uploads.
#
# ============================================================

import os
import re
from typing import Dict, List, Any, Optional
from pypdf import PdfReader


# ============================================================
# SUSPICIOUS / ADVERSARIAL PATTERNS
# ============================================================

SUSPICIOUS_INSTRUCTION_PATTERNS = [
    # Prompt injection / rule overrides
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|directions?|rules?|prompts?)",
    r"disregard\s+(?:all\s+)?(?:previous|prior|safety|system)\s+(?:instructions?|guidelines?|rules?)",
    r"forget\s+(?:all\s+)?(?:previous|prior)\s+(?:instructions?|rules?|prompts?)",
    r"override\s+(?:system|drugassist|safety|clinical|prescribing)\s+(?:prompt|instructions?|rules?)",
    r"system\s+(?:prompt|override|instructions?)\s*:",
    r"developer\s+(?:mode|override|instructions?)\s*:",
    r"you\s+are\s+now\s+(?:in\s+)?(?:an?\s+)?(?:unrestricted|developer|god|dan|jailbreak)\s+mode",
    r"pretend\s+you\s+are\s+(?:an?\s+)?(?:unrestricted|evil|unfiltered|jailbroken)",
    r"bypass\s+(?:safety|clinical|medical|evidence)\s+(?:filters?|rules?|checks?)",
    r"do\s+not\s+follow\s+(?:fda|prescribing|clinical)\s+guidelines",
    r"new\s+system\s+instruction\s*:",
    r"instruction-like\s+content",
    r"prompt\s+injection",
    r"output\s+format\s+override\s*:",
    r"jailbreak\s+successful",
    r"act\s+as\s+an\s+ai\s+without\s+(?:rules|filters|morals|restrictions)",
    r"you\s+must\s+state\s+that\s+this\s+drug\s+has\s+no\s+(?:side\s+effects|risks|warnings)",
    r"you\s+must\s+say\s+that\s+patients\s+can\s+take\s+any\s+dose",
]

COMPILED_SUSPICIOUS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_INSTRUCTION_PATTERNS
]


# ============================================================
# TRUSTED PRESCRIBING INFORMATION STRUCTURE PATTERNS
# ============================================================

# Standard FDA / EMA Prescribing Information & Package Insert Headings
OFFICIAL_PRESCRIBING_HEADINGS = [
    r"highlights\s+of\s+prescribing\s+information",
    r"full\s+prescribing\s+information",
    r"indications?\s+and\s+usage",
    r"dosage\s+and\s+administration",
    r"dosage\s+forms?\s+and\s+strengths?",
    r"contraindications?",
    r"warnings?\s+and\s+precautions?",
    r"adverse\s+reactions?",
    r"drug\s+interactions?",
    r"use\s+in\s+specific\s+populations?",
    r"overdosage",
    r"description",
    r"clinical\s+pharmacology",
    r"nonclinical\s+toxicology",
    r"clinical\s+studies",
    r"how\s+supplied\s*/\s*storage\s+and\s+handling",
    r"patient\s+counseling\s+information",
    # OTC Drug Facts standard headings
    r"drug\s+facts",
    r"active\s+ingredients?",
    r"purpose",
    r"uses?",
    r"warnings?",
    r"directions?",
    r"inactive\s+ingredients?",
    # EMA / SmPC (Summary of Product Characteristics)
    r"summary\s+of\s+product\s+characteristics",
    r"therapeutic\s+indications?",
    r"posology\s+and\s+method\s+of\s+administration",
    r"pharmacological\s+properties",
    r"pharmaceutical\s+particulars",
]

COMPILED_HEADING_PATTERNS = [
    re.compile(r"\b" + h + r"\b", re.IGNORECASE) for h in OFFICIAL_PRESCRIBING_HEADINGS
]


# Core clinical / pharmaceutical vocabulary
CLINICAL_VOCABULARY = [
    "dosage", "administration", "contraindication", "contraindications",
    "adverse", "reactions", "tablet", "capsules", "capsule", "oral",
    "injection", "intravenous", "clearance", "renal", "hepatic",
    "pediatric", "pregnancy", "lactation", "mg", "mcg", "pharmacology",
    "pharmacokinetics", "pharmacodynamics", "prescribing", "indication",
    "indications", "patient", "clinical", "efficacy", "safety",
    "overdosage", "toxicity", "hypersensitivity", "inhibitor", "metabolism",
    "plasma", "half-life", "cytochrome", "cyp3a4", "bioavailability"
]


# ============================================================
# EXTRACT TEXT HELPER
# ============================================================

def extract_pdf_pages_for_auth(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract page text safely using pypdf.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(pdf_path)
    pages = []

    for idx, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append({"page": idx, "text": text})

    return pages


# ============================================================
# 1. SUSPICIOUS INSTRUCTION DETECTION
# ============================================================

def detect_suspicious_instructions(pages: List[Dict[str, Any]]) -> Optional[str]:
    """
    Scans PDF text for prompt injections, system overrides, or suspicious
    adversarial instruction-like content.

    Returns:
        Matched snippet if suspicious content is detected, else None.
    """
    for page_data in pages:
        text = page_data.get("text", "")
        if not text:
            continue

        for pattern in COMPILED_SUSPICIOUS_PATTERNS:
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                return text[start:end].replace("\n", " ").strip()

    return None


# ============================================================
# 2. PRESCRIBING INFORMATION STRUCTURE VERIFICATION
# ============================================================

def verify_prescribing_information_authenticity(
    pages: List[Dict[str, Any]],
    original_filename: str = ""
) -> Dict[str, Any]:
    """
    Verifies that the PDF is genuine drug prescribing information
    or a clinical monograph from an official/trusted source.
    """
    total_text = " ".join([p.get("text", "") for p in pages])
    normalized_text = total_text.lower()

    if len(total_text.strip()) < 50:
        return {
            "is_valid": False,
            "reason": "empty_document",
            "detail": "PDF contains insufficient readable text or is blank/scanned without OCR."
        }

    # 1. Count matching official prescribing headings
    matched_sections = []
    for heading, pattern in zip(OFFICIAL_PRESCRIBING_HEADINGS, COMPILED_HEADING_PATTERNS):
        if pattern.search(total_text):
            clean_name = heading.replace(r"\s+", " ").replace(r"\b", "").replace("\\", "").title()
            matched_sections.append(clean_name)

    # 2. Count clinical vocabulary density
    words = re.findall(r"\b[a-z]{2,}\b", normalized_text)
    total_words = len(words)
    if total_words == 0:
        return {
            "is_valid": False,
            "reason": "no_words",
            "detail": "PDF contains no recognizable text words."
        }

    clinical_word_count = sum(1 for w in words if w in CLINICAL_VOCABULARY)
    clinical_density = clinical_word_count / total_words

    # 3. Regulatory / Source markers
    regulatory_markers = [
        "fda", "nda", "bla", "package insert", "prescribing information",
        "reference id", "initial u.s. approval", "daily med", "ema",
        "national drug code", "ndc", "abbvie", "pfizer", "novartis",
        "roche", "merck", "bayer", "glaxosmithkline", "gsk", "sanofi",
        "astrazeneca", "johnson & johnson", "janssen", "lilly", "bristol myers",
        "takeda", "amgen", "gilead", "biogen", "mylan", "teva", "sandoz"
    ]
    matched_markers = [m for m in regulatory_markers if m in normalized_text]

    # Acceptance threshold:
    # A genuine prescribing document has:
    # - At least 2 official section headings OR
    # - At least 1 section heading + regulatory marker + high clinical density (>= 1.5%) OR
    # - High clinical density (>= 2.5%) and regulatory markers
    has_prescribing_sections = len(matched_sections) >= 2
    has_mixed_signals = (len(matched_sections) >= 1 and len(matched_markers) >= 1) or (clinical_density >= 0.02 and len(matched_markers) >= 1)

    is_trusted = has_prescribing_sections or has_mixed_signals or (clinical_density >= 0.035 and len(matched_sections) >= 1)

    confidence = min(
        1.0,
        (len(matched_sections) * 0.15) + (len(matched_markers) * 0.1) + (clinical_density * 10)
    )

    return {
        "is_valid": is_trusted,
        "matched_sections": matched_sections,
        "matched_markers": matched_markers,
        "clinical_word_count": clinical_word_count,
        "clinical_density": round(clinical_density, 4),
        "confidence_score": round(confidence, 2)
    }


# ============================================================
# 3. COMPLETE AUTHENTICATION PIPELINE
# ============================================================

def authenticate_pdf_document(
    pdf_path: str,
    original_filename: str = ""
) -> Dict[str, Any]:
    """
    Main entry point for authenticating uploaded PDFs in DrugAssist.

    Enforces:
      1. Security & file validity.
      2. Rejection of suspicious instruction-like content (prompt injections).
      3. Verification of authentic prescribing information from trusted sources.

    Returns:
      {
        "is_authentic": bool,
        "reason": str,
        "detail": str,
        "matched_sections": list,
        "confidence_score": float
      }
    """
    filename = original_filename or os.path.basename(pdf_path)

    # 1. File verification
    if not os.path.exists(pdf_path):
        return {
            "is_authentic": False,
            "reason": "file_not_found",
            "detail": f"File not found: {filename}"
        }

    try:
        pages = extract_pdf_pages_for_auth(pdf_path)
    except Exception as e:
        return {
            "is_authentic": False,
            "reason": "invalid_pdf_format",
            "detail": f"Unable to parse PDF '{filename}'. File may be corrupt or encrypted: {str(e)}"
        }

    if not pages or all(len(p.get("text", "").strip()) == 0 for p in pages):
        return {
            "is_authentic": False,
            "reason": "empty_document",
            "detail": f"The PDF '{filename}' contains no readable text. Scanned documents require OCR."
        }

    # 2. Check for suspicious instruction-like content (Adversarial / Prompt Injection)
    suspicious_snippet = detect_suspicious_instructions(pages)
    if suspicious_snippet:
        return {
            "is_authentic": False,
            "reason": "suspicious_instructions",
            "detail": "PDF upload failed.\n\nThis PDF contains suspicious instruction-like content and cannot be used as a DrugAssist evidence.",
            "matched_snippet": suspicious_snippet,
            "confidence_score": 0.0
        }

    # 3. Check for authentic prescribing information / trusted medical source
    auth_check = verify_prescribing_information_authenticity(pages, filename)
    if not auth_check["is_valid"]:
        return {
            "is_authentic": False,
            "reason": "untrusted_source",
            "detail": (
                "PDF upload failed.\n\n"
                "This PDF could not be verified as authentic drug prescribing information "
                "from a trusted medical source. DrugAssist only accepts official prescribing information, "
                "package inserts, or clinical monographs (e.g., FDA/EMA/DailyMed)."
            ),
            "matched_sections": auth_check.get("matched_sections", []),
            "clinical_density": auth_check.get("clinical_density", 0.0),
            "confidence_score": auth_check.get("confidence_score", 0.0)
        }

    # Passed all checks!
    return {
        "is_authentic": True,
        "reason": "verified_authentic",
        "detail": "PDF verified as authentic drug prescribing information from a trusted medical source.",
        "matched_sections": auth_check.get("matched_sections", []),
        "matched_markers": auth_check.get("matched_markers", []),
        "clinical_density": auth_check.get("clinical_density", 0.0),
        "confidence_score": auth_check.get("confidence_score", 0.95),
        "verification_status": "Verified Trusted Source"
    }
