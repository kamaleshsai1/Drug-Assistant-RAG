import sys, rag
sys.stdout.reconfigure(encoding='utf-8')

q = "Crohn's Disease Dosage"
matches = rag.retrieve_documents(q)
print(f"Matches found: {len(matches)}")
context, sources = rag.build_context(matches)
print("\n--- CONTEXT PASSED TO LLM ---")
print(context)

print("\n--- RAW LLM RESPONSE ---")
raw_ans = rag._call_groq(rag.MODEL_NAME, q, context)
print(raw_ans)

print("\n--- AFTER CITATION NORMALIZATION & VALIDATION ---")
norm_ans = rag.normalize_citations(raw_ans)
val_ans = rag.validate_citations(norm_ans, sources)
print(val_ans)
