"""DOCX, XLSX and PDF extraction using only the standard library.

DOCX and XLSX are ZIP containers, so decompression-ratio, entry-count and
uncompressed-size ceilings apply before any parsing (SEC-R-017). XML is parsed
with entity resolution disabled and no remote relationship following.
"""

from __future__ import annotations

import io
import re
import zipfile
from xml.etree import ElementTree

from app.domain.errors import ExtractionError
from app.rag.extractors.base import Extracted, _cap

MAX_ZIP_ENTRIES = 4_000
MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _guard_zip(archive: zipfile.ZipFile) -> None:
    infos = archive.infolist()
    if len(infos) > MAX_ZIP_ENTRIES:
        raise ExtractionError("That file contains too many internal entries to process safely.")
    total = 0
    for info in infos:
        if info.file_size > MAX_UNCOMPRESSED_BYTES:
            raise ExtractionError("That file expands to an unsafe size.")
        if info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > MAX_COMPRESSION_RATIO and info.file_size > 1_048_576:
                raise ExtractionError("That file has an unsafe compression ratio.")
        total += info.file_size
        if total > MAX_UNCOMPRESSED_BYTES:
            raise ExtractionError("That file expands to an unsafe size.")
    for info in infos:
        name = info.filename
        if name.startswith("/") or ".." in name.split("/"):
            raise ExtractionError("That file contains an unsafe internal path.")


_DOCTYPE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
_ENTITY = re.compile(rb"<!ENTITY", re.IGNORECASE)
_EXTERNAL_REF = re.compile(rb"SYSTEM\s+[\"']|PUBLIC\s+[\"']", re.IGNORECASE)


def _safe_xml(data: bytes) -> ElementTree.Element:
    """Parse Office XML with entity and external-reference declarations refused.

    `defusedxml` is not a dependency of this zero-install prototype, so the
    defence is applied before parsing instead of inside it: any document type
    definition, entity declaration or external reference is rejected outright.
    That closes XXE and billion-laughs without trusting parser internals, and
    it is testable (see tests/security/test_xml_hardening.py). Office documents
    produced by Word or Excel never contain these constructs.
    """
    head = data[:8192]
    if _DOCTYPE.search(head) or _ENTITY.search(data) or _EXTERNAL_REF.search(head):
        raise ExtractionError(
            "That document contains an XML declaration that is not permitted.",
            remediation="Re-save the file from Word or Excel and upload it again.",
        )
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        raise ExtractionError("That document's internal XML could not be read.") from exc


class DocxExtractor:
    """Paragraph and table text. Embedded images are not processed (SEC-R-018)."""

    extension = "docx"

    def extract(self, payload: bytes) -> Extracted:
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile as exc:
            raise ExtractionError("That DOCX file is not a readable Word document.") from exc
        with archive:
            _guard_zip(archive)
            if "word/document.xml" not in archive.namelist():
                raise ExtractionError("That DOCX file has no document body.")
            root = _safe_xml(archive.read("word/document.xml"))
        blocks: list[str] = []
        body = root.find(f"{_W}body")
        if body is None:
            raise ExtractionError("That DOCX file has no document body.")
        for element in body.iter():
            if element.tag == f"{_W}p":
                text = "".join(t.text or "" for t in element.iter(f"{_W}t")).strip()
                if text:
                    blocks.append(text)
            elif element.tag == f"{_W}tr":
                cells = [
                    "".join(t.text or "" for t in cell.iter(f"{_W}t")).strip()
                    for cell in element.findall(f"{_W}tc")
                ]
                if any(cells):
                    blocks.append(" | ".join(cells))
        notes = ("Embedded images are not processed; OCR is out of scope.",)
        return Extracted(text=_cap("\n".join(blocks)), page_count=1, notes=notes)


