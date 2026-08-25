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
    if suffix in {".xlsx", ".xls"}:
        import pandas as pd
        sheets = pd.read_excel(path, sheet_name=None)
        parts = []
        for name, frame in sheets.items():
            frame = frame.fillna("")
            parts.append(f"Sheet: {name}\n{frame.to_csv(index=False)}")
        return "\n\n".join(parts)
    raise ValueError(f"Unsupported file type: {suffix}")
