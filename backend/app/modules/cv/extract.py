"""Plain-text extraction from PDF and DOCX bytes. Blocking: call via asyncio.to_thread."""

import io
import zipfile

from lxml import etree
from pypdf import PdfReader

MAX_PDF_PAGES = 30
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024  # guards against zip bombs
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def pdf_text(data: bytes) -> str:
    """Text of the first pages of a PDF. Raises ValueError if it is encrypted."""
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError("encrypted PDF")
    return "\n".join(page.extract_text() or "" for page in reader.pages[:MAX_PDF_PAGES])


def docx_text(data: bytes) -> str:
    """Paragraph text (tables included) of a DOCX body, one paragraph per line."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.getinfo("word/document.xml")
        if info.file_size > MAX_DOCX_XML_BYTES:
            raise ValueError("document.xml too large")
        xml = archive.read(info)
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(xml, parser=parser)
    lines = ("".join(t.text or "" for t in p.iter(f"{_W}t")) for p in root.iter(f"{_W}p"))
    return "\n".join(line for line in lines if line.strip())
