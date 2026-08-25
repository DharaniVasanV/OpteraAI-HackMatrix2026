import os
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import docx
except ImportError:
    docx = None

def extract_text_from_pdf(filepath: str) -> str:
    if not fitz:
        return ""
    
    text = ""
    try:
        doc = fitz.open(filepath)
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text().strip()
            
            # If text is empty, it might be a scanned PDF, let's try OCR
            if not page_text and pytesseract and Image:
                try:
                    pix = page.get_pixmap()
                    img_path = f"{filepath}_page{page_num}.png"
                    pix.save(img_path)
                    
                    img = Image.open(img_path)
                    page_text = pytesseract.image_to_string(img).strip()
                    
                    img.close()
                    os.remove(img_path)
                except Exception as ocr_exc:
                    print(f"OCR failed for {filepath} page {page_num}: {ocr_exc}")
            
            text += page_text + "\n\n"
        doc.close()
    except Exception as e:
        print(f"PDF extraction failed for {filepath}: {e}")
    return text.strip()

def extract_text_from_docx(filepath: str) -> str:
    if not docx:
        return ""
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"DOCX extraction failed for {filepath}: {e}")
        return ""

def extract_text(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(filepath)
    elif ext in [".txt", ".csv", ".md"]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    
    return ""

def generate_preview(filepath: str, text: str) -> str:
    """Returns a short 200 character preview of the extracted text."""
    if text:
        preview = text[:200].replace("\n", " ")
        return preview + "..." if len(text) > 200 else preview
    return ""
