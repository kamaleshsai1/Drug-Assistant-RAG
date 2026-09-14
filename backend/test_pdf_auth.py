# ============================================================
# PDF AUTHENTICATION TEST SUITE
# ============================================================

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdf_authenticator import authenticate_pdf_document

def run_tests():
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    pdfs_dir = os.path.join(uploads_dir, "pdfs")

    suspicious_file = os.path.join(uploads_dir, "rinvoq_medical_information_test.pdf")
    untrusted_file = os.path.join(uploads_dir, "fake_untrusted_sample.pdf")
    authentic_alleroff = os.path.join(uploads_dir, "ALLEROFF.pdf")

    print("\n" + "=" * 60)
    print("RUNNING PDF AUTHENTICATION CHECKS")
    print("=" * 60)

    # TEST 1: Suspicious Instruction-like PDF
    print("\n--- TEST 1: Suspicious fake PDF (rinvoq_medical_information_test.pdf) ---")
    res1 = authenticate_pdf_document(suspicious_file)
    print("Is Authentic:", res1["is_authentic"])
    print("Reason:", res1["reason"])
    print("Detail:", res1["detail"])
    assert not res1["is_authentic"], "Test 1 FAILED: Suspicious PDF was not rejected!"
    assert res1["reason"] == "suspicious_instructions", "Test 1 FAILED: Expected reason 'suspicious_instructions'"
    assert "suspicious instruction-like content" in res1["detail"], "Test 1 FAILED: Detail text does not match"
    print(">>> TEST 1 PASSED: Correctly rejected as suspicious instruction-like content!")

    # TEST 2: Arbitrary Non-Medical PDF
    print("\n--- TEST 2: Untrusted Non-Medical PDF (fake_untrusted_sample.pdf) ---")
    res2 = authenticate_pdf_document(untrusted_file)
    print("Is Authentic:", res2["is_authentic"])
    print("Reason:", res2["reason"])
    print("Detail:", res2["detail"])
    assert not res2["is_authentic"], "Test 2 FAILED: Untrusted PDF was not rejected!"
    assert res2["reason"] == "untrusted_source", "Test 2 FAILED: Expected reason 'untrusted_source'"
    print(">>> TEST 2 PASSED: Correctly rejected as untrusted source!")

    # TEST 3: Authentic Medical Document (ALLEROFF.pdf)
    if os.path.exists(authentic_alleroff):
        print("\n--- TEST 3: Authentic Prescribing Document (ALLEROFF.pdf) ---")
        res3 = authenticate_pdf_document(authentic_alleroff)
        print("Is Authentic:", res3["is_authentic"])
        print("Matched Sections:", res3.get("matched_sections"))
        print("Confidence Score:", res3.get("confidence_score"))
        assert res3["is_authentic"], "Test 3 FAILED: Authentic PDF was rejected!"
        print(">>> TEST 3 PASSED: Correctly authenticated official prescribing document!")

    # TEST 4: Authentic Rinvoq Prescribing PDF in pdfs_dir
    rinvoq_files = [os.path.join(pdfs_dir, f) for f in os.listdir(pdfs_dir) if "rinvoq_pi" in f]
    if rinvoq_files:
        print("\n--- TEST 4: Authentic Rinvoq PI PDF ---")
        res4 = authenticate_pdf_document(rinvoq_files[0])
        print("Is Authentic:", res4["is_authentic"])
        print("Matched Sections:", len(res4.get("matched_sections", [])))
        print("Confidence Score:", res4.get("confidence_score"))
        assert res4["is_authentic"], "Test 4 FAILED: Authentic Rinvoq PI was rejected!"
        print(">>> TEST 4 PASSED: Correctly authenticated Rinvoq Prescribing Information!")

    print("\n" + "=" * 60)
    print("ALL PDF AUTHENTICATION TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
