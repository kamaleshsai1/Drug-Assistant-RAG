# ============================================================
# DRUGASSIST PDF PROCESSOR
# ============================================================
#
# Responsibilities:
#   1. Extract PDF text page-by-page
#   2. Preserve page numbers
#   3. Detect drug name robustly
#   4. Detect FDA / OTC section headings
#   5. Create logical overlapping chunks
#   6. Preserve drug/source/page/section metadata
#   7. Provide a clean process_pdf() pipeline
#
# Compatible with:
#   - pinecone_db.py
#   - rag.py
#   - main.py
#   - database.py
#
# ============================================================

import hashlib
import os
import re
from typing import Dict, List, Optional

from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_PDF_PATH = os.path.join(
    "uploads",
    "drug.pdf",
)

CHUNK_SIZE = 1400
CHUNK_OVERLAP = 220
MIN_TEXT_LENGTH = 20


# ============================================================
# PDF TEXT CLEANING
# ============================================================

def clean_page_text(text: str) -> str:
    """
    Clean extracted PDF text while preserving useful
    document structure.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\x00", "")
    text = text.replace("\xa0", " ")

    lines = []

    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line:
            lines.append(line)
        else:
            if lines and lines[-1] != "":
                lines.append("")

    text = "\n".join(lines)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# EXTRACT PAGES
# ============================================================

def extract_pages(pdf_path: str) -> List[Dict]:
    """
    Extract PDF text page-by-page.

    Each page retains its original 1-based page number.
    """

    if not pdf_path:
        raise ValueError("PDF path cannot be empty.")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if not os.path.isfile(pdf_path):
        raise ValueError(
            f"PDF path is not a file: {pdf_path}"
        )

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        try:
            raw_text = page.extract_text()
        except Exception:
            raw_text = ""

        text = clean_page_text(
            raw_text or ""
        )

        pages.append(
            {
                "page": page_number,
                "text": text,
            }
        )

    return pages


# ============================================================
# GENERIC TEXT HELPERS
# ============================================================

def _normalize_spaces(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text or "",
    ).strip()


def _normalize_for_matching(text: str) -> str:
    text = (text or "").lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def _is_uuid_like(text: str) -> bool:
    if not text:
        return False

    value = text.strip()

    return bool(
        re.fullmatch(
            r"[0-9a-f]{8}"
            r"(?:[\s-]+[0-9a-f]{4})?"
            r"(?:[\s-]+[0-9a-f]{4})?"
            r"(?:[\s-]+[0-9a-f]{4})?"
            r"(?:[\s-]+[0-9a-f]{12})",
            value,
            flags=re.IGNORECASE,
        )
    )


def _contains_uuid(text: str) -> bool:
    if not text:
        return False

    value = text.lower()

    return bool(
        re.search(
            r"[0-9a-f]{8}"
            r"(?:[\s-]+[0-9a-f]{4})"
            r"(?:[\s-]+[0-9a-f]{4})"
            r"(?:[\s-]+[0-9a-f]{4})?"
            r"(?:[\s-]+[0-9a-f]{12})",
            value,
            flags=re.IGNORECASE,
        )
    )


# ============================================================
# CLEAN DRUG NAME
# ============================================================

def clean_drug_name(
    name: Optional[str],
) -> Optional[str]:
    """
    Normalize a detected drug name.

    Removes dosage strengths, dosage forms and obvious
    document metadata.
    """

    if not name:
        return None

    name = str(name).strip()

    if not name:
        return None

    # Remove UUID-like metadata.
    name = re.sub(
        r"\b[0-9a-f]{8}"
        r"(?:[\s-]+[0-9a-f]{4})"
        r"(?:[\s-]+[0-9a-f]{4})"
        r"(?:[\s-]+[0-9a-f]{4})"
        r"(?:[\s-]+[0-9a-f]{12})\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove common dosage strengths.
    name = re.sub(
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:mg|mcg|µg|g|kg|ml|mL|"
        r"MG|MCG|G|KG|ML)\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove percentages such as 1%.
    name = re.sub(
        r"\b\d+(?:\.\d+)?\s*%",
        " ",
        name,
    )

    # Remove trademark / registered symbols.
    name = re.sub(r"[®™\u00ae\u2122]", " ", name)

    # Remove release modifiers.
    name = re.sub(
        r"\b(?:extended[- ]release|delayed[- ]release|immediate[- ]release)\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove parenthesized generic names e.g. (upadacitinib).
    name = re.sub(r"\(.*?\)", " ", name)

    # Remove common pharmaceutical dosage forms.
    dosage_forms = (
        r"tablets?|"
        r"capsules?|"
        r"caplets?|"
        r"solutions?|"
        r"syrups?|"
        r"suspensions?|"
        r"injections?|"
        r"creams?|"
        r"ointments?|"
        r"gels?|"
        r"patches?|"
        r"powders?|"
        r"granules?|"
        r"sprays?|"
        r"drops?|"
        r"lozenges?|"
        r"film[- ]?coated|"
        r"oral[- ]?solution|"
        r"oral[- ]?suspension|"
        r"nasal[- ]?spray"
    )

    name = re.sub(
        rf"\b({dosage_forms})\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove common label wording.
    name = re.sub(
        r"\bfor\s+oral\s+use\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    name = re.sub(
        r"\bfor\s+topical\s+use\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    name = re.sub(
        r"\bactive\s+ingredient\b",
        " ",
        name,
        flags=re.IGNORECASE,
    )

    # Remove surrounding punctuation.
    name = re.sub(
        r"^[\s:;,./|_\-–—]+",
        "",
        name,
    )

    name = re.sub(
        r"[\s:;,./|_\-–—]+$",
        "",
        name,
    )

    name = _normalize_spaces(name)
    name = re.sub(r"\b(?:for|and|with)\s*$", "", name, flags=re.IGNORECASE).strip()

    if not name:
        return None

    # Reject if UUID residue remains.
    if _contains_uuid(name):
        return None

    return name.title()


# ============================================================
# DRUG NAME VALIDATION
# ============================================================

def _looks_like_drug_name(
    candidate: str,
) -> bool:
    """
    Conservative validation for a possible drug name.
    """

    if not candidate:
        return False

    value = _normalize_spaces(candidate)

    if len(value) < 2:
        return False

    if len(value) > 100:
        return False

    if _contains_uuid(value):
        return False

    normalized = _normalize_for_matching(value)

    ignored_exact = {
        "highlights",
        "highlights of prescribing information",
        "prescribing information",
        "information",
        "drug",
        "drug facts",
        "label",
        "package insert",
        "table of contents",
        "contents",
        "medication guide",
        "patient information",
        "product information",
        "uses",
        "warning",
        "warnings",
        "boxed warning",
        "recent major changes",
        "major changes",
        "indications and usage",
        "dosage and administration",
        "dosage forms and strengths",
        "contraindications",
        "adverse reactions",
        "drug interactions",
        "use in specific populations",
        "clinical pharmacology",
        "clinical studies",
        "how supplied",
        "patient counseling",
        "patient counseling information",
        "full prescribing information",
        "initial us approval",
        "initial u s approval",
        "mace",
        "thrombosis",
        "mortality",
        "serious infections",
        "directions",
        "other information",
        "inactive ingredients",
        "active ingredient",
        "questions or comments",
        "questions comments",
        "unii",
        "ndc",
        "corporation",
    }

    if normalized in ignored_exact:
        return False

    ignored_terms = [
        "prescribing information",
        "drug facts",
        "product information",
        "inactive ingredients",
        "active ingredient",
        "questions or comments",
        "recent major changes",
        "indications and usage",
        "dosage and administration",
        "contraindications",
        "boxed warning",
        "full prescribing information",
        "manufactured by",
        "distributed by",
        "laboratories",
        "laboratory",
        "pharmaceuticals",
        "pharma",
        "corporation",
        "company",
        "inc ",
        " inc",
        "limited",
        " ltd",
        "unii",
        "ndc:",
        "item code",
        "route of administration",
        "source:",
    ]

    if any(
        term in normalized
        for term in ignored_terms
    ):
        return False

    # Avoid lines containing obvious metadata.
    if re.search(
        r"\b(?:unii|ndc|item\s+code|route\s+of\s+administration)\b",
        value,
        flags=re.IGNORECASE,
    ):
        return False

    # Too many numbers means this is probably metadata.
    digit_count = sum(
        char.isdigit()
        for char in value
    )

    if digit_count > 3:
        return False

    # Excessive punctuation is suspicious.
    punctuation_count = len(
        re.findall(
            r"[^A-Za-z0-9\s\-]",
            value,
        )
    )

    if punctuation_count > 3:
        return False

    words = value.split()

    if len(words) > 8:
        return False

    # Must contain alphabetic characters.
    if not re.search(
        r"[A-Za-z]",
        value,
    ):
        return False

    return True


# ============================================================
# EXTRACT STRONG DRUG CANDIDATES
# ============================================================

def _extract_candidates_from_line(
    line: str,
) -> List[str]:
    """
    Extract possible drug-name candidates from one line.
    """

    candidates = []

    if not line:
        return candidates

    original = line.strip()

    if not original:
        return candidates

    # --------------------------------------------------------
    # Pattern:
    # ALLEROFF - cetirizine hydrochloride syrup
    # --------------------------------------------------------

    match = re.match(
        r"^([A-Za-z][A-Za-z0-9\s\-]{1,80}?)"
        r"\s*[-–—:]\s*"
        r"[a-zA-Z].*$",
        original,
    )

    if match:
        candidates.append(
            match.group(1).strip()
        )

    # --------------------------------------------------------
    # Pattern:
    # LOSARTAN POTASSIUM TABLETS
    # --------------------------------------------------------

    patterns = [
        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+TABLETS?\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+CAPSULES?\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SYRUPS?\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SOLUTION\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SUSPENSION\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+INJECTION\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+ORAL\s+SOLUTION\b",

        r"^([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+FOR\s+ORAL\s+USE\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            original,
            flags=re.IGNORECASE,
        )

        if match:
            candidates.append(
                match.group(1).strip()
            )

    # --------------------------------------------------------
    # Entire uppercase line.
    # --------------------------------------------------------

    if (
        len(original.split()) <= 8
        and re.fullmatch(
            r"[A-Z0-9\s\-]+",
            original,
        )
    ):
        candidates.append(original)

    return candidates


# ============================================================
# DETECT DRUG NAME
# ============================================================

def detect_drug_name(
    pages: List[Dict],
    pdf_path: str,
) -> str:
    """
    Detect the primary drug name.

    Detection priority:

        1. Strong first-page patterns
        2. Drug name before dosage form
        3. OTC "DRUG FACTS" product-name patterns
        4. Repeated uppercase drug names
        5. Meaningful filename fallback
    """

    if not pages:
        return "Unknown Drug"

    first_page_text = pages[0].get(
        "text",
        "",
    ) or ""

    lines = [
        line.strip()
        for line in first_page_text.splitlines()
        if line.strip()
    ]

    # --------------------------------------------------------
    # Strategy 0:
    # FDA Prescribing Information Highlights Header
    # --------------------------------------------------------

    if "HIGHLIGHTS OF PRESCRIBING INFORMATION" in first_page_text.upper():
        m_brand = re.search(r"\b([A-Z0-9\-]{2,30})[®™\u00ae\u2122]", first_page_text)
        if m_brand:
            brand_candidate = clean_drug_name(m_brand.group(1).strip())
            if brand_candidate and _looks_like_drug_name(brand_candidate):
                return brand_candidate.upper()

    # --------------------------------------------------------
    # Strategy 1:
    # Look at first 50 lines for strong candidates.
    # --------------------------------------------------------

    strong_candidates = []

    for line in lines[:50]:
        for candidate in _extract_candidates_from_line(line):

            cleaned = clean_drug_name(
                candidate
            )

            if (
                cleaned
                and _looks_like_drug_name(
                    cleaned
                )
            ):
                strong_candidates.append(cleaned)

    # Prefer candidates that appear early and are concise.
    if strong_candidates:
        unique = []

        for candidate in strong_candidates:
            if candidate not in unique:
                unique.append(candidate)

        # Prefer names with 1-4 words.
        unique.sort(
            key=lambda value: (
                len(value.split()) > 4,
                len(value.split()),
                len(value),
            )
        )

        return unique[0]

    # --------------------------------------------------------
    # Strategy 2:
    # Explicitly search text surrounding dosage forms.
    # --------------------------------------------------------

    search_text = "\n".join(
        lines[:60]
    )

    patterns = [
        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+TABLETS?\b",

        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+CAPSULES?\b",

        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SYRUP\b",

        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SOLUTION\b",

        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+SUSPENSION\b",

        r"\b([A-Z][A-Z0-9\s\-]{1,80}?)"
        r"\s+INJECTION\b",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            search_text,
            flags=re.IGNORECASE,
        )

        for candidate in matches:

            cleaned = clean_drug_name(
                candidate
            )

            if (
                cleaned
                and _looks_like_drug_name(
                    cleaned
                )
            ):
                return cleaned

    # --------------------------------------------------------
    # Strategy 3:
    # Search first page for explicit OTC pattern.
    #
    # Example:
    # ALLEROFF
    # cetirizine hydrochloride syrup
    # --------------------------------------------------------

    for index, line in enumerate(lines[:30]):

        normalized = _normalize_for_matching(
            line
        )

        if normalized in {
            "drug facts",
            "drug facts label",
        }:
            continue

        # A short uppercase line immediately before a
        # generic ingredient line is a strong product-name
        # candidate.
        if (
            len(line.split()) <= 5
            and re.fullmatch(
                r"[A-Z][A-Z0-9\s\-]*",
                line,
            )
        ):
            candidate = clean_drug_name(
                line
            )

            if (
                candidate
                and _looks_like_drug_name(
                    candidate
                )
            ):
                # Ignore generic document headings.
                if normalized not in {
                    "highlights",
                    "warnings",
                    "directions",
                    "uses",
                    "active ingredient",
                    "inactive ingredients",
                    "other information",
                    "questions or comments",
                }:
                    return candidate

        # Look at the previous line when the current line
        # describes an ingredient/form.
        if (
            re.search(
                r"\b(?:hydrochloride|sodium|potassium|"
                r"acetate|sulfate|maleate|"
                r"solution|syrup|tablets?|capsules?)\b",
                line,
                flags=re.IGNORECASE,
            )
            and index > 0
        ):
            previous = lines[index - 1]

            candidate = clean_drug_name(
                previous
            )

            if (
                candidate
                and _looks_like_drug_name(
                    candidate
                )
                and len(candidate.split()) <= 5
            ):
                return candidate

    # --------------------------------------------------------
    # Strategy 4:
    # Repeated uppercase candidates over first pages.
    # --------------------------------------------------------

    combined_text = "\n".join(
        page.get("text", "")
        for page in pages[:5]
    )

    uppercase_candidates = re.findall(
        r"\b[A-Z][A-Z0-9\-]{2,}"
        r"(?:\s+[A-Z][A-Z0-9\-]{2,}){0,4}\b",
        combined_text,
    )

    frequency = {}

    for candidate in uppercase_candidates:

        cleaned = clean_drug_name(
            candidate
        )

        if not cleaned:
            continue

        if not _looks_like_drug_name(
            cleaned
        ):
            continue

        frequency[cleaned] = (
            frequency.get(cleaned, 0)
            + 1
        )

    if frequency:

        ranked = sorted(
            frequency.items(),
            key=lambda item: (
                -item[1],
                len(item[0].split()),
                len(item[0]),
            ),
        )

        return ranked[0][0]

    # --------------------------------------------------------
    # Strategy 5:
    # Filename fallback.
    # --------------------------------------------------------

    filename = os.path.basename(
        pdf_path
    )

    filename_without_extension = os.path.splitext(
        filename
    )[0]

    # Replace separators.
    filename_without_extension = (
        filename_without_extension
        .replace("_", " ")
        .replace("-", " ")
    )

    # Remove UUID from filename.
    filename_without_extension = re.sub(
        r"\b[0-9a-f]{8}"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{12})\b",
        " ",
        filename_without_extension,
        flags=re.IGNORECASE,
    )

    filename_without_extension = _normalize_spaces(
        filename_without_extension
    )

    generic_names = {
        "drug",
        "medicine",
        "document",
        "file",
        "sample",
        "pdf",
    }

    if (
        filename_without_extension
        and filename_without_extension.lower()
        not in generic_names
    ):
        cleaned = clean_drug_name(
            filename_without_extension
        )

        if (
            cleaned
            and _looks_like_drug_name(
                cleaned
            )
        ):
            return cleaned

    return "Unknown Drug"


# ============================================================
# CREATE SOURCE NAME
# ============================================================

def create_source_name(
    drug_name: str,
    pdf_path: str,
) -> str:
    """
    Generate a clean source/document name.

    For files such as:

        UUID ALLEROFF.pdf

    return:

        ALLEROFF

    instead of exposing the UUID.
    """

    filename = os.path.basename(
        pdf_path
    )

    name_without_extension = os.path.splitext(
        filename
    )[0]

    readable_name = (
        name_without_extension
        .replace("_", " ")
        .replace("-", " ")
    )

    # Remove UUIDs from filename.
    readable_name = re.sub(
        r"\b[0-9a-f]{8}"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{4})"
        r"(?:\s+[0-9a-f]{12})\b",
        " ",
        readable_name,
        flags=re.IGNORECASE,
    )

    readable_name = _normalize_spaces(
        readable_name
    )

    generic_names = {
        "",
        "drug",
        "medicine",
        "document",
        "file",
        "sample",
        "pdf",
    }

    if readable_name.lower() in generic_names:
        if drug_name and drug_name != "Unknown Drug":
            return (
                f"{drug_name} "
                f"Prescribing Information"
            )

        return "Drug Information"

    return readable_name


# ============================================================
# SECTION DETECTION
# ============================================================

KNOWN_SECTION_HEADINGS = {
    # FDA prescribing information
    "highlights",
    "highlights of prescribing information",
    "indications and usage",
    "dosage and administration",
    "dosage forms and strengths",
    "contraindications",
    "warnings and precautions",
    "adverse reactions",
    "drug interactions",
    "use in specific populations",
    "pregnancy",
    "lactation",
    "pediatric use",
    "geriatric use",
    "overdosage",
    "description",
    "clinical pharmacology",
    "mechanism of action",
    "pharmacodynamics",
    "pharmacokinetics",
    "nonclinical toxicology",
    "clinical studies",
    "how supplied",
    "storage and handling",
    "patient counseling information",
    "medication guide",
    "references",
    "boxed warning",
    "warnings",
    "precautions",

    # OTC Drug Facts
    "drug facts",
    "uses",
    "warnings",
    "directions",
    "other information",
    "inactive ingredients",
    "active ingredient",
    "purpose",
    "questions or comments",
    "questions or comments?",
    "do not use",
    "ask a doctor before use",
    "ask a doctor or pharmacist before use",
    "when using this product",
    "stop use and ask a doctor",
    "keep out of reach of children",
}


def _normalize_heading_for_matching(
    line: str,
) -> str:

    normalized = _normalize_for_matching(
        line
    )

    return normalized


def is_section_heading(
    line: str,
) -> bool:
    """
    Detect FDA-style and OTC Drug Facts headings.
    """

    if not line:
        return False

    line = line.strip()

    if len(line) < 2 or len(line) > 120:
        return False

    # --------------------------------------------------------
    # Exclude non-headings:
    # 1. Dosages, quantities, weights, ages, percentages, etc.
    # --------------------------------------------------------
    if re.match(
        r"^\d+(?:\.\d+)*\s*(?:mg|ml|mcg|kg|g|tablet|tablets|capsule|capsules|weeks|days|hours|months|years|patient|patients|%|x\s+uln)\b",
        line,
        re.IGNORECASE,
    ):
        return False

    # --------------------------------------------------------
    # 2. Lines starting with bullets or list symbols
    # --------------------------------------------------------
    if line.startswith(("•", "·", "-", "*", "–", "—")):
        return False

    # --------------------------------------------------------
    # 3. Sentences with full period followed by another sentence
    # --------------------------------------------------------
    if re.search(r"\.\s+[A-Z]", line):
        return False

    # --------------------------------------------------------
    # 4. Dangling prepositions or sentence continuations
    # --------------------------------------------------------
    if re.search(
        r"\b(?:is|are|of|for|and|or|to|with|may be|in|by|a|the|than|as|was|were|see|at)\s*$",
        line,
        re.IGNORECASE,
    ):
        return False

    # --------------------------------------------------------
    # 5. Parenthetical cross-references like (2.12, 2.13)
    # --------------------------------------------------------
    if re.match(r"^[\(\[].*?[\)\]]$", line):
        return False

    normalized = _normalize_heading_for_matching(
        line
    )

    # --------------------------------------------------------
    # Exact known heading.
    # --------------------------------------------------------

    if normalized in KNOWN_SECTION_HEADINGS:
        return True

    # --------------------------------------------------------
    # Heading followed by punctuation.
    # --------------------------------------------------------

    normalized_no_punctuation = re.sub(
        r"[^\w\s]",
        "",
        normalized,
    )

    if normalized_no_punctuation in KNOWN_SECTION_HEADINGS:
        return True

    # --------------------------------------------------------
    # Common heading with additional section number.
    #
    # Example:
    # 6 ADVERSE REACTIONS
    # 2 DOSAGE AND ADMINISTRATION
    # --------------------------------------------------------

    for heading in KNOWN_SECTION_HEADINGS:

        if normalized.endswith(
            " " + heading
        ):
            prefix = normalized[
                :-(len(heading))
            ].strip()

            if (
                prefix
                and re.fullmatch(
                    r"\d+(?:\.\d+)*",
                    prefix,
                )
            ):
                return True

    # --------------------------------------------------------
    # Numbered FDA subsections.
    # Must have decimal dot and standard FDA section number (1-17),
    # followed by an uppercase word:
    # 2.1 Recommended Evaluations...
    # 2.7 Recommended Dosage in Crohn's Disease
    # 14.5 Crohn's Disease
    # --------------------------------------------------------

    if re.match(
        r"^(?:[1-9]|1[0-7])\.\d+(?:\.\d+)*\s+[A-Z]",
        line,
    ):
        words = line.split()
        if len(words) <= 12 and not line.endswith((".", ",", ";", ":")):
            return True

    # --------------------------------------------------------
    # Numbered FDA top-level section.
    # 1 to 17 followed by uppercase title
    # --------------------------------------------------------
    match_top = re.match(r"^(?:[1-9]|1[0-7])\s+([A-Z\s,/&-]+)$", line)
    if match_top:
        title_part = match_top.group(1).strip()
        if len(title_part) >= 3 and len(title_part.split()) <= 8:
            return True

    # --------------------------------------------------------
    # Short uppercase heading.
    # --------------------------------------------------------

    letters = [
        char
        for char in line
        if char.isalpha()
    ]

    if letters:

        uppercase_count = sum(
            char.isupper()
            for char in letters
        )

        uppercase_ratio = (
            uppercase_count / len(letters)
        )

        if (
            uppercase_ratio >= 0.90
            and len(line.split()) <= 8
            and not line.endswith((".", ",", ";", ":"))
        ):
            # Avoid treating long metadata lines as headings.
            if not re.search(
                r"\b(?:UNII|NDC|CAS|ISBN|TABLE|FIGURE|PAGE)\b",
                line,
                flags=re.IGNORECASE,
            ):
                return True

    # --------------------------------------------------------
    # Title-case short headings.
    #
    # Example:
    # Product Information
    # General
    # --------------------------------------------------------

    if len(line.split()) <= 6 and not line.endswith((".", ",", ";", ":")):
        title_case_words = sum(
            1
            for word in line.split()
            if word
            and word[0].isupper()
        )

        if (
            title_case_words >= 2
            and title_case_words
            >= max(2, len(line.split()) - 1)
        ):
            if normalized in {
                "product information",
                "general",
                "indications",
                "contraindications",
                "dosage",
            }:
                return True

    return False


# ============================================================
# NORMALIZE SECTION HEADING
# ============================================================

def normalize_section_heading(
    line: str,
) -> str:
    """
    Clean a detected section heading.
    """

    if not line:
        return "General"

    line = _normalize_spaces(
        line
    )

    line = re.sub(
        r"[|]+",
        " ",
        line,
    )

    line = _normalize_spaces(
        line
    )

    if not line:
        return "General"

    return line


# ============================================================
# PAGE SECTIONS
# ============================================================

def split_page_into_sections(
    page_text: str,
) -> List[Dict]:
    """
    Split one page into logical sections.

    Each block contains:

        {
            "section": "...",
            "text": "..."
        }

    Page boundaries are preserved by create_chunks().
    """

    if not page_text:
        return []

    lines = page_text.splitlines()

    sections = []

    current_section = "General"
    current_lines = []

    def flush_current():
        nonlocal current_lines

        text = "\n".join(
            current_lines
        ).strip()

        if text:
            sections.append(
                {
                    "section": current_section,
                    "text": text,
                }
            )

        current_lines = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            if (
                current_lines
                and current_lines[-1] != ""
            ):
                current_lines.append("")

            continue

        if is_section_heading(
            stripped
        ):
            flush_current()

            current_section = (
                normalize_section_heading(
                    stripped
                )
            )

            continue

        current_lines.append(
            stripped
        )

    flush_current()

    return sections


# ============================================================
# PARAGRAPH SPLITTING
# ============================================================

def split_into_paragraphs(
    text: str,
) -> List[str]:
    """
    Split text into meaningful paragraph-like blocks.
    """

    if not text:
        return []

    blocks = re.split(
        r"\n\s*\n",
        text,
    )

    paragraphs = []

    for block in blocks:

        block = block.strip()

        if not block:
            continue

        block = re.sub(
            r"\s+",
            " ",
            block,
        ).strip()

        if len(block) >= MIN_TEXT_LENGTH:
            paragraphs.append(
                block
            )

    return paragraphs


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_into_sentences(
    text: str,
) -> List[str]:
    """
    Conservative sentence splitting for medical text.
    """

    if not text:
        return []

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if not text:
        return []

    protected = {
        "e.g.": "egPLACEHOLDER",
        "i.e.": "iePLACEHOLDER",
        "etc.": "etcPLACEHOLDER",
        "vs.": "vsPLACEHOLDER",
        "Dr.": "DrPLACEHOLDER",
        "mg.": "mgPLACEHOLDER",
        "mL.": "mLPLACEHOLDER",
    }

    for original, replacement in protected.items():
        text = text.replace(
            original,
            replacement,
        )

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text,
    )

    restored = []

    for sentence in sentences:

        for original, replacement in protected.items():
            sentence = sentence.replace(
                replacement,
                original,
            )

        sentence = sentence.strip()

        if sentence:
            restored.append(
                sentence
            )

    return restored


# ============================================================
# CHUNK TEXT
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """
    Create logical overlapping chunks.

    Priority:

        1. Paragraphs
        2. Sentences
        3. Word boundaries
        4. Hard character split
    """

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0."
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    paragraphs = split_into_paragraphs(
        text
    )

    if not paragraphs:
        paragraphs = [
            text.strip()
        ]

    chunks = []
    current = ""

    for paragraph in paragraphs:

        candidate = (
            f"{current}\n\n{paragraph}"
            if current
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(
                current.strip()
            )

        if len(paragraph) > chunk_size:

            sentences = split_into_sentences(
                paragraph
            )

            if not sentences:
                sentences = [
                    paragraph
                ]

            current = ""

            for sentence in sentences:

                candidate = (
                    f"{current} {sentence}"
                    if current
                    else sentence
                )

                if len(candidate) <= chunk_size:
                    current = candidate
                    continue

                if current:
                    chunks.append(
                        current.strip()
                    )

                if len(sentence) > chunk_size:

                    start = 0

                    while start < len(sentence):

                        end = (
                            start + chunk_size
                        )

                        piece = sentence[
                            start:end
                        ].strip()

                        if piece:
                            chunks.append(
                                piece
                            )

                        if end >= len(sentence):
                            break

                        start = max(
                            end - chunk_overlap,
                            start + 1,
                        )

                    current = ""

                else:
                    current = sentence

        else:
            current = paragraph

    if current:
        chunks.append(
            current.strip()
        )

    # --------------------------------------------------------
    # Add overlap.
    # --------------------------------------------------------

    if chunk_overlap <= 0:
        return [
            chunk
            for chunk in chunks
            if chunk
        ]

    overlapped = []

    for index, chunk in enumerate(
        chunks
    ):

        if index == 0:
            overlapped.append(
                chunk
            )
            continue

        previous = chunks[
            index - 1
        ]

        overlap_text = previous[
            -chunk_overlap:
        ].strip()

        if overlap_text:

            merged = (
                overlap_text
                + "\n"
                + chunk
            )

            if len(merged) <= (
                chunk_size
                + chunk_overlap
            ):
                overlapped.append(
                    merged.strip()
                )
            else:
                overlapped.append(
                    chunk
                )

        else:
            overlapped.append(
                chunk
            )

    return overlapped


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(
    pages: List[Dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    """
    Create logical chunks from PDF pages.

    Every chunk retains:

        id
        page
        section
        text

    Page boundaries are preserved.
    """

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    chunks = []

    chunk_counter = 1

    for page_data in pages:

        page_number = page_data.get(
            "page"
        )

        text = (
            page_data.get(
                "text",
                "",
            )
            or ""
        ).strip()

        if not text:
            continue

        sections = split_page_into_sections(
            text
        )

        if not sections:
            sections = [
                {
                    "section": "General",
                    "text": text,
                }
            ]

        for section_data in sections:

            section_name = (
                section_data.get(
                    "section",
                    "General",
                )
                or "General"
            )

            section_text = (
                section_data.get(
                    "text",
                    "",
                )
                or ""
            ).strip()

            if not section_text:
                continue

            if (
                section_name != "General"
                and not section_text.lower().startswith(section_name.lower())
            ):
                full_text_to_chunk = f"{section_name}\n\n{section_text}"
            else:
                full_text_to_chunk = section_text

            section_chunks = chunk_text(
                full_text_to_chunk,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            for chunk_value in section_chunks:

                chunk_value = (
                    chunk_value.strip()
                )

                if not chunk_value:
                    continue

                chunks.append(
                    {
                        "id": (
                            f"chunk-"
                            f"{chunk_counter}"
                        ),
                        "page": page_number,
                        "section": section_name,
                        "text": chunk_value,
                    }
                )

                chunk_counter += 1

    return chunks


# ============================================================
# CREATE DOCUMENT KEY
# ============================================================

def create_document_key(
    pdf_path: str,
) -> str:
    """
    Create a stable local document key from filename.
    """

    filename = os.path.basename(
        pdf_path
    )

    filename = os.path.splitext(
        filename
    )[0]

    filename = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        filename,
    )

    filename = filename.strip(
        "-"
    ).lower()

    if not filename:
        filename = "drug-document"

    return filename


# ============================================================
# CREATE CONTENT HASH
# ============================================================

def create_content_hash(
    pdf_path: str,
) -> str:
    """
    Create a stable content hash.

    Useful for document freshness/version tracking.
    """

    sha256 = hashlib.sha256()

    with open(
        pdf_path,
        "rb",
    ) as file:

        while True:
            block = file.read(
                1024 * 1024
            )

            if not block:
                break

            sha256.update(block)

    return sha256.hexdigest()


# ============================================================
# DOCUMENT METADATA
# ============================================================

def create_document_metadata(
    pdf_path: str,
    drug_name: str,
    source_name: str,
    pages: List[Dict],
    chunks: List[Dict],
) -> Dict:
    """
    Create summary metadata.
    """

    try:
        file_size = os.path.getsize(
            pdf_path
        )
    except OSError:
        file_size = 0

    try:
        content_hash = create_content_hash(
            pdf_path
        )
    except Exception:
        content_hash = ""

    return {
        "filename": os.path.basename(
            pdf_path
        ),
        "pdf_path": pdf_path,
        "document_key": create_document_key(
            pdf_path
        ),
        "content_hash": content_hash,
        "drug": drug_name,
        "source": source_name,
        "pages": len(pages),
        "chunks": len(chunks),
        "file_size": file_size,
    }


# ============================================================
# PROCESS PDF
# ============================================================

def process_pdf(
    pdf_path: str,
) -> Dict:
    """
    Complete PDF processing pipeline.

    Returns:

        {
            "drug": "...",
            "source": "...",
            "pdf_path": "...",
            "pages": [...],
            "chunks": [...],
            "metadata": {...}
        }
    """

    if not pdf_path:
        raise ValueError(
            "PDF path cannot be empty."
        )

    if not os.path.exists(
        pdf_path
    ):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    pages = extract_pages(
        pdf_path
    )

    if not pages:
        raise ValueError(
            "No pages were found in the PDF."
        )

    drug_name = detect_drug_name(
        pages,
        pdf_path,
    )

    source_name = create_source_name(
        drug_name,
        pdf_path,
    )

    chunks = create_chunks(
        pages
    )

    document_key = create_document_key(
        pdf_path
    )

    for chunk in chunks:

        chunk["drug"] = drug_name
        chunk["source"] = source_name
        chunk["pdf_path"] = pdf_path
        chunk["document_key"] = document_key

    metadata = create_document_metadata(
        pdf_path=pdf_path,
        drug_name=drug_name,
        source_name=source_name,
        pages=pages,
        chunks=chunks,
    )

    return {
        "drug": drug_name,
        "source": source_name,
        "pdf_path": pdf_path,
        "pages": pages,
        "chunks": chunks,
        "metadata": metadata,
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def extract_text_from_pdf(
    pdf_path: str,
) -> str:
    """
    Return complete extracted PDF text.
    """

    pages = extract_pages(
        pdf_path
    )

    return "\n\n".join(
        page["text"]
        for page in pages
        if page.get("text")
    )


def get_pdf_page_count(
    pdf_path: str,
) -> int:
    """
    Return number of PDF pages.
    """

    if not os.path.exists(
        pdf_path
    ):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    reader = PdfReader(
        pdf_path
    )

    return len(
        reader.pages
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("DRUGASSIST PDF PROCESSING TEST")
    print("=" * 70)

    print()
    print("PDF:")
    print(DEFAULT_PDF_PATH)

    try:

        result = process_pdf(
            DEFAULT_PDF_PATH
        )

        print()
        print("-" * 70)
        print("DOCUMENT INFORMATION")
        print("-" * 70)

        print(
            "Drug:",
            result["drug"],
        )

        print(
            "Source:",
            result["source"],
        )

        print(
            "Pages:",
            len(result["pages"]),
        )

        print(
            "Chunks:",
            len(result["chunks"]),
        )

        print(
            "Document Key:",
            result["metadata"]["document_key"],
        )

        print(
            "Content Hash:",
            result["metadata"]["content_hash"],
        )

        if result["chunks"]:

            print()
            print("-" * 70)
            print("FIRST CHUNK")
            print("-" * 70)

            first_chunk = (
                result["chunks"][0]
            )

            print(
                "Chunk ID:",
                first_chunk["id"],
            )

            print(
                "Page:",
                first_chunk["page"],
            )

            print(
                "Section:",
                first_chunk.get(
                    "section",
                    "General",
                ),
            )

            print()
            print(
                first_chunk["text"][:2000]
            )

            print()
            print("-" * 70)
            print("SAMPLE SECTION DISTRIBUTION")
            print("-" * 70)

            section_counts = {}

            for chunk in result["chunks"]:
                section = chunk.get(
                    "section",
                    "General",
                )

                section_counts[section] = (
                    section_counts.get(
                        section,
                        0,
                    )
                    + 1
                )

            for section, count in list(
                section_counts.items()
            )[:20]:
                print(
                    f"{section}: {count} chunk(s)"
                )

            print()
            print("-" * 70)
            print("LAST CHUNK")
            print("-" * 70)

            last_chunk = (
                result["chunks"][-1]
            )

            print(
                "Chunk ID:",
                last_chunk["id"],
            )

            print(
                "Page:",
                last_chunk["page"],
            )

            print(
                "Section:",
                last_chunk.get(
                    "section",
                    "General",
                ),
            )

        print()
        print("=" * 70)
        print("PDF PROCESSING TEST PASSED")
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print("PDF PROCESSING ERROR")
        print("=" * 70)

        print(
            type(error).__name__,
            ":",
            str(error),
        )

        print("=" * 70)