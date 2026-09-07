
from io import BytesIO
from pypdf import PdfReader

def extract_pdf_text(file_bytes):
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        raise ValueError(f"Could not read the PDF: {exc}") from exc
    if not text:
        raise ValueError("No readable text found. Use a text-based PDF resume.")
    return text
