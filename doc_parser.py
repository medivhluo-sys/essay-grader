"""Extract plain text from .txt, .docx, and .pdf files."""
from io import BytesIO
from docx import Document


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from uploaded file content.

    Args:
        filename: Original filename (used to detect format via extension)
        content: Raw file bytes

    Returns:
        Extracted plain text

    Raises:
        ValueError: If file format is unsupported or content is empty
    """
    text = _extract(filename, content).strip()
    if not text:
        raise ValueError("文件中没有检测到文字内容，请检查文件后重试。")
    return text


def _extract(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith('.txt'):
        # Try UTF-8 first, fallback to GBK for Chinese files
        for encoding in ('utf-8', 'gbk', 'gb2312', 'latin-1'):
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise ValueError("无法识别文件编码，请保存为 UTF-8 格式后重试。")

    elif lower.endswith('.docx'):
        doc = Document(BytesIO(content))
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        return '\n\n'.join(paragraphs)

    elif lower.endswith('.pdf'):
        import pdfplumber
        pages = []
        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    pages.append(text.strip())
        return '\n\n'.join(pages)

    else:
        raise ValueError(f"不支持的文件格式：{filename}。请上传 .txt、.docx 或 .pdf 文件。")
