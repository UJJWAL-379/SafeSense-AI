from pathlib import Path


def extract_text_from_file(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        from PIL import Image
        import pytesseract
        return pytesseract.image_to_string(Image.open(path))
    raise ValueError(f"Unsupported file type: {suffix}")
