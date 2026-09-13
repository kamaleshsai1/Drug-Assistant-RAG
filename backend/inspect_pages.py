import sys, pdf_processor
sys.stdout.reconfigure(encoding='utf-8')

res = pdf_processor.process_pdf('uploads/pdfs/353c2573-e16e-44cf-aef9-641a89855260_rinvoq_pi.pdf')
print("Total chunks:", len(res['chunks']))
for c in res['chunks']:
    if c['page'] in (2, 8, 9, 10):
        print("--------------------------------------------------")
        print("Page:", c['page'], "| Section:", c['section'])
        print("Starts with:", c['text'][:150])
        print("Ends with:", c['text'][-150:])

