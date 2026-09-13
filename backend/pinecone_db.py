import os
import hashlib
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pinecone import Pinecone

from embeddings import generate_embeddings
from pdf_processor import process_pdf


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PINECONE CONFIGURATION
# ============================================================

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY is missing from .env"
    )

INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "drug-information"
)

NAMESPACE = os.getenv(
    "PINECONE_NAMESPACE",
    "drug-rag"
)

TOP_K = int(
    os.getenv("PINECONE_TOP_K", "5")
)

BATCH_SIZE = int(
    os.getenv("PINECONE_BATCH_SIZE", "100")
)


# ============================================================
# CONNECT TO PINECONE
# ============================================================

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(
    INDEX_NAME
)

print(
    f"Connected to index: {INDEX_NAME}"
)

print(
    f"Namespace: {NAMESPACE}"
)


# ============================================================
# DOCUMENT ID
# ============================================================

def create_document_id(pdf_path: str) -> str:
    """
    Create a stable unique ID for a PDF.

    The ID is based on:
        - filename
        - file contents

    This allows multiple drug documents to coexist
    safely inside the same Pinecone namespace.

    If the PDF contents change, a new document ID is created.
    """

    absolute_path = os.path.abspath(pdf_path)

    if not os.path.isfile(absolute_path):
        raise FileNotFoundError(
            f"PDF not found: {absolute_path}"
        )

    with open(
        absolute_path,
        "rb"
    ) as file:
        file_bytes = file.read()

    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()[:16]

    filename = os.path.basename(
        absolute_path
    )

    filename_hash = hashlib.md5(
        filename.encode("utf-8")
    ).hexdigest()[:8]

    return (
        f"{filename_hash}-{file_hash}"
    )


# ============================================================
# DELETE EXISTING DOCUMENT
# ============================================================

def delete_document(
    document_id: str
) -> bool:
    """
    Delete only vectors belonging to one document.

    IMPORTANT:
    This never clears the complete namespace.

    Other drug documents remain untouched.
    """

    if not document_id:
        raise ValueError(
            "document_id is required."
        )

    print()
    print(
        "Deleting existing vectors for document..."
    )

    try:
        index.delete(
            namespace=NAMESPACE,
            filter={
                "document_id": {
                    "$eq": document_id
                }
            }
        )

        print(
            "Existing document vectors deleted."
        )

        return True

    except Exception as e:
        print(
            "Warning: Could not delete existing "
            f"vectors: {e}"
        )

        return False


# ============================================================
# NORMALIZE EMBEDDING
# ============================================================

def _embedding_to_list(
    embedding: Any
) -> List[float]:
    """
    Convert an embedding object into a normal
    Python list of floats.
    """

    if hasattr(
        embedding,
        "tolist"
    ):
        embedding = embedding.tolist()

    return [
        float(value)
        for value in embedding
    ]


# ============================================================
# NORMALIZE PINECONE MATCH
# ============================================================

def _match_to_dict(
    match: Any
) -> Dict[str, Any]:
    """
    Convert a Pinecone match object or dictionary
    into a normal Python dictionary.
    """

    if isinstance(
        match,
        dict
    ):
        return {
            "id": match.get("id"),
            "score": float(
                match.get("score", 0.0) or 0.0
            ),
            "metadata": match.get(
                "metadata",
                {}
            ) or {}
        }

    metadata = getattr(
        match,
        "metadata",
        {}
    ) or {}

    return {
        "id": getattr(
            match,
            "id",
            None
        ),
        "score": float(
            getattr(
                match,
                "score",
                0.0
            ) or 0.0
        ),
        "metadata": metadata
    }


# ============================================================
# UPLOAD CHUNKS
# ============================================================