class XlsxExtractor:
    """Cell values as data. Formulas are never evaluated (SEC-R-018)."""

    extension = "xlsx"

    def extract(self, payload: bytes) -> Extracted:
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile as exc:
            raise ExtractionError("That XLSX file is not a readable workbook.") from exc
        with archive:
            _guard_zip(archive)
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = _safe_xml(archive.read("xl/sharedStrings.xml"))
                for si in root.findall(f"{_S}si"):
                    shared.append("".join(t.text or "" for t in si.iter(f"{_S}t")))
            sheets = sorted(
                n for n in archive.namelist() if n.startswith("xl/worksheets/sheet")
            )
            if not sheets:
                raise ExtractionError("That workbook contains no worksheets.")
            lines: list[str] = []
            for sheet in sheets:
                lines.append(f"### {sheet.rsplit('/', 1)[1].replace('.xml', '')}")
                root = _safe_xml(archive.read(sheet))
                for row in root.iter(f"{_S}row"):
                    cells: list[str] = []
                    for cell in row.findall(f"{_S}c"):
                        value = cell.find(f"{_S}v")
                        raw = value.text if value is not None and value.text else ""
                        if cell.get("t") == "s" and raw.isdigit():
                            index = int(raw)
                            raw = shared[index] if index < len(shared) else ""
                        cells.append(raw.strip())
                    if any(cells):
                        lines.append(" | ".join(cells))
        notes = ("Formulas are treated as data and are never evaluated.",)
        return Extracted(text=_cap("\n".join(lines)), page_count=len(sheets), notes=notes)


_PDF_TEXT = re.compile(rb"\((?:\\.|[^\\()])*\)")
_PDF_ESCAPES = {b"\\n": b"\n", b"\\r": b"\n", b"\\t": b"\t", b"\\(": b"(", b"\\)": b")", b"\\\\": b"\\"}


class PdfExtractor:
    """Uncompressed and Flate text streams. No JavaScript, no URI following."""

    extension = "pdf"

    def extract(self, payload: bytes) -> Extracted:
        if not payload.startswith(b"%PDF-"):
            raise ExtractionError("That file is not a readable PDF.")
        page_count = max(1, len(re.findall(rb"/Type\s*/Page[^s]", payload)))
        streams: list[bytes] = []
        for match in re.finditer(rb"stream\r?\n(.*?)endstream", payload, re.DOTALL):
            raw = match.group(1)
            try:
                import zlib

                streams.append(zlib.decompress(raw))
            except Exception:
                streams.append(raw)
        pieces: list[str] = []
        for stream in streams:
            for token in _PDF_TEXT.findall(stream):
                body = token[1:-1]
                for escape, replacement in _PDF_ESCAPES.items():
                    body = body.replace(escape, replacement)
                try:
                    text = body.decode("utf-8")
                except UnicodeDecodeError:
                    text = body.decode("latin-1", errors="ignore")
                if text.strip():
                    pieces.append(text)
        if not pieces:
            # Some producers place text-showing operators outside a stream, and
            # some streams are unrecognised filters. Fall back to the raw bytes
            # before declaring the document image-only.
            for token in _PDF_TEXT.findall(payload):
                body = token[1:-1]
                for escape, replacement in _PDF_ESCAPES.items():
                    body = body.replace(escape, replacement)
                text = body.decode("latin-1", errors="ignore")
                if text.strip():
                    pieces.append(text)
        text = " ".join(pieces)
        text = re.sub(r"[ \t]{2,}", " ", text)
        notes = (
            "Image-only PDFs require OCR, which is outside the scope of this prototype.",
        )
        return Extracted(text=_cap(text.strip()), page_count=page_count, notes=notes)


def default_extractors() -> dict[str, object]:
    from app.rag.extractors.base import (
        CsvExtractor,
        JsonExtractor,
        MarkdownExtractor,
        TextExtractor,
    )

    registry: dict[str, object] = {}
    for extractor in (
        TextExtractor(),
        MarkdownExtractor(),
        JsonExtractor(),
        CsvExtractor(),
        DocxExtractor(),
        XlsxExtractor(),
        PdfExtractor(),
    ):
        registry[extractor.extension] = extractor
    return registry
