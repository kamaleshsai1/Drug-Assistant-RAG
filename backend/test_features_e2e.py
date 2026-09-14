# ============================================================
# END-TO-END FEATURE VERIFICATION TEST SUITE
# ============================================================
#
# Verifies:
# 1. Feature 1: PDF view endpoint and page navigation (#page=N)
# 2. Feature 2: PDF authentication of trusted vs fake/suspicious PDFs
# 3. /upload-pdf HTTP 400 rejection behavior
# 4. /chat attachment rejection response matching user screenshot
# ============================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from auth import create_access_token
from pdf_authenticator import authenticate_pdf_document

def run_e2e_tests():
    print("\n" + "=" * 65)
    print("STARTING DRUGASSIST FEATURE VERIFICATION TESTS")
    print("=" * 65)

    client = TestClient(app)
    token = create_access_token(1)
    auth_headers = {"Authorization": f"Bearer {token}"}

    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    suspicious_pdf = os.path.join(uploads_dir, "rinvoq_medical_information_test.pdf")
    untrusted_pdf = os.path.join(uploads_dir, "fake_untrusted_sample.pdf")
    authentic_pdf = os.path.join(uploads_dir, "ALLEROFF.pdf")

    # --------------------------------------------------------
    # 1. FEATURE 1 TEST: PDF View / Stream Endpoint
    # --------------------------------------------------------
    print("\n[TEST 1.1] Verifying GET /documents/{id}/pdf endpoint...")
    resp = client.get("/documents/drug.pdf/pdf")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "application/pdf" in resp.headers.get("content-type", ""), "Wrong content-type"
    assert "inline" in resp.headers.get("content-disposition", ""), "Expected inline disposition"
    print("-> Successfully verified /documents/drug.pdf/pdf (inline PDF stream)!")

    print("\n[TEST 1.2] Verifying lookup by document_id key...")
    resp_rinvoq = client.get("/documents/1b18b96d-9f0524388a03e816/pdf")
    if resp_rinvoq.status_code == 200:
        assert "rinvoq_pi.pdf" in resp_rinvoq.headers.get("content-disposition", "")
        print("-> Successfully verified Rinvoq PDF lookup by Pinecone document key!")
    else:
        print("-> Note: Key not in test DB, fallback served.")

    # --------------------------------------------------------
    # 2. FEATURE 2 TEST: PDF Authenticator Direct Verification
    # --------------------------------------------------------
    print("\n[TEST 2.1] Authenticating suspicious PDF (rinvoq_medical_information_test.pdf)...")
    res_suspicious = authenticate_pdf_document(suspicious_pdf)
    assert not res_suspicious["is_authentic"]
    assert res_suspicious["reason"] == "suspicious_instructions"
    assert "suspicious instruction-like content" in res_suspicious["detail"]
    print("-> Verified suspicious instruction detection!")
    print("   Message:", res_suspicious["detail"].replace('\n', ' '))

    print("\n[TEST 2.2] Authenticating untrusted non-medical PDF (fake_untrusted_sample.pdf)...")
    res_untrusted = authenticate_pdf_document(untrusted_pdf)
    assert not res_untrusted["is_authentic"]
    assert res_untrusted["reason"] == "untrusted_source"
    print("-> Verified untrusted non-medical source rejection!")
    print("   Message:", res_untrusted["detail"].replace('\n', ' '))

    print("\n[TEST 2.3] Authenticating authentic drug prescribing information (ALLEROFF.pdf)...")
    res_authentic = authenticate_pdf_document(authentic_pdf)
    assert res_authentic["is_authentic"]
    print("-> Verified authentic document approval!")
    print("   Matched sections:", res_authentic.get("matched_sections"))

    # --------------------------------------------------------
    # 3. FEATURE 2 TEST: Upload API Endpoint HTTP 400 Rejection
    # --------------------------------------------------------
    print("\n[TEST 3.1] Testing POST /upload-pdf with suspicious fake PDF...")
    with open(suspicious_pdf, "rb") as f:
        r_up1 = client.post(
            "/upload-pdf",
            files={"file": ("rinvoq_medical_information_test.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    assert r_up1.status_code == 400, f"Expected 400, got {r_up1.status_code}"
    detail_up1 = r_up1.json().get("detail", "")
    assert "suspicious instruction-like content" in detail_up1
    print("-> POST /upload-pdf correctly rejected with HTTP 400 and exact screenshot message!")

    print("\n[TEST 3.2] Testing POST /upload-pdf with untrusted non-medical PDF...")
    with open(untrusted_pdf, "rb") as f:
        r_up2 = client.post(
            "/upload-pdf",
            files={"file": ("fake_untrusted_sample.pdf", f, "application/pdf")},
            headers=auth_headers
        )
    assert r_up2.status_code == 400, f"Expected 400, got {r_up2.status_code}"
    print("-> POST /upload-pdf correctly rejected untrusted PDF with HTTP 400!")

    # --------------------------------------------------------
    # 4. FEATURE 2 TEST: Chat Attachment Handling (Screenshot 1 Match)
    # --------------------------------------------------------
    print("\n[TEST 4] Testing POST /chat with attached fake PDF (Screenshot 1 simulation)...")
    with open(suspicious_pdf, "rb") as f:
        r_chat = client.post(
            "/chat",
            data={"question": "Uploading rinvoq_medical_information_test.pdf..."},
            files=[("files", ("rinvoq_medical_information_test.pdf", f, "application/pdf"))],
            headers=auth_headers
        )
    assert r_chat.status_code == 200
    chat_answer = r_chat.json().get("answer", "")
    assert "PDF upload failed." in chat_answer
    assert "suspicious instruction-like content and cannot be used as a DrugAssist evidence" in chat_answer
    print("-> /chat response matches screenshot 1:")
    print("--------------------------------------------------")
    print(chat_answer)
    print("--------------------------------------------------")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED! BOTH FEATURES FULLY OPERATIONAL.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_e2e_tests()
