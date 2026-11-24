import io
import zipfile
from unittest.mock import AsyncMock, patch

from sqlalchemy import func, select

from app.modules.ai.schemas import CVExtraction
from app.modules.ai.service import AIBadResponse
from app.modules.cv.extract import pdf_text
from app.modules.cv.models import CV
from app.modules.jobs import repository as jobs_repository

EXTRACT = "app.modules.cv.service.ai.extract_profile"
CV_TEXT = "Jane Doe. Senior Python engineer with eight years building FastAPI services."
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx(*paragraphs: str) -> bytes:
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "word/document.xml", f'<w:document xmlns:w="{w}"><w:body>{body}</w:body></w:document>'
        )
    return buf.getvalue()


def _pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
        b"/Resources<</Font<</F1 5 0 R>>>>>>",
        b"<</Length %d>>stream\n%s\nendstream" % (len(stream), stream),
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (n, obj)
    xref = len(out)
    out += b"xref\n0 6\n0000000000 65535 f \n" + b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF" % xref
    return bytes(out)


def _extraction(**kw) -> CVExtraction:
    base = {"headline": "Senior Python Engineer", "summary": "S", "skills": ["Python", "FastAPI"]}
    return CVExtraction(**(base | kw))


async def _upload(client, name: str, data: bytes, mime: str = DOCX_TYPE):
    return await client.post("/api/cv", files={"file": (name, data, mime)})


async def test_upload_replaces_cv_and_overwrites_profile(client, db):
    assert (await client.get("/api/cv")).json() is None
    await jobs_repository.upsert_many(
        [{"source": "x", "url": "u", "title": "T", "description": "d", "score": 80}], db
    )
    with patch(EXTRACT, AsyncMock(return_value=_extraction(education=["BSc"]))) as ai:
        r = await _upload(client, "cv.docx", _docx("Jane Doe", CV_TEXT))
    assert r.status_code == 201
    body = r.json()
    assert body["cv"]["filename"] == "cv.docx"
    assert "Senior Python engineer" in body["cv"]["text"]
    assert "data" not in body["cv"]
    assert body["profile"]["skills"] == ["Python", "FastAPI"]
    assert body["profile"]["locations"] == ["Phnom Penh"]  # search preferences kept
    assert CV_TEXT in ai.await_args.args[0]
    job = (await client.get("/api/jobs")).json()["items"][0]
    assert job["score"] is None  # next analysis must use the new profile

    with patch(EXTRACT, AsyncMock(return_value=_extraction(skills=["Go"], education=[]))):
        r = await _upload(client, "new.docx", _docx(CV_TEXT, "Now a Go developer."))
    assert r.status_code == 201
    profile = (await client.get("/api/profile")).json()
    assert (profile["skills"], profile["education"]) == (["Go"], [])  # overwritten, not appended
    assert (await client.get("/api/cv")).json()["filename"] == "new.docx"
    assert await db.scalar(select(func.count()).select_from(CV)) == 1


async def test_failed_processing_keeps_previous_cv(client):
    with patch(EXTRACT, AsyncMock(return_value=_extraction())):
        await _upload(client, "old.docx", _docx(CV_TEXT))
    with patch(EXTRACT, AsyncMock(side_effect=AIBadResponse("AI returned an invalid response."))):
        r = await _upload(client, "bad.docx", _docx(CV_TEXT, "different"))
    assert r.status_code == 502
    assert (await client.get("/api/cv")).json()["filename"] == "old.docx"
    assert (await client.get("/api/profile")).json()["headline"] == "Senior Python Engineer"


async def test_pdf_upload_extracts_text(client):
    with patch(EXTRACT, AsyncMock(return_value=_extraction())) as ai:
        r = await _upload(client, "CV.PDF", _pdf(CV_TEXT), "application/pdf")
    assert r.status_code == 201
    assert r.json()["cv"]["content_type"] == "application/pdf"
    assert CV_TEXT in ai.await_args.args[0]


async def test_rejects_bad_files_without_calling_ai(client):
    cases = [
        ("cv.txt", CV_TEXT.encode(), "Unsupported file type"),
        ("cv.docx", b"", "empty"),
        ("cv.pdf", _docx(CV_TEXT), "not a valid .pdf"),
        ("cv.docx", b"PK\x03\x04garbage", "Could not read"),
        ("cv.docx", _docx("Too short"), "No readable text"),
        ("cv.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024), "larger than 5 MB"),
    ]
    with patch(EXTRACT, AsyncMock()) as ai:
        for name, data, message in cases:
            r = await _upload(client, name, data)
            assert r.status_code == 400, name
            assert message in r.json()["detail"], name
    ai.assert_not_called()
    assert (await client.get("/api/cv")).json() is None


def test_pdf_text_helper():
    assert CV_TEXT in pdf_text(_pdf(CV_TEXT))
