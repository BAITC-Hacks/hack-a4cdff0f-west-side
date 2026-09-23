from analyzer.extractors import extract_document
from analyzer.findings import analyze
from analyzer.models import ExtractedDocument, Segment, Source
from analyzer.report import to_markdown
import pymupdf
from pathlib import Path


def doc(name, location, *texts):
    return ExtractedDocument(name, "test", [Segment(Source(name, location, text), text) for text in texts])


def test_analysis_preserves_sources_for_each_finding():
    before = [doc("before.docx", "абзац 3",
                  "Отдел закупок обеспечивает проведение закупочных процедур и контроль договоров.",
                  "Служба контроля осуществляет мониторинг исполнения договоров.")]
    after = [doc("after.xlsx", "лист «Структура», строка 4",
                 "Отдел снабжения обеспечивает проведение закупочных процедур и контроль договоров.",
                 "Служба аудита осуществляет мониторинг исполнения договоров.",
                 "Департамент цифровизации организует разработку цифровых сервисов.")]
    result = analyze(before, after)
    assert result.findings
    assert all(f.sources and all(s.document and s.location and s.excerpt for s in f.sources) for f in result.findings)
    assert any(f.category == "Новая функция" for f in result.findings)


def test_extractor_rejects_unsupported_format():
    try:
        extract_document("file.txt", b"text")
    except ValueError as exc:
        assert "Неподдерживаемый формат" in str(exc)
    else:
        raise AssertionError("unsupported format should fail")


def test_pdf_extraction_keeps_page_reference():
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "The department manages procurement planning and contract monitoring.")
    payload = pdf.tobytes()
    pdf.close()
    extracted = extract_document("policy.pdf", payload)
    assert extracted.segments
    assert all(segment.source.location == "страница 1" for segment in extracted.segments)


def test_empty_sides_rejected():
    try:
        analyze([], [doc("after", "строка 1", "функция")])
    except ValueError as exc:
        assert "Загрузите документы" in str(exc)
    else:
        raise AssertionError("empty before side should fail")


def test_demo_upload_to_analysis_to_cited_report():
    root = Path(__file__).parents[1] / "sample_data"
    before = extract_document("before.docx", (root / "before.docx").read_bytes())
    after = extract_document("after.xlsx", (root / "after.xlsx").read_bytes())
    result = analyze([before], [after])
    assert len(result.functions_before) == 2
    assert len(result.functions_after) == 3
    assert "Департамент цифровизации" in result.units_after
    assert result.findings
    assert all(f.sources and all(s.document and s.location and s.excerpt for s in f.sources) for f in result.findings)
    report = to_markdown(result)
    assert "before.docx — абзац" in report
    assert "after.xlsx — лист" in report
    assert "Источники:" in report


def test_empty_after_rejected(): before = [doc("before", "строка 1", "Функция отдела")]
try:
    analyze(before, [])
except ValueError as exc:
    assert "Загрузите документы" in str(exc)
else:
    raise AssertionError("empty after side should fail")


def test_both_sides_empty_rejected():
    try:
        analyze([], [])
    except ValueError as exc:
        assert "Загрузите документы" in str(exc)
    else:
        raise AssertionError("empty documents should fail")