def upload_chunks(
    chunks: List[Dict[str, Any]],
    document_id: str,
    drug: str,
    source: str
) -> int:
    """
    Generate embeddings and upload document chunks
    to Pinecone.

    Metadata stored for every vector:

        text
        page
        section
        source
        drug
        document_id

    This metadata is later used for:
        - citations
        - drug filtering
        - source snippets
        - explainability
        - multi-document retrieval
    """

    if not chunks:
        print(
            "No chunks to upload."
        )
        return 0

    if not document_id:
        raise ValueError(
            "document_id is required."
        )

    if not drug:
        drug = "Unknown"

    if not source:
        source = "Unknown"

    # --------------------------------------------------------
    # Keep only valid chunks
    # --------------------------------------------------------

    valid_chunks = []

    for chunk in chunks:

        if not isinstance(
            chunk,
            dict
        ):
            continue

        text = str(
            chunk.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        valid_chunks.append(
            chunk
        )

    if not valid_chunks:
        print(
            "No valid text chunks found."
        )
        return 0

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    texts = [
        str(
            chunk.get(
                "text",
                ""
            )
        ).strip()
        for chunk in valid_chunks
    ]

    # --------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------

    print()
    print(
        "Generating embeddings..."
    )

    embeddings = generate_embeddings(
        texts
    )

    if embeddings is None:
        raise ValueError(
            "Embedding generation returned None."
        )

    if len(embeddings) != len(valid_chunks):
        raise ValueError(
            "Number of embeddings does not match "
            "number of chunks."
        )

    print(
        f"Generated {len(embeddings)} embeddings."
    )

    # --------------------------------------------------------
    # Create Pinecone records
    # --------------------------------------------------------

    records = []

    for i, (
        chunk,
        embedding
    ) in enumerate(
        zip(
            valid_chunks,
            embeddings
        )
    ):

        vector_id = (
            f"{document_id}-chunk-{i}"
        )

        # ----------------------------------------------------
        # Page
        # ----------------------------------------------------

        page = chunk.get(
            "page",
            0
        )

        try:
            page = int(page)
        except (
            TypeError,
            ValueError
        ):
            page = 0

        # ----------------------------------------------------
        # Section
        # ----------------------------------------------------

        section = chunk.get(
            "section"
        )

        if section is not None:
            section = str(
                section
            ).strip()

        # ----------------------------------------------------
        # Text
        # ----------------------------------------------------

        text = str(
            chunk.get(
                "text",
                ""
            )
        ).strip()

        # ----------------------------------------------------
        # Metadata
        # ----------------------------------------------------

        metadata = {
            "text": text,
            "page": page,
            "source": str(source),
            "drug": str(drug),
            "document_id": str(document_id)
        }

        if section:
            metadata["section"] = section

        # ----------------------------------------------------
        # Vector
        # ----------------------------------------------------

        records.append(
            {
                "id": vector_id,
                "values": _embedding_to_list(
                    embedding
                ),
                "metadata": metadata
            }
        )

    if not records:
        return 0

    # --------------------------------------------------------
    # Upload in batches
    # --------------------------------------------------------

    print()
    print(
        f"Uploading {len(records)} vectors..."
    )

    total_uploaded = 0

    for start in range(
        0,
        len(records),
        BATCH_SIZE
    ):

        batch = records[
            start:start + BATCH_SIZE
        ]

        index.upsert(
            vectors=batch,
            namespace=NAMESPACE
        )

        total_uploaded += len(
            batch
        )

        print(
            f"Uploaded "
            f"{total_uploaded}/"
            f"{len(records)}"
        )

    print()
    print(
        "All vectors uploaded successfully."
    )

    return total_uploaded


# ============================================================
# BUILD PINECONE FILTER
# ============================================================

def _build_filter(
    drug: Optional[str] = None,
    document_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Build Pinecone metadata filters.

    Examples:

        drug only:
            {"drug": {"$eq": "Alleroff"}}

        document only:
            {"document_id": {"$eq": "..."}}

        both:
            {
                "$and": [
                    {"drug": {"$eq": "..."}},
                    {"document_id": {"$eq": "..."}}
                ]
            }
    """

    filters = []

    if drug:
        filters.append(
            {
                "drug": {
                    "$eq": str(drug)
                }
            }
        )

    if document_id:
        filters.append(
            {
                "document_id": {
                    "$eq": str(document_id)
                }
            }
        )

    if not filters:
        return None

    if len(filters) == 1:
        return filters[0]

    return {
        "$and": filters
    }


# ============================================================
# SEARCH PINECONE
# ============================================================

def search_pinecone(
    question: str,
    top_k: int = TOP_K,
    drug: Optional[str] = None,
    document_id: Optional[str] = None
):
    """
    Search Pinecone using semantic similarity.

    Optional filters:
        drug
        document_id

    If both are supplied, BOTH conditions must match.
    """

    if not question:
        return {
            "matches": []
        }

    question = str(
        question
    ).strip()

    if not question:
        return {
            "matches": []
        }

    try:
        top_k = int(
            top_k
        )
    except (
        TypeError,
        ValueError
    ):
        top_k = TOP_K

    top_k = max(
        1,
        min(
            top_k,
            100
        )
    )

    # --------------------------------------------------------
    # Generate query embedding
    # --------------------------------------------------------

    query_embeddings = generate_embeddings(
        [question]
    )

    if not query_embeddings:
        return {
            "matches": []
        }

    query_embedding = (
        query_embeddings[0]
    )

    # --------------------------------------------------------
    # Query configuration
    # --------------------------------------------------------

    query_kwargs = {
        "namespace": NAMESPACE,
        "vector": _embedding_to_list(
            query_embedding
        ),
        "top_k": top_k,
        "include_metadata": True
    }

    # --------------------------------------------------------
    # Metadata filters
    # --------------------------------------------------------

    pinecone_filter = _build_filter(
        drug=drug,
        document_id=document_id
    )

    if pinecone_filter:
        query_kwargs["filter"] = (
            pinecone_filter
        )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    results = index.query(
        **query_kwargs
    )

    return results


# ============================================================
# SEARCH AS NORMAL PYTHON LIST
# ============================================================

def search_pinecone_list(
    question: str,
    top_k: int = TOP_K,
    drug: Optional[str] = None,
    document_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function.

    Returns Pinecone matches as normal dictionaries.
    """

    results = search_pinecone(
        question=question,
        top_k=top_k,
        drug=drug,
        document_id=document_id
    )

    matches = extract_matches(
        results
    )

    return [
        _match_to_dict(
            match
        )
        for match in matches
    ]


# ============================================================
# CONVERT PINECONE RESULTS
# ============================================================

def extract_matches(
    results: Any
) -> List[Any]:
    """
    Convert Pinecone response into a normal list.

    Supports:
        - Pinecone response objects
        - dictionaries
        - None
    """

    if results is None:
        return []

    # --------------------------------------------------------
    # Pinecone object
    # --------------------------------------------------------

    if hasattr(
        results,
        "matches"
    ):

        matches = (
            results.matches
        )

        return matches or []

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(
        results,
        dict
    ):

        return (
            results.get(
                "matches",
                []
            )
            or []
        )

    return []


# ============================================================
# GET DOCUMENT STATISTICS
# ============================================================

def get_index_stats() -> Dict[str, Any]:
    """
    Return Pinecone index statistics as a normal dictionary
    where possible.
    """

    stats = (
        index.describe_index_stats()
    )

    if isinstance(
        stats,
        dict
    ):
        return stats

    if hasattr(
        stats,
        "to_dict"
    ):
        try:
            return stats.to_dict()
        except Exception:
            pass

    result = {}

    for key in [
        "dimension",
        "index_fullness",
        "total_vector_count",
        "namespaces"
    ]:

        if hasattr(
            stats,
            key
        ):
            result[key] = getattr(
                stats,
                key
            )

    return result


# ============================================================
# GET NAMESPACE VECTOR COUNT
# ============================================================

def get_namespace_vector_count() -> int:
    """
    Return the number of vectors in the configured namespace.
    """

    try:
        stats = get_index_stats()

        namespaces = stats.get(
            "namespaces",
            {}
        ) or {}

        namespace_info = (
            namespaces.get(
                NAMESPACE,
                {}
            )
            or {}
        )

        if isinstance(
            namespace_info,
            dict
        ):
            return int(
                namespace_info.get(
                    "vector_count",
                    0
                )
                or 0
            )

        if hasattr(
            namespace_info,
            "vector_count"
        ):
            return int(
                namespace_info.vector_count
                or 0
            )

    except Exception:
        pass

    return 0


# ============================================================
# INDEX ONE PDF
# ============================================================

def index_pdf(
    pdf_path: str
) -> Dict[str, Any]:
    """
    Process and index one drug PDF.

    Steps:

        1. Validate PDF
        2. Extract PDF
        3. Detect drug/source
        4. Create logical chunks
        5. Create stable document ID
        6. Delete old vectors for THIS document
        7. Generate embeddings
        8. Upload vectors
        9. Return indexing information
    """

    print()
    print("=" * 60)
    print("INDEXING DRUG PDF")
    print("=" * 60)

    print(
        f"\nPDF: {pdf_path}"
    )

    # --------------------------------------------------------
    # Validate file
    # --------------------------------------------------------

    if not os.path.isfile(
        pdf_path
    ):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if not pdf_path.lower().endswith(
        ".pdf"
    ):
        raise ValueError(
            "Only PDF files can be indexed."
        )

    # --------------------------------------------------------
    # Process PDF
    # --------------------------------------------------------

    result = process_pdf(
        pdf_path
    )

    if not result:
        raise ValueError(
            "PDF processing returned no result."
        )

    # --------------------------------------------------------
    # Extract processed information
    # --------------------------------------------------------

    drug = result.get(
        "drug",
        "Unknown"
    )

    source = result.get(
        "source",
        os.path.basename(
            pdf_path
        )
    )

    chunks = result.get(
        "chunks",
        []
    )

    pages = result.get(
        "pages",
        []
    )

    # --------------------------------------------------------
    # Validate processed data
    # --------------------------------------------------------

    if not chunks:
        raise ValueError(
            "No chunks were generated from the PDF."
        )

    # --------------------------------------------------------
    # Create stable document ID
    # --------------------------------------------------------

    document_id = create_document_id(
        pdf_path
    )

    print()
    print(
        f"Drug: {drug}"
    )

    print(
        f"Source: {source}"
    )

    print(
        f"Document ID: {document_id}"
    )

    print(
        f"Pages: {len(pages)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    # --------------------------------------------------------
    # Delete previous version
    # --------------------------------------------------------

    delete_document(
        document_id
    )

    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------

    vector_count = upload_chunks(
        chunks=chunks,
        document_id=document_id,
        drug=drug,
        source=source
    )

    if vector_count <= 0:
        raise ValueError(
            "No vectors were uploaded."
        )

    # --------------------------------------------------------
    # Complete
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("PDF INDEXING COMPLETE")
    print("=" * 60)

    return {
        "success": True,
        "drug": drug,
        "source": source,
        "document_id": document_id,
        "pages": len(pages),
        "chunks": len(chunks),
        "vectors": vector_count
    }


# ============================================================
# INDEX ALL PDFs
# ============================================================

def index_all_pdfs(
    uploads_directory: str = "uploads"
) -> List[Dict[str, Any]]:
    """
    Find and index every PDF inside uploads/.

    Existing documents are NOT globally deleted.

    Each PDF gets its own document ID.
    """

    if not os.path.isdir(
        uploads_directory
    ):
        print(
            f"Uploads directory not found: "
            f"{uploads_directory}"
        )

        return []

    pdf_files = sorted(
        [
            file
            for file in os.listdir(
                uploads_directory
            )
            if file.lower().endswith(
                ".pdf"
            )
        ]
    )

    if not pdf_files:
        print(
            "\nNo PDF files found in uploads."
        )

        return []

    print()
    print("=" * 60)
    print(
        f"FOUND {len(pdf_files)} PDF FILE(S)"
    )
    print("=" * 60)

    results = []

    for filename in pdf_files:

        pdf_path = os.path.join(
            uploads_directory,
            filename
        )

        try:

            result = index_pdf(
                pdf_path
            )

            results.append(
                result
            )

        except Exception as e:

            print()
            print(
                f"ERROR indexing {filename}:"
            )

            print(
                repr(e)
            )

            results.append(
                {
                    "success": False,
                    "filename": filename,
                    "error": str(e)
                }
            )

    return results


# ============================================================
# SHOW PINECONE STATISTICS
# ============================================================

def show_stats():
    """
    Display Pinecone index statistics.
    """

    print()
    print("=" * 60)
    print("PINECONE INDEX STATISTICS")
    print("=" * 60)

    try:

        stats = (
            index.describe_index_stats()
        )

        print(
            stats
        )

        # ----------------------------------------------------
        # Namespace information
        # ----------------------------------------------------

        if hasattr(
            stats,
            "namespaces"
        ):

            namespaces = (
                stats.namespaces
                or {}
            )

        elif isinstance(
            stats,
            dict
        ):

            namespaces = (
                stats.get(
                    "namespaces",
                    {}
                )
                or {}
            )

        else:

            namespaces = {}

        namespace_info = (
            namespaces.get(
                NAMESPACE
            )
        )

        if namespace_info:

            if hasattr(
                namespace_info,
                "vector_count"
            ):

                vector_count = (
                    namespace_info.vector_count
                )

            elif isinstance(
                namespace_info,
                dict
            ):

                vector_count = (
                    namespace_info.get(
                        "vector_count",
                        0
                    )
                )

            else:

                vector_count = 0

            print()
            print(
                f"Namespace: {NAMESPACE}"
            )

            print(
                f"Vector count: {vector_count}"
            )

        else:

            print()
            print(
                f"Namespace '{NAMESPACE}' "
                "is currently empty or not returned."
            )

    except Exception as e:

        print(
            f"Could not retrieve "
            f"statistics: {e}"
        )


# ============================================================
# TEST SEARCH
# ============================================================

def test_search():
    """
    Basic Pinecone retrieval test.
    """

    question = (
        "What is Losartan Potassium used for?"
    )

    print()
    print("=" * 60)
    print("TESTING PINECONE SEARCH")
    print("=" * 60)

    print(
        f"\nQuestion: {question}"
    )

    try:

        results = search_pinecone(
            question,
            top_k=5
        )

        matches = extract_matches(
            results
        )

        print()
        print(
            f"Matches found: {len(matches)}"
        )

        # ----------------------------------------------------
        # Display results
        # ----------------------------------------------------

        for i, match in enumerate(
            matches,
            start=1
        ):

            match_dict = _match_to_dict(
                match
            )

            score = match_dict.get(
                "score",
                0.0
            )

            metadata = (
                match_dict.get(
                    "metadata",
                    {}
                )
                or {}
            )

            print()
            print(
                "-" * 60
            )

            print(
                f"Result {i}"
            )

            print(
                f"Score: {score:.4f}"
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
                f"Document ID: "
                f"{metadata.get('document_id', 'Unknown')}"
            )

            if metadata.get(
                "section"
            ):

                print(
                    f"Section: "
                    f"{metadata.get('section')}"
                )

            text = str(
                metadata.get(
                    "text",
                    ""
                )
            )

            print(
                f"Text: {text[:300]}..."
            )

    except Exception as e:

        print()
        print(
            f"Search test failed: {e}"
        )


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("DRUG RAG PINECONE INDEXER")
    print("=" * 60)

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # DO NOT CLEAR THE WHOLE NAMESPACE.
    #
    # Existing Losartan and Alleroff vectors
    # must remain safe.
    # --------------------------------------------------------

    results = index_all_pdfs(
        "uploads"
    )

    print()
    print(
        "INDEXING SUMMARY"
    )

    for result in results:

        print(
            result
        )

    show_stats()

    test_search()

    print()
    print("=" * 60)
    print("PINECONE TEST COMPLETE")
    print("=" * 60